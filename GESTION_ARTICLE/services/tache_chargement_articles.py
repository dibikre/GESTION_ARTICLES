"""
Tâche exécutée dans un thread secondaire pour l'extraction non-bloquante avec pagination.
Respecte la règle 16 (Threading et tâches longues).
"""

from PySide6.QtCore import QThread, Signal
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class TacheChargementArticles(QThread):
    """Exécute l'extraction réseau d'articles et de pagination en arrière-plan."""

    resultat_charge = Signal(str, object)
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
        """Point d'entrée du thread d'arrière-plan avec extraction paginée."""
        nom_source = self._extracteur.obtenir_nom_source()
        self._journal.info(
            "Starting background thread for source: %s (page %d)",
            nom_source,
            self._numero_page,
        )
        self.progression_signalee.emit(
            nom_source, f"Fetching page {self._numero_page} from {nom_source}..."
        )

        try:
            resultat: ResultatExtractionArticles = self._extracteur.recuperer_articles(
                self._numero_page
            )
            self.resultat_charge.emit(nom_source, resultat)
            self._journal.info(
                "Background fetch completed: %d articles loaded for %s (page %d)",
                len(resultat.articles),
                nom_source,
                self._numero_page,
            )
        except Exception as erreur:
            message_erreur = str(erreur)
            self._journal.error(
                "Background thread error for %s: %s", nom_source, message_erreur
            )
            self.erreur_survenue.emit(nom_source, message_erreur)
