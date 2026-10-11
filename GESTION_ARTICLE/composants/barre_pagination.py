"""
Composant graphique réutilisable représentant la barre de pagination au pied du tableau.
Permet la navigation page par page (Previous / Next / indicateur de page).
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from GESTION_ARTICLE.modeles.modele_pagination import ModelePagination


class BarrePagination(QWidget):
    """Barre inférieure disposée au pied du tableau pour naviguer entre les pages."""

    page_changee = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._pagination_actuelle = ModelePagination()
        self._bouton_precedent = QPushButton("Previous", self)
        self._bouton_suivant = QPushButton("Next", self)
        self._etiquette_page = QLabel("Page 1", self)
        self._initialiser_composants()
        self._connecter_signaux()

    def _initialiser_composants(self) -> None:
        """Dispose les boutons et le libellé dans une rangée horizontale centrée."""
        mise_en_page = QHBoxLayout(self)
        mise_en_page.setContentsMargins(8, 6, 8, 6)
        mise_en_page.setSpacing(12)

        # Style sobre des boutons de pagination (sans aucun emoji ni symbole Unicode)
        style_bouton = """
        QPushButton {
            background-color: #FFFFFF;
            color: #1A202C;
            border: 1px solid #CBD5E0;
            border-radius: 4px;
            padding: 5px 14px;
            font-weight: 500;
            font-size: 12px;
        }
        QPushButton:hover:!disabled {
            background-color: #EDF2F7;
            border-color: #A0AEC0;
        }
        QPushButton:disabled {
            background-color: #F8F9FA;
            color: #A0AEC0;
            border-color: #E2E8F0;
        }
        """
        self._bouton_precedent.setStyleSheet(style_bouton)
        self._bouton_suivant.setStyleSheet(style_bouton)

        self._bouton_precedent.setEnabled(False)
        self._bouton_suivant.setEnabled(True)

        self._etiquette_page.setStyleSheet(
            "color: #4A5568; font-size: 12px; font-weight: 600;"
        )
        self._etiquette_page.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mise_en_page.addStretch(1)
        mise_en_page.addWidget(self._bouton_precedent)
        mise_en_page.addWidget(self._etiquette_page)
        mise_en_page.addWidget(self._bouton_suivant)
        mise_en_page.addStretch(1)

        self.setLayout(mise_en_page)

    def _connecter_signaux(self) -> None:
        """Associe les clics sur les boutons aux changements de page."""
        self._bouton_precedent.clicked.connect(self._sur_clic_precedent)
        self._bouton_suivant.clicked.connect(self._sur_clic_suivant)

    def _sur_clic_precedent(self) -> None:
        """Déclenche le passage à la page précédente si permis."""
        if self._pagination_actuelle.peut_reculer():
            page_cible = self._pagination_actuelle.page_courante - 1
            self.page_changee.emit(page_cible)

    def _sur_clic_suivant(self) -> None:
        """Déclenche le passage à la page suivante si permis."""
        if self._pagination_actuelle.peut_avancer():
            page_cible = self._pagination_actuelle.page_courante + 1
            self.page_changee.emit(page_cible)

    def mettre_a_jour(self, pagination: ModelePagination) -> None:
        """
        Met à jour l'affichage de l'état de pagination et active/désactive les boutons.

        :param pagination: Modèle de pagination à jour.
        """
        self._pagination_actuelle = pagination
        self._etiquette_page.setText(pagination.texte_affichage())
        self._bouton_precedent.setEnabled(pagination.peut_reculer())
        self._bouton_suivant.setEnabled(pagination.peut_avancer())

    def definir_chargement(self, en_cours: bool) -> None:
        """Désactive temporairement les boutons pendant le chargement réseau."""
        if en_cours:
            self._bouton_precedent.setEnabled(False)
            self._bouton_suivant.setEnabled(False)
        else:
            self._bouton_precedent.setEnabled(self._pagination_actuelle.peut_reculer())
            self._bouton_suivant.setEnabled(self._pagination_actuelle.peut_avancer())
