"""
Modèle représentant une source ou catégorie d'articles.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModeleSourceArticle:
    """Représentation métier d'une source d'articles pour un onglet."""

    identifiant: str
    titre_affichage: str
    description: Optional[str] = None
    est_active: bool = True

    def obtenir_cle_unique(self) -> str:
        """Retourne la clé unique de la source."""
        return self.identifiant.lower().strip()
