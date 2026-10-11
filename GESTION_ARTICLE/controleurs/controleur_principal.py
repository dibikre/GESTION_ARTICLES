"""
Contrôleur principal orchestrant les interactions utilisateur et le flux de données.
Gère la navigation par onglet, la pagination au pied de chaque tableau et le cache par page.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal
from GESTION_ARTICLE.configuration.configuration_application import (
    LISTE_ONGLETS_SOURCES,
    MESSAGE_CHARGEMENT_EN_COURS,
    MESSAGE_CHARGEMENT_SUCCES,
    MESSAGE_ERREUR_CHARGEMENT,
    MESSAGE_ONGLET_SELECTIONNE,
    MESSAGE_STATUT_PRET,
)
from GESTION_ARTICLE.modeles.modele_source_article import ModeleSourceArticle
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)
from GESTION_ARTICLE.services.extracteurs.fabrique_extracteurs import (
    FabriqueExtracteurs,
)
from GESTION_ARTICLE.services.service_cache_articles import ServiceCacheArticles
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation
from GESTION_ARTICLE.services.tache_chargement_articles import (
    TacheChargementArticles,
)


class ControleurPrincipal(QObject):
    """Orchestre la navigation entre onglets, la pagination et le cache multi-pages."""

    articles_receptionnes = Signal(str, list)
    resultat_receptionne = Signal(str, object)
    statut_modifie = Signal(str)
    etat_chargement_change = Signal(str, bool)

    def __init__(
        self,
        service_cache: Optional[ServiceCacheArticles] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._journal = ServiceJournalisation.obtenir_journal("ControleurPrincipal")
        self._service_cache = service_cache or ServiceCacheArticles()
        self._sources: List[ModeleSourceArticle] = []
        self._source_active: Optional[ModeleSourceArticle] = None
        self._taches_actives: Dict[str, TacheChargementArticles] = {}
        self._initialiser_sources()

    def _initialiser_sources(self) -> None:
        """Initialise la liste des sources d'articles à partir de la configuration."""
        self._sources = [
            ModeleSourceArticle(identifiant=titre, titre_affichage=titre)
            for titre in LISTE_ONGLETS_SOURCES
        ]
        if self._sources:
            self._source_active = self._sources[0]
        self._journal.info("Initialized %d article sources.", len(self._sources))

    def obtenir_titres_sources(self) -> List[str]:
        """Retourne la liste ordonnée des titres de sources."""
        return [source.titre_affichage for source in self._sources]

    def traiter_selection_onglet(self, index: int, titre: str) -> str:
        """
        Traite le changement d'onglet et consulte le cache de la page 1.
        """
        self._journal.info("Tab selected: index=%d, source='%s'", index, titre)
        source_trouvee = next(
            (s for s in self._sources if s.titre_affichage == titre), None
        )
        if source_trouvee:
            self._source_active = source_trouvee

            # Consultation prioritaire du cache de session pour la page 1
            if self._service_cache.est_en_cache(titre, 1):
                resultat = self._service_cache.obtenir_resultat(titre, 1)
                if resultat:
                    self.resultat_receptionne.emit(titre, resultat)
                    self.articles_receptionnes.emit(titre, resultat.articles)
                    return f"{MESSAGE_ONGLET_SELECTIONNE}{titre} (Cached: {len(resultat.articles)} items)"

            # Premier affichage de la session pour cet onglet
            self._lancer_tache_extraction(titre, numero_page=1)
            return f"{MESSAGE_ONGLET_SELECTIONNE}{titre}"

        return MESSAGE_STATUT_PRET

    def changer_page_source(self, nom_source: str, nouvelle_page: int) -> None:
        """
        Bascule vers une autre page pour la source indiquée avec vérification du cache.
        """
        self._journal.info(
            "Page navigation requested: source='%s', page=%d",
            nom_source,
            nouvelle_page,
        )

        # Si la page demandée est déjà en mémoire, retour instantané
        if self._service_cache.est_en_cache(nom_source, nouvelle_page):
            resultat = self._service_cache.obtenir_resultat(nom_source, nouvelle_page)
            if resultat:
                self.resultat_receptionne.emit(nom_source, resultat)
                self.articles_receptionnes.emit(nom_source, resultat.articles)
                self.statut_modifie.emit(
                    f"{nom_source} — Page {nouvelle_page} (Loaded from cache)"
                )
                return

        # Sinon, extraction asynchrone de la page ciblée
        self._lancer_tache_extraction(nom_source, numero_page=nouvelle_page)

    def actualiser_source(self, nom_source: str) -> None:
        """
        Déclenche une mise à jour manuelle : vide le cache de la source et recharge la page 1.
        """
        self._journal.info("Manual refresh requested for source: %s", nom_source)
        self._service_cache.invalider_source(nom_source)
        self._lancer_tache_extraction(nom_source, numero_page=1)

    def _lancer_tache_extraction(self, nom_source: str, numero_page: int = 1) -> None:
        """Lance l'extraction en arrière-plan d'une page pour une source."""
        cle_tache = f"{nom_source.upper()}_P{numero_page}"
        if cle_tache in self._taches_actives and self._taches_actives[cle_tache].isRunning():
            self._journal.info("Task already active for %s (page %d)", nom_source, numero_page)
            return

        extracteur = FabriqueExtracteurs.obtenir_extracteur(nom_source)
        if not extracteur:
            self._journal.warning("No extractor available for: %s", nom_source)
            return

        self.etat_chargement_change.emit(nom_source, True)
        self.statut_modifie.emit(
            f"{MESSAGE_CHARGEMENT_EN_COURS}{nom_source} (Page {numero_page})..."
        )

        tache = TacheChargementArticles(
            extracteur=extracteur, numero_page=numero_page, parent=self
        )
        tache.resultat_charge.connect(self._sur_resultat_charge)
        tache.erreur_survenue.connect(self._sur_erreur_chargement)
        self._taches_actives[cle_tache] = tache
        tache.start()

    def _sur_resultat_charge(
        self, nom_source: str, resultat: ResultatExtractionArticles
    ) -> None:
        """Enregistre le résultat de page dans le cache et met à jour l'interface."""
        num_page = resultat.pagination.page_courante
        cle_tache = f"{nom_source.upper()}_P{num_page}"
        if cle_tache in self._taches_actives:
            del self._taches_actives[cle_tache]

        self._service_cache.mettre_en_cache(nom_source, resultat, num_page)
        self.etat_chargement_change.emit(nom_source, False)
        self.resultat_receptionne.emit(nom_source, resultat)
        self.articles_receptionnes.emit(nom_source, resultat.articles)

        message = (
            f"{len(resultat.articles)}{MESSAGE_CHARGEMENT_SUCCES}{nom_source} "
            f"({resultat.pagination.texte_affichage()})"
        )
        self.statut_modifie.emit(message)
        self._journal.info(message)

    def _sur_erreur_chargement(self, nom_source: str, message_erreur: str) -> None:
        """Stoppe l'état de chargement et notifie l'erreur."""
        self.etat_chargement_change.emit(nom_source, False)
        message = f"{MESSAGE_ERREUR_CHARGEMENT}{nom_source}: {message_erreur}"
        self.statut_modifie.emit(message)
        self._journal.error(message)

    def obtenir_source_active(self) -> Optional[ModeleSourceArticle]:
        """Retourne le modèle de la source actuellement active."""
        return self._source_active
