"""
Modèle de pagination représentant l'état de navigation d'une liste d'articles.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelePagination:
    """Informations de pagination pour une source d'articles."""

    page_courante: int = 1
    page_maximale: Optional[int] = None
    a_page_suivante: bool = True

    def peut_reculer(self) -> bool:
        """Indique si la navigation vers la page précédente est permise."""
        return self.page_courante > 1

    def peut_avancer(self) -> bool:
        """Indique si la navigation vers la page suivante est permise."""
        if self.page_maximale is not None:
            return self.page_courante < self.page_maximale
        return self.a_page_suivante

    def texte_affichage(self) -> str:
        """Formate le texte d'état de pagination en anglais pour l'interface."""
        if self.page_maximale is not None and self.page_maximale > 0:
            return f"Page {self.page_courante} of {self.page_maximale}"
        return f"Page {self.page_courante}"
