"""
Extracteur d'articles pour la source STATTIMES avec support de pagination.
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


class ExtracteurStatTimes(InterfaceExtracteurArticles):
    """Implémentation de l'extracteur avec pagination pour STAT Times."""

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

    def recuperer_articles(
        self, numero_page: int = 1
    ) -> ResultatExtractionArticles:
        self._journal.info("Fetching STAT Times articles for page %d", numero_page)
        articles: List[ModeleArticle] = []
        a_suivante = True

        try:
            import requests
            import stattimes_scraper  # type: ignore

            with requests.Session() as session:
                resultat = stattimes_scraper.fetch_page(
                    session=session,
                    page=numero_page,
                )

            if isinstance(resultat, tuple):
                donnees_brutes, a_suivante = resultat
            else:
                donnees_brutes = resultat

            for element in donnees_brutes:
                articles.append(
                    ModeleArticle(
                        titre=element.get("title", ""),
                        date=element.get("date", ""),
                        url_image=element.get("image_url"),
                        url_source=element.get("url"),
                    )
                )

            self._journal.info(
                "Extracted %d articles from STAT Times (page %d, has_next=%s)",
                len(articles),
                numero_page,
                str(a_suivante),
            )
        except Exception as erreur:
            self._journal.error(
                "Error extracting articles from STAT Times: %s", str(erreur)
            )

        pagination = ModelePagination(
            page_courante=numero_page,
            page_maximale=None,
            a_page_suivante=a_suivante,
        )
        return ResultatExtractionArticles(articles=articles, pagination=pagination)
