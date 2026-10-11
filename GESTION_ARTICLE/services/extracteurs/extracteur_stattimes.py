"""
Extracteur d'articles pour la source STATTIMES.
Délègue la récupération au module spécialisé stattimes_scraper.
"""

import os
import sys
from typing import List
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ExtracteurStatTimes(InterfaceExtracteurArticles):
    """Implémentation concrète de l'extracteur pour STAT Times."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ExtracteurStatTimes")
        self._nom_source = "STATTIMES"
        self._initialiser_chemin_source()

    def _initialiser_chemin_source(self) -> None:
        """Ajoute le dossier source au sys.path si nécessaire."""
        racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chemin_module = os.path.join(racine, "..", "SOURCE_ONGLET", "STATTIMES")
        if os.path.isdir(chemin_module) and chemin_module not in sys.path:
            sys.path.insert(0, chemin_module)

    def obtenir_nom_source(self) -> str:
        return self._nom_source

    def recuperer_articles(self, numero_page: int = 1) -> List[ModeleArticle]:
        self._journal.info("Fetching articles for STAT Times (page %d)", numero_page)
        articles: List[ModeleArticle] = []

        try:
            import requests
            import stattimes_scraper  # type: ignore

            with requests.Session() as session:
                resultat = stattimes_scraper.fetch_page(
                    session=session,
                    page=numero_page,
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
            self._journal.info("Extracted %d articles from STAT Times", len(articles))

        except Exception as erreur:
            self._journal.error(
                "Error extracting articles from STAT Times: %s", str(erreur)
            )

        return articles
