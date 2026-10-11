"""
Tâche exécutée dans un thread secondaire pour l'extraction non-bloquante des articles.
Respecte la règle 16 (Threading et tâches longues).
"""

from typing import List
from PySide6.QtCore import QThread, Signal
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class TacheChargementArticles(QThread):
    """Exécute l'extraction réseau d'articles en arrière-plan."""

    articles_charges = Signal(str, list)
    erreur_survenue = Signal(str, str)
    progression_signalee = Signal(str, str)

    def __init__(
        self,
        extracteur: InterfaceExtracteurArticles,
        numero_page: int = 1,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._extracteur = extracteur
        self._numero_page = numero_page
        self._journal = ServiceJournalisation.obtenir_journal("TacheChargementArticles")

    def run(self) -> None:
        """Point d'entrée du thread d'arrière-plan."""
        nom_source = self._extracteur.obtenir_nom_source()
        self._journal.info("Starting background thread for source: %s", nom_source)
        self.progression_signalee.emit(nom_source, f"Fetching articles from {nom_source}...")

        try:
            articles: List[ModeleArticle] = self._extracteur.recuperer_articles(
                self._numero_page
            )
            self.articles_charges.emit(nom_source, articles)
            self._journal.info(
                "Background fetch completed: %d articles loaded for %s",
                len(articles),
                nom_source,
            )
        except Exception as erreur:
            message_erreur = str(erreur)
            self._journal.error(
                "Background thread error for %s: %s", nom_source, message_erreur
            )
            self.erreur_survenue.emit(nom_source, message_erreur)
