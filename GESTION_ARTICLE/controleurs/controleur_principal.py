"""
Contrôleur principal orchestrant les interactions utilisateur et le flux de données.
Coordonne le chargement en arrière-plan et la distribution des articles aux vues.
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
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation
from GESTION_ARTICLE.services.tache_chargement_articles import (
    TacheChargementArticles,
)


class ControleurPrincipal(QObject):
    """Orchestre la navigation entre onglets et le chargement des articles."""

    articles_receptionnes = Signal(str, list)
    statut_modifie = Signal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._journal = ServiceJournalisation.obtenir_journal("ControleurPrincipal")
        self._sources: List[ModeleSourceArticle] = []
        self._source_active: Optional[ModeleSourceArticle] = None
        self._cache_articles: Dict[str, List[ModeleArticle]] = {}
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
        Traite le changement d'onglet et déclenche le chargement si nécessaire.

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
            self.charger_articles_source(titre)
            return f"{MESSAGE_ONGLET_SELECTIONNE}{titre}"

        return MESSAGE_STATUT_PRET

    def charger_articles_source(self, nom_source: str, forcer: bool = False) -> None:
        """
        Déclenche l'extraction asynchrone des articles pour une source donnée.

        :param nom_source: Titre de la source à charger.
        :param forcer: Force le rechargement même si le cache est plein.
        """
        cle = nom_source.upper()
        if not forcer and cle in self._cache_articles:
            self._journal.info("Serving articles from memory cache for %s", nom_source)
            self.articles_receptionnes.emit(nom_source, self._cache_articles[cle])
            return

        if cle in self._taches_actives and self._taches_actives[cle].isRunning():
            self._journal.info("Task already running for %s", nom_source)
            return

        extracteur = FabriqueExtracteurs.obtenir_extracteur(nom_source)
        if not extracteur:
            self._journal.warning("No extractor available for source: %s", nom_source)
            return

        self.statut_modifie.emit(f"{MESSAGE_CHARGEMENT_EN_COURS}{nom_source}...")
        tache = TacheChargementArticles(extracteur=extracteur, parent=self)
        tache.articles_charges.connect(self._sur_articles_charges)
        tache.erreur_survenue.connect(self._sur_erreur_chargement)
        self._taches_actives[cle] = tache
        tache.start()

    def _sur_articles_charges(self, nom_source: str, articles: List[ModeleArticle]) -> None:
        """Réceptionne les articles extraits par le thread d'arrière-plan."""
        cle = nom_source.upper()
        self._cache_articles[cle] = articles
        if cle in self._taches_actives:
            del self._taches_actives[cle]

        self.articles_receptionnes.emit(nom_source, articles)
        message = f"{len(articles)}{MESSAGE_CHARGEMENT_SUCCES}{nom_source}"
        self.statut_modifie.emit(message)
        self._journal.info(message)

    def _sur_erreur_chargement(self, nom_source: str, message_erreur: str) -> None:
        """Gère l'erreur survenue lors du chargement réseau."""
        cle = nom_source.upper()
        if cle in self._taches_actives:
            del self._taches_actives[cle]

        message = f"{MESSAGE_ERREUR_CHARGEMENT}{nom_source}: {message_erreur}"
        self.statut_modifie.emit(message)
        self._journal.error(message)

    def obtenir_source_active(self) -> Optional[ModeleSourceArticle]:
        """Retourne le modèle de la source actuellement active."""
        return self._source_active
