"""
Interface abstraite pour l'extraction modulaire des articles avec pagination (SOLID / DIP / OCP).
"""

from abc import ABC, abstractmethod
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)


class InterfaceExtracteurArticles(ABC):
    """Contrat définissant le comportement attendu d'un extracteur d'articles."""

    @abstractmethod
    def obtenir_nom_source(self) -> str:
        """Retourne le nom unique identifiant la source."""
        pass

    @abstractmethod
    def recuperer_articles(
        self, numero_page: int = 1
    ) -> ResultatExtractionArticles:
        """
        Extrait et retourne la liste des articles et la pagination pour la page donnée.

        :param numero_page: Numéro de la page à extraire.
        :return: Instance de ResultatExtractionArticles.
        """
        pass
