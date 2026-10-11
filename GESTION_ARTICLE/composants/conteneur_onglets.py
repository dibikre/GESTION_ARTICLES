"""
Composant graphique réutilisable gérant le conteneur d'onglets de navigation.
Héberge un PanneauSourceArticles pour chaque source afin d'afficher les articles.
Relaye les demandes d'actualisation et de pagination de chaque onglet.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget, QWidget
from GESTION_ARTICLE.composants.panneau_source_articles import (
    PanneauSourceArticles,
)


class ConteneurOnglets(QTabWidget):
    """
    Conteneur d'onglets positionné en haut à gauche.
    Associe chaque onglet de source à son PanneauSourceArticles dédié.
    """

    onglet_change = Signal(int, str)
    demande_actualisation = Signal(str)
    demande_changement_page = Signal(str, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._panneaux_sources: Dict[str, PanneauSourceArticles] = {}
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
        Crée les onglets demandés en leur associant leur panneau de contenu tabulaire.

        :param liste_titres: Liste des titres des onglets à initialiser.
        """
        self.clear()
        self._panneaux_sources.clear()

        for titre in liste_titres:
            panneau = PanneauSourceArticles(nom_source=titre, parent=self)
            panneau.demande_actualisation.connect(self.demande_actualisation.emit)
            panneau.demande_changement_page.connect(
                self.demande_changement_page.emit
            )
            self._panneaux_sources[titre.upper()] = panneau
            self.addTab(panneau, titre)

    def obtenir_panneau_source(
        self, nom_source: str
    ) -> Optional[PanneauSourceArticles]:
        """Retourne le panneau de contenu d'une source spécifique."""
        return self._panneaux_sources.get(nom_source.upper())

    def obtenir_titre_actif(self) -> str:
        """Retourne le titre de l'onglet actuellement sélectionné."""
        return self.tabText(self.currentIndex())
