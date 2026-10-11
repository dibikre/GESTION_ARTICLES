"""
Extracteur d'articles pour la source SEATRADE-MARITIME.
Délègue la récupération au module spécialisé seatrade_scraper.
"""

import os
import sys
from typing import List
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ExtracteurSeatrade(InterfaceExtracteurArticles):
    """Implémentation concrète de l'extracteur pour Seatrade Maritime."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ExtracteurSeatrade")
        self._nom_source = "SEATRADE-MARITIME"
        self._initialiser_chemin_source()

    def _initialiser_chemin_source(self) -> None:
        """Ajoute le dossier source au sys.path si nécessaire."""
        racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chemin_module = os.path.join(racine, "..", "SOURCE_ONGLET", "SEATRADE-MARITIME")
        if os.path.isdir(chemin_module) and chemin_module not in sys.path:
            sys.path.insert(0, chemin_module)

    def obtenir_nom_source(self) -> str:
        return self._nom_source

    def recuperer_articles(self, numero_page: int = 1) -> List[ModeleArticle]:
        self._journal.info("Fetching articles for Seatrade Maritime (page %d)", numero_page)
        articles: List[ModeleArticle] = []

        try:
            import requests
            import seatrade_scraper  # type: ignore

            with requests.Session() as session:
                resultat = seatrade_scraper.fetch_page(
                    session=session,
                    page=numero_page,
                    page_param=seatrade_scraper.PAGE_PARAM,
                )
                donnees_brutes = resultat[0] if isinstance(resultat, tuple) else resultat

            for element in donnees_brutes:
                articles.append(
                    ModeleArticle(
                        titre=element.get("title", ""),
                        date=element.get("date", ""),
                        url_image=element.get("image_url"),
                        url_source=element.get("url"),
                    )
                )
            self._journal.info("Extracted %d articles from Seatrade Maritime", len(articles))

        except Exception as erreur:
            self._journal.error(
                "Error extracting articles from Seatrade Maritime: %s", str(erreur)
            )

        return articles
