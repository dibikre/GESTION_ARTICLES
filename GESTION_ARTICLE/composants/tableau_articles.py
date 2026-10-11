"""
Composant graphique réutilisable pour l'affichage tabulaire des articles.
Affiche les 3 colonnes requises : Image (1ère), Title (2ème), Date (3ème).
Aucune action de clic n'est attachée aux éléments conformément aux spécifications.
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)
from GESTION_ARTICLE.configuration.configuration_application import (
    ENTETES_COLONNES_ARTICLES,
    HAUTEUR_LIGNE_ARTICLE,
    INDEX_COLONNE_DATE,
    INDEX_COLONNE_IMAGE,
    INDEX_COLONNE_TITRE,
    LARGEUR_COLONNE_DATE,
    LARGEUR_COLONNE_IMAGE,
)
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.services.service_chargement_image import ServiceChargementImage


class TableauArticles(QTableWidget):
    """Tableau passif affichant les articles extraits (Image, Titre, Date)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._initialiser_tableau()

    def _initialiser_tableau(self) -> None:
        """Configure les colonnes, la disposition et désactive les interactions de clic."""
        self.setColumnCount(len(ENTETES_COLONNES_ARTICLES))
        self.setHorizontalHeaderLabels(ENTETES_COLONNES_ARTICLES)

        # Désactivation stricte de toute action de clic ou d'édition
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Configuration des en-têtes et du redimensionnement responsive
        en_tete_horizontal = self.horizontalHeader()
        en_tete_horizontal.setSectionResizeMode(
            INDEX_COLONNE_IMAGE, QHeaderView.ResizeMode.Fixed
        )
        self.setColumnWidth(INDEX_COLONNE_IMAGE, LARGEUR_COLONNE_IMAGE)

        en_tete_horizontal.setSectionResizeMode(
            INDEX_COLONNE_TITRE, QHeaderView.ResizeMode.Stretch
        )

        en_tete_horizontal.setSectionResizeMode(
            INDEX_COLONNE_DATE, QHeaderView.ResizeMode.Fixed
        )
        self.setColumnWidth(INDEX_COLONNE_DATE, LARGEUR_COLONNE_DATE)

        en_tete_horizontal.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

    def afficher_articles(self, articles: List[ModeleArticle]) -> None:
        """
        Remplit le tableau avec la liste des articles.

        :param articles: Liste d'articles à présenter.
        """
        self.setRowCount(len(articles))

        for index_ligne, article in enumerate(articles):
            self.setRowHeight(index_ligne, HAUTEUR_LIGNE_ARTICLE)

            # 1ère colonne : Image
            widget_image = self._creer_cellule_image(article.url_image)
            self.setCellWidget(index_ligne, INDEX_COLONNE_IMAGE, widget_image)

            # 2ème colonne : Titre
            element_titre = QTableWidgetItem(article.titre)
            element_titre.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            element_titre.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.setItem(index_ligne, INDEX_COLONNE_TITRE, element_titre)

            # 3ème colonne : Date
            element_date = QTableWidgetItem(article.date_formatee())
            element_date.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            element_date.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.setItem(index_ligne, INDEX_COLONNE_DATE, element_date)

    def _creer_cellule_image(self, url_image: Optional[str]) -> QLabel:
        """Crée une étiquette QLabel contenant la vignette redimensionnée."""
        etiquette = QLabel()
        etiquette.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = ServiceChargementImage.charger_pixmap_depuis_url(
            url_image=url_image,
            largeur_cible=120,
            hauteur_cible=68,
        )
        etiquette.setPixmap(pixmap)
        return etiquette

    def vider(self) -> None:
        """Efface l'ensemble des lignes du tableau."""
        self.setRowCount(0)
