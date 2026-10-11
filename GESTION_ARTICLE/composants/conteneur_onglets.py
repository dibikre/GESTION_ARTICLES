"""
Composant graphique réutilisable gérant le conteneur d'onglets de navigation.
"""

from typing import List, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout


class ConteneurOnglets(QTabWidget):
    """
    Conteneur d'onglets personnalisable positionné en haut à gauche.
    Fournit des pages sans contenu comme requis par la spécification.
    """

    onglet_change = Signal(int, str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._initialiser_proprietes()
        self._connecter_signaux()

    def _initialiser_proprietes(self) -> None:
        """Configure les paramètres de base des onglets."""
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setDocumentMode(True)
        self.setMovable(False)
        self.setTabsClosable(False)

    def _connecter_signaux(self) -> None:
        """Connecte les signaux natifs de PySide6 aux méthodes du composant."""
        self.currentChanged.connect(self._sur_changement_onglet)

    def _sur_changement_onglet(self, index: int) -> None:
        """Émet un signal enrichi lors de la sélection d'un nouvel onglet."""
        titre = self.tabText(index)
        self.onglet_change.emit(index, titre)

    def initialiser_onglets_sources(self, liste_titres: List[str]) -> None:
        """
        Crée les onglets demandés avec des conteneurs vides (sans contenu).

        :param liste_titres: Liste des titres des onglets à initialiser.
        """
        self.clear()
        for titre in liste_titres:
            self.ajouter_onglet_vide(titre)

    def ajouter_onglet_vide(self, titre: str) -> QWidget:
        """
        Ajoute un nouvel onglet avec un widget vierge.

        :param titre: Nom affiché dans l'onglet.
        :return: Le widget vide associé à l'onglet.
        """
        panneau_vide = QWidget()
        mise_en_page = QVBoxLayout(panneau_vide)
        mise_en_page.setContentsMargins(16, 16, 16, 16)
        panneau_vide.setLayout(mise_en_page)

        self.addTab(panneau_vide, titre)
        return panneau_vide

    def obtenir_titre_actif(self) -> str:
        """Retourne le titre de l'onglet actuellement sélectionné."""
        return self.tabText(self.currentIndex())
