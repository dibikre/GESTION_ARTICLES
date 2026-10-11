"""
Composant représentant le panneau de contenu d'un onglet de source d'articles.
Intègre le tableau d'articles et la gestion des états de chargement / vacuité.
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from GESTION_ARTICLE.composants.tableau_articles import TableauArticles
from GESTION_ARTICLE.configuration.configuration_application import (
    MESSAGE_AUCUN_ARTICLE,
    MESSAGE_CHARGEMENT_EN_COURS,
)
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle


class PanneauSourceArticles(QWidget):
    """Vue intégrée d'un onglet contenant le tableau des articles d'une source."""

    def __init__(self, nom_source: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._nom_source = nom_source
        self._tableau = TableauArticles(self)
        self._etiquette_statut = QLabel(self)
        self._initialiser_interface()

    def _initialiser_interface(self) -> None:
        """Dispose les éléments dans un layout vertical responsive."""
        mise_en_page = QVBoxLayout(self)
        mise_en_page.setContentsMargins(8, 8, 8, 8)
        mise_en_page.setSpacing(6)

        # En-tête informatif discret
        self._etiquette_statut.setStyleSheet("color: #718096; font-size: 12px; padding: 2px 4px;")
        self._etiquette_statut.setText(f"{MESSAGE_CHARGEMENT_EN_COURS}{self._nom_source}...")
        mise_en_page.addWidget(self._etiquette_statut)

        # Tableau des articles occupant l'espace principal
        mise_en_page.addWidget(self._tableau, stretch=1)
        self.setLayout(mise_en_page)

    def definir_articles(self, articles: List[ModeleArticle]) -> None:
        """
        Met à jour les données du tableau avec la liste des articles.

        :param articles: Articles à afficher.
        """
        if not articles:
            self._tableau.vider()
            self._etiquette_statut.setText(f"{self._nom_source}: {MESSAGE_AUCUN_ARTICLE}")
            return

        self._tableau.afficher_articles(articles)
        self._etiquette_statut.setText(
            f"{self._nom_source} — {len(articles)} articles"
        )

    def afficher_erreur(self, message_erreur: str) -> None:
        """Affiche un message d'erreur d'extraction."""
        self._etiquette_statut.setText(f"Error ({self._nom_source}): {message_erreur}")

    def afficher_chargement(self) -> None:
        """Affiche l'état de chargement en cours."""
        self._etiquette_statut.setText(f"{MESSAGE_CHARGEMENT_EN_COURS}{self._nom_source}...")

    def obtenir_nom_source(self) -> str:
        """Retourne le nom de la source associée à ce panneau."""
        return self._nom_source
