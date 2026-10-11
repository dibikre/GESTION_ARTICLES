"""
Service de mise en cache mémoire des articles et de la pagination par source et par page.
Garantit que la navigation entre pages et onglets est instantanée sans nouvel appel réseau.
"""

from typing import Dict, List, Optional
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ServiceCacheArticles:
    """Gestionnaire de cache en mémoire indexé par (source, numéro de page)."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ServiceCacheArticles")
        self._cache_pages: Dict[str, Dict[int, ResultatExtractionArticles]] = {}

    def _obtenir_cle_source(self, nom_source: str) -> str:
        """Harmonise la clé de source en majuscules."""
        return nom_source.upper().strip()

    def est_en_cache(self, nom_source: str, numero_page: int = 1) -> bool:
        """
        Vérifie si la page demandée est déjà en mémoire pour la source.

        :param nom_source: Nom de la source (ex. STATTIMES).
        :param numero_page: Numéro de la page.
        :return: True si en cache, sinon False.
        """
        cle = self._obtenir_cle_source(nom_source)
        return cle in self._cache_pages and numero_page in self._cache_pages[cle]

    def obtenir_resultat(
        self, nom_source: str, numero_page: int = 1
    ) -> Optional[ResultatExtractionArticles]:
        """
        Retourne le résultat d'extraction et de pagination en cache.

        :param nom_source: Nom de la source.
        :param numero_page: Numéro de la page.
        :return: Instance de ResultatExtractionArticles ou None.
        """
        cle = self._obtenir_cle_source(nom_source)
        pages_source = self._cache_pages.get(cle)
        if pages_source and numero_page in pages_source:
            self._journal.info(
                "Cache HIT: Page %d found for %s", numero_page, nom_source
            )
            return pages_source[numero_page]

        self._journal.info(
            "Cache MISS: Page %d not in cache for %s", numero_page, nom_source
        )
        return None

    def obtenir_articles(
        self, nom_source: str, numero_page: int = 1
    ) -> Optional[List[ModeleArticle]]:
        """Retourne uniquement la liste d'articles d'une page mise en cache."""
        resultat = self.obtenir_resultat(nom_source, numero_page)
        return resultat.articles if resultat else None

    def mettre_en_cache(
        self,
        nom_source: str,
        resultat: ResultatExtractionArticles,
        numero_page: int = 1,
    ) -> None:
        """
        Enregistre les données et la pagination d'une page spécifique en cache.
        """
        cle = self._obtenir_cle_source(nom_source)
        if cle not in self._cache_pages:
            self._cache_pages[cle] = {}

        self._cache_pages[cle][numero_page] = resultat
        self._journal.info(
            "Cached %d articles for %s (page %d)",
            len(resultat.articles),
            nom_source,
            numero_page,
        )

    def invalider_source(self, nom_source: str) -> None:
        """
        Invalide toutes les pages en cache pour une source (lors d'une actualisation manuelle).
        """
        cle = self._obtenir_cle_source(nom_source)
        if cle in self._cache_pages:
            del self._cache_pages[cle]
            self._journal.info("All cached pages cleared for source: %s", nom_source)

    def vider_tout(self) -> None:
        """Vide l'intégralité du cache."""
        self._cache_pages.clear()
        self._journal.info("Full articles cache cleared.")
