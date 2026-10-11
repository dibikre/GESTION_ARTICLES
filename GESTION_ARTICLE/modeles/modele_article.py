"""
Modèle métier représentant un article extrait d'une source d'actualité.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModeleArticle:
    """Structure de données immuable pour un article individuel."""

    titre: str
    date: str
    url_image: Optional[str] = None
    url_source: Optional[str] = None

    def a_une_image(self) -> bool:
        """Indique si une URL d'image est disponible."""
        return bool(self.url_image and self.url_image.strip())

    def date_formatee(self) -> str:
        """Retourne la date ou une valeur de repli si absente."""
        return self.date if self.date else "N/A"
