"""
Modèle encapsulant la liste des articles extraits et leurs métadonnées de pagination.
"""

from dataclasses import dataclass
from typing import List
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.modele_pagination import ModelePagination


@dataclass
class ResultatExtractionArticles:
    """Résultat complet retourné par les extracteurs de sources."""

    articles: List[ModeleArticle]
    pagination: ModelePagination
