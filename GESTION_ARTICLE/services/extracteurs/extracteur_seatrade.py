"""
Extracteur d'articles pour la source SEATRADE-MARITIME avec support de pagination.
"""

import math
import os
import sys
from typing import List, Optional
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.modele_pagination import ModelePagination
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ExtracteurSeatrade(InterfaceExtracteurArticles):
    """Implémentation de l'extracteur avec pagination pour Seatrade Maritime."""

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

    def recuperer_articles(
        self, numero_page: int = 1
    ) -> ResultatExtractionArticles:
        self._journal.info("Fetching Seatrade Maritime articles for page %d", numero_page)
        articles: List[ModeleArticle] = []
        page_max: Optional[int] = None

        try:
            import requests
            import seatrade_scraper  # type: ignore

            with requests.Session() as session:
                resultat = seatrade_scraper.fetch_page(
                    session=session,
                    page=numero_page,
                    page_param=seatrade_scraper.PAGE_PARAM,
                )

            if isinstance(resultat, tuple) and len(resultat) >= 4:
                donnees_brutes, page_recue, total_articles, taille_page = resultat
                if taille_page > 0 and total_articles > 0:
                    page_max = max(1, math.ceil(total_articles / taille_page))
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
                "Extracted %d articles from Seatrade Maritime (page %d of %s)",
                len(articles),
                numero_page,
                str(page_max),
            )
        except Exception as erreur:
            self._journal.error(
                "Error extracting articles from Seatrade Maritime: %s", str(erreur)
            )

        pagination = ModelePagination(
            page_courante=numero_page,
            page_maximale=page_max,
            a_page_suivante=page_max is None or numero_page < page_max,
        )
        return ResultatExtractionArticles(articles=articles, pagination=pagination)
