"""
Extracteur d'articles pour la source AIRCARGOWEEK avec support de pagination.
"""

import os
import sys
from typing import List
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.modele_pagination import ModelePagination
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ExtracteurAirCargoWeek(InterfaceExtracteurArticles):
    """Implémentation de l'extracteur avec pagination pour Air Cargo Week."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ExtracteurAirCargoWeek")
        self._nom_source = "AIRCARGOWEEK"
        self._initialiser_chemin_source()

    def _initialiser_chemin_source(self) -> None:
        """Ajoute le dossier source au sys.path si nécessaire."""
        racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chemin_module = os.path.join(racine, "..", "SOURCE_ONGLET", "AIRCARGOWEEK")
        if os.path.isdir(chemin_module) and chemin_module not in sys.path:
            sys.path.insert(0, chemin_module)

    def obtenir_nom_source(self) -> str:
        return self._nom_source

    def recuperer_articles(
        self, numero_page: int = 1
    ) -> ResultatExtractionArticles:
        self._journal.info("Fetching Air Cargo Week articles for page %d", numero_page)
        articles: List[ModeleArticle] = []
        a_suivante = True

        try:
            import requests
            import aircargoweek_scraper  # type: ignore

            with requests.Session() as session:
                donnees_brutes = aircargoweek_scraper.fetch_page(
                    session=session,
                    page=numero_page,
                    page_param=aircargoweek_scraper.PAGE_PARAM,
                )

            for element in donnees_brutes:
                articles.append(
                    ModeleArticle(
                        titre=element.get("title", ""),
                        date=element.get("date", ""),
                        url_image=element.get("image_url"),
                        url_source=element.get("url"),
                    )
                )

            a_suivante = len(donnees_brutes) > 0
            self._journal.info(
                "Extracted %d articles from Air Cargo Week (page %d)",
                len(articles),
                numero_page,
            )
        except Exception as erreur:
            self._journal.error(
                "Error extracting articles from Air Cargo Week: %s", str(erreur)
            )

        pagination = ModelePagination(
            page_courante=numero_page,
            page_maximale=None,
            a_page_suivante=a_suivante,
        )
        return ResultatExtractionArticles(articles=articles, pagination=pagination)
