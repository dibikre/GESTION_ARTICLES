"""
Extracteur d'articles pour la source FREIGHTWAVES avec support de pagination.
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


class ExtracteurFreightWaves(InterfaceExtracteurArticles):
    """Implémentation de l'extracteur avec pagination pour FreightWaves."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ExtracteurFreightWaves")
        self._nom_source = "FREIGHTWAVES"
        self._initialiser_chemin_source()

    def _initialiser_chemin_source(self) -> None:
        """Ajoute le dossier source au sys.path si nécessaire."""
        racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chemin_module = os.path.join(racine, "..", "SOURCE_ONGLET", "FREIGHTWAVES")
        if os.path.isdir(chemin_module) and chemin_module not in sys.path:
            sys.path.insert(0, chemin_module)

    def obtenir_nom_source(self) -> str:
        return self._nom_source

    def recuperer_articles(
        self, numero_page: int = 1
    ) -> ResultatExtractionArticles:
        self._journal.info("Fetching FreightWaves articles for page %d", numero_page)
        articles: List[ModeleArticle] = []
        page_max = None

        try:
            import requests
            import freightwaves_scraper  # type: ignore

            with requests.Session() as session:
                resultat = freightwaves_scraper.fetch_page(
                    session=session,
                    page=numero_page,
                )

            if isinstance(resultat, tuple) and len(resultat) >= 3:
                donnees_brutes, page_actuelle, page_max = resultat
            else:
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

            self._journal.info(
                "Extracted %d articles from FreightWaves (page %d of %s)",
                len(articles),
                numero_page,
                str(page_max),
            )
        except Exception as erreur:
            self._journal.error(
                "Error extracting articles from FreightWaves: %s", str(erreur)
            )

        pagination = ModelePagination(
            page_courante=numero_page,
            page_maximale=page_max,
            a_page_suivante=page_max is None or numero_page < page_max,
        )
        return ResultatExtractionArticles(articles=articles, pagination=pagination)
