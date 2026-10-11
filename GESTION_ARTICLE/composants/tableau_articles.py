"""
Composant graphique réutilisable pour l'affichage tabulaire ultra-fluide des articles.
Optimisé pour une réactivité instantanée sans aucun freeze d'affichage.
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
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
    """Tableau passif optimisé pour le rendu fluide et instantané."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._articles_affiches: List[ModeleArticle] = []
        self._etiquettes_images: List[QLabel] = []
        self._initialiser_tableau()

    def _initialiser_tableau(self) -> None:
        """Configure les colonnes et optimise le moteur de rendu Qt."""
        self.setColumnCount(len(ENTETES_COLONNES_ARTICLES))
        self.setHorizontalHeaderLabels(ENTETES_COLONNES_ARTICLES)

        # Désactivation complète des interactions de clic et focus pour fluidité maximale
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

    def a_articles_affiches(self) -> bool:
        """Indique si le tableau contient déjà des articles affichés."""
        return len(self._articles_affiches) > 0

    def afficher_articles(self, articles: List[ModeleArticle]) -> None:
        """
        Remplit le tableau en coupant temporairement les rafraîchissements pour fluidité.
        """
        # Si les mêmes articles sont déjà présents, ne pas recalculer l'arbre graphique
        if self._articles_affiches == articles:
            return

        self._articles_affiches = list(articles)
        self._etiquettes_images.clear()

        # Optimisation Qt critique : gèle les rafraîchissements pendant le peuplement
        self.setUpdatesEnabled(False)
        try:
            self.setRowCount(len(articles))

            for index_ligne, article in enumerate(articles):
                self.setRowHeight(index_ligne, HAUTEUR_LIGNE_ARTICLE)

                # 1ère colonne : Image avec chargement asynchrone non bloquant
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
        """Crée le QLabel et l'alimente de manière asynchrone sans latence."""
        etiquette = QLabel()
        etiquette.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def mettre_a_jour_pixmap(url_recue: str, pixmap: QPixmap) -> None:
            if url_recue == url_image:
                etiquette.setPixmap(pixmap)

        pixmap_initial = ServiceChargementImage.obtenir_pixmap(
            url_image=url_image,
            largeur_cible=120,
            hauteur_cible=68,
            sur_image_prete=mettre_a_jour_pixmap if url_image else None,
        )
        etiquette.setPixmap(pixmap_initial)
        self._etiquettes_images.append(etiquette)
        return etiquette

    def vider(self) -> None:
        """Efface l'ensemble des lignes du tableau de manière sécurisée."""
        self._articles_affiches.clear()
        self._etiquettes_images.clear()
        self.setRowCount(0)
