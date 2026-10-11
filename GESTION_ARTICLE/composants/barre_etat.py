"""
Composant graphique réutilisable pour la barre de statut de la fenêtre principale.
"""

from typing import Optional
from PySide6.QtWidgets import QStatusBar, QLabel, QWidget


class BarreEtat(QStatusBar):
    """Barre d'état inférieure affichant les messages système et d'interaction."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._etiquette_message = QLabel()
        self._initialiser_composants()

    def _initialiser_composants(self) -> None:
        """Configure les composants internes de la barre d'état."""
        self.addWidget(self._etiquette_message)

    def definir_message(self, texte: str) -> None:
        """
        Définit le message affiché dans la barre de statut.

        :param texte: Texte d'état (en anglais pour l'utilisateur final).
        """
        self._etiquette_message.setText(texte)

    def effacer_message(self) -> None:
        """Efface le message d'état en cours."""
        self._etiquette_message.clear()
