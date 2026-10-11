"""
Contrôleur principal orchestrant les interactions utilisateur et le flux de données.
Intègre le ServiceCacheArticles pour éviter tout appel réseau intempestif lors des clics.
Gère les mises à jour volontaires avec rotation de l'icône d'actualisation.
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
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.modele_source_article import ModeleSourceArticle
from GESTION_ARTICLE.services.extracteurs.fabrique_extracteurs import (
    FabriqueExtracteurs,
)
from GESTION_ARTICLE.services.service_cache_articles import ServiceCacheArticles
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation
from GESTION_ARTICLE.services.tache_chargement_articles import (
    TacheChargementArticles,
)


class ControleurPrincipal(QObject):
    """Orchestre la navigation entre onglets, le cache et les mises à jour manuelles."""

    articles_receptionnes = Signal(str, list)
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
        Traite le changement d'onglet sans déclencher d'appel réseau si déjà en cache.

        :param index: Index de l'onglet sélectionné.
        :param titre: Nom de la source sélectionnée.
        :return: Message de statut pour la barre d'état.
        """
        self._journal.info("Tab selected: index=%d, source='%s'", index, titre)
        source_trouvee = next(
            (s for s in self._sources if s.titre_affichage == titre), None
        )
        if source_trouvee:
            self._source_active = source_trouvee

            # Consultation prioritaire du cache de session
            if self._service_cache.est_en_cache(titre):
                articles = self._service_cache.obtenir_articles(titre) or []
                self.articles_receptionnes.emit(titre, articles)
                return f"{MESSAGE_ONGLET_SELECTIONNE}{titre} (Cached: {len(articles)} items)"

            # Si non présent (premier affichage de l'onglet lors de la session)
            self._lancer_tache_extraction(titre)
            return f"{MESSAGE_ONGLET_SELECTIONNE}{titre}"

        return MESSAGE_STATUT_PRET

    def actualiser_source(self, nom_source: str) -> None:
        """
        Déclenche une mise à jour volontaire par appel de récupération via l'icône.
        Invalide le cache pour cette source et active l'icône rotative.

        :param nom_source: Nom de la source à rafraîchir.
        """
        self._journal.info("Manual refresh requested for source: %s", nom_source)
        self._service_cache.invalider_source(nom_source)
        self._lancer_tache_extraction(nom_source)

    def _lancer_tache_extraction(self, nom_source: str) -> None:
        """Lance l'extraction en arrière-plan et signale le début du chargement."""
        cle = nom_source.upper()
        if cle in self._taches_actives and self._taches_actives[cle].isRunning():
            self._journal.info("Extraction already running for %s", nom_source)
            return

        extracteur = FabriqueExtracteurs.obtenir_extracteur(nom_source)
        if not extracteur:
            self._journal.warning("No extractor available for: %s", nom_source)
            return

        # Notification de début de chargement pour activer l'icône rotative
        self.etat_chargement_change.emit(nom_source, True)
        self.statut_modifie.emit(f"{MESSAGE_CHARGEMENT_EN_COURS}{nom_source}...")

        tache = TacheChargementArticles(extracteur=extracteur, parent=self)
        tache.articles_charges.connect(self._sur_articles_charges)
        tache.erreur_survenue.connect(self._sur_erreur_chargement)
        self._taches_actives[cle] = tache
        tache.start()

    def _sur_articles_charges(self, nom_source: str, articles: List[ModeleArticle]) -> None:
        """Enregistre dans le cache et stoppe l'animation rotative."""
        cle = nom_source.upper()
        self._service_cache.mettre_en_cache(nom_source, articles)
        if cle in self._taches_actives:
            del self._taches_actives[cle]

        self.etat_chargement_change.emit(nom_source, False)
        self.articles_receptionnes.emit(nom_source, articles)

        message = f"{len(articles)}{MESSAGE_CHARGEMENT_SUCCES}{nom_source}"
        self.statut_modifie.emit(message)
        self._journal.info(message)

    def _sur_erreur_chargement(self, nom_source: str, message_erreur: str) -> None:
        """Arrête l'animation rotative et affiche l'erreur."""
        cle = nom_source.upper()
        if cle in self._taches_actives:
            del self._taches_actives[cle]

        self.etat_chargement_change.emit(nom_source, False)
        message = f"{MESSAGE_ERREUR_CHARGEMENT}{nom_source}: {message_erreur}"
        self.statut_modifie.emit(message)
        self._journal.error(message)

    def obtenir_source_active(self) -> Optional[ModeleSourceArticle]:
        """Retourne le modèle de la source actuellement active."""
        return self._source_active
