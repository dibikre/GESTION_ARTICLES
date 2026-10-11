"""
Composant graphique réutilisable pour l'affichage tabulaire ultra-fluide des articles.
Assure un affichage fiable des vignettes, y compris lors du défilement (scroll).
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
    """Tableau passif optimisé pour le rendu fluide et le chargement continu des vignettes."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._articles_affiches: List[ModeleArticle] = []
        self._etiquettes_images: List[QLabel] = []
        self._initialiser_tableau()

    def _initialiser_tableau(self) -> None:
        """Configure les colonnes et optimise le comportement lors du défilement."""
        self.setColumnCount(len(ENTETES_COLONNES_ARTICLES))
        self.setHorizontalHeaderLabels(ENTETES_COLONNES_ARTICLES)

        # Désactivation stricte des interactions de clic et focus pour fluidité maximale
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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

        # Défilement fluide par pixel pour éviter les à-coups visuels
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    def a_articles_affiches(self) -> bool:
        """Indique si le tableau contient déjà des articles affichés."""
        return len(self._articles_affiches) > 0

    def afficher_articles(self, articles: List[ModeleArticle]) -> None:
        """
        Remplit le tableau avec les articles et prépare le chargement fiable des vignettes.
        """
        if self._articles_affiches == articles:
            return

        self._articles_affiches = list(articles)
        self._etiquettes_images.clear()

        self.setUpdatesEnabled(False)
        try:
            self.setRowCount(len(articles))

            for index_ligne, article in enumerate(articles):
                self.setRowHeight(index_ligne, HAUTEUR_LIGNE_ARTICLE)

                # 1ère colonne : Image avec chargement garanti même après défilement
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
        finally:
            self.setUpdatesEnabled(True)

    def _creer_cellule_image(self, url_image: Optional[str]) -> QLabel:
        """Crée l'étiquette et y attache le récepteur de vignette garanti."""
        etiquette = QLabel()
        etiquette.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiquette.setMinimumSize(120, 68)

        # Assigne immédiatement le pixmap (cache ou défaut) et enregistre la mise à jour asynchrone
        pixmap_initial = ServiceChargementImage.charger_vignette(
            url_image=url_image,
            sur_reception=etiquette.setPixmap,
            largeur=120,
            hauteur=68,
        )
        etiquette.setPixmap(pixmap_initial)
        self._etiquettes_images.append(etiquette)
        return etiquette

    def vider(self) -> None:
        """Efface l'ensemble des lignes du tableau de manière sécurisée."""
        self._articles_affiches.clear()
        self._etiquettes_images.clear()
        self.setRowCount(0)
