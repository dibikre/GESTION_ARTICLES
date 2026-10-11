"""
Interface abstraite pour l'extraction modulaire des articles (Principe SOLID / DIP / OCP).
"""

from abc import ABC, abstractmethod
from typing import List
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle


class InterfaceExtracteurArticles(ABC):
    """Contrat définissant le comportement attendu d'un extracteur d'articles."""

    @abstractmethod
    def obtenir_nom_source(self) -> str:
        """Retourne le nom unique identifiant la source."""
        pass

    @abstractmethod
    def recuperer_articles(self, numero_page: int = 1) -> List[ModeleArticle]:
        """
        Extrait et retourne la liste des articles pour la page donnée.

        :param numero_page: Numéro de la page à extraire.
        :return: Liste d'instances de ModeleArticle.
        """
        pass
