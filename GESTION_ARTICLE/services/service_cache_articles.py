"""
Service de mise en cache mémoire des articles pour la durée de la session.
Évite les requêtes réseau répétitives lors de la navigation entre onglets (SOLID / SRP).
"""

from typing import Dict, List, Optional
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ServiceCacheArticles:
    """Gestionnaire central de cache en mémoire pour les articles de chaque source."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ServiceCacheArticles")
        self._donnees_cache: Dict[str, List[ModeleArticle]] = {}

    def est_en_cache(self, nom_source: str) -> bool:
        """
        Vérifie si les articles de la source sont déjà en cache.

        :param nom_source: Nom de la source (ex. STATTIMES).
        :return: True si les articles sont mémorisés, sinon False.
        """
        cle = nom_source.upper().strip()
        return cle in self._donnees_cache

    def obtenir_articles(self, nom_source: str) -> Optional[List[ModeleArticle]]:
        """
        Récupère les articles en cache pour une source donnée.

        :param nom_source: Nom de la source.
        :return: Liste des articles ou None si non présent.
        """
        cle = nom_source.upper().strip()
        articles = self._donnees_cache.get(cle)
        if articles is not None:
            self._journal.info(
                "Cache HIT: %d articles retrieved for %s", len(articles), nom_source
            )
        else:
            self._journal.info("Cache MISS: No cached articles for %s", nom_source)
        return articles

    def mettre_en_cache(
        self, nom_source: str, articles: List[ModeleArticle]
    ) -> None:
        """
        Enregistre les articles d'une source dans le cache mémoire.

        :param nom_source: Nom de la source.
        :param articles: Liste des articles à conserver.
        """
        cle = nom_source.upper().strip()
        self._donnees_cache[cle] = articles
        self._journal.info(
            "Cached %d articles successfully for %s", len(articles), nom_source
        )

    def invalider_source(self, nom_source: str) -> None:
        """
        Supprime les articles d'une source spécifique du cache.

        :param nom_source: Nom de la source à invalider.
        """
        cle = nom_source.upper().strip()
        if cle in self._donnees_cache:
            del self._donnees_cache[cle]
            self._journal.info("Cache invalidated for source: %s", nom_source)

    def vider_tout(self) -> None:
        """Vide l'intégralité du cache."""
        self._donnees_cache.clear()
        self._journal.info("Full articles cache cleared.")
