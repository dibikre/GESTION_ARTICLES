"""
Composant représentant le panneau d'un onglet de source d'articles.
Intègre le tableau d'articles, le bouton rotatif en haut à droite,
et la barre de pagination disposée au pied du tableau.
"""

from typing import List, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from GESTION_ARTICLE.composants.barre_pagination import BarrePagination
from GESTION_ARTICLE.composants.bouton_actualisation import BoutonActualisation
from GESTION_ARTICLE.composants.tableau_articles import TableauArticles
from GESTION_ARTICLE.configuration.configuration_application import (
    MESSAGE_AUCUN_ARTICLE,
    MESSAGE_CHARGEMENT_EN_COURS,
)
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.modele_pagination import ModelePagination
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)


class PanneauSourceArticles(QWidget):
    """Panneau d'onglet : en-tête d'actualisation, tableau, et pagination au pied."""

    demande_actualisation = Signal(str)
    demande_changement_page = Signal(str, int)

    def __init__(self, nom_source: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._nom_source = nom_source
        self._tableau = TableauArticles(self)
        self._etiquette_statut = QLabel(self)
        self._bouton_actualisation = BoutonActualisation(self)
        self._barre_pagination = BarrePagination(self)
        self._page_actuelle = 1
        self._initialiser_interface()
        self._connecter_signaux()

    def _initialiser_interface(self) -> None:
        """Dispose l'en-tête en haut, le tableau au centre et la pagination au pied."""
        mise_en_page = QVBoxLayout(self)
        mise_en_page.setContentsMargins(8, 8, 8, 8)
        mise_en_page.setSpacing(6)

        # 1. En-tête supérieur : libellé à gauche, bouton rotatif en haut à droite
        en_tete_horizontal = QHBoxLayout()
        en_tete_horizontal.setContentsMargins(4, 0, 4, 0)

        self._etiquette_statut.setStyleSheet("color: #4A5568; font-size: 12px; font-weight: 500;")
        self._etiquette_statut.setText(f"{MESSAGE_CHARGEMENT_EN_COURS}{self._nom_source}...")
        en_tete_horizontal.addWidget(self._etiquette_statut)

        en_tete_horizontal.addStretch(1)
        en_tete_horizontal.addWidget(self._bouton_actualisation)
        mise_en_page.addLayout(en_tete_horizontal)

        # 2. Corps : tableau des articles
        mise_en_page.addWidget(self._tableau, stretch=1)

        # 3. Pied : barre de pagination disposée directement au pied du tableau
        mise_en_page.addWidget(self._barre_pagination)

        self.setLayout(mise_en_page)

    def _connecter_signaux(self) -> None:
        """Connecte les interactions utilisateur du panneau."""
        self._bouton_actualisation.clicked.connect(self._sur_clic_actualiser)
        self._barre_pagination.page_changee.connect(self._sur_changement_page)

    def _sur_clic_actualiser(self) -> None:
        """Déclenche la demande d'actualisation manuelle pour cette source."""
        self.demande_actualisation.emit(self._nom_source)

    def _sur_changement_page(self, nouvelle_page: int) -> None:
        """Transmet la demande de changement de page pour cette source."""
        self.demande_changement_page.emit(self._nom_source, nouvelle_page)

    def a_deja_articles(self) -> bool:
        """Indique si le tableau contient déjà des articles affichés."""
        return self._tableau.a_articles_affiches()

    def definir_etat_chargement(self, en_cours: bool) -> None:
        """Active/désactive la rotation de l'icône et fige la barre de pagination."""
        self._barre_pagination.definir_chargement(en_cours)
        if en_cours:
            self._bouton_actualisation.demarrer_rotation()
            self._etiquette_statut.setText(f"Loading {self._nom_source}...")
        else:
            self._bouton_actualisation.arreter_rotation()

    def definir_resultat(self, resultat: ResultatExtractionArticles) -> None:
        """
        Met à jour le tableau et la barre de pagination au pied du tableau.

        :param resultat: Instance de ResultatExtractionArticles.
        """
        self.definir_etat_chargement(False)
        self._page_actuelle = resultat.pagination.page_courante
        self._barre_pagination.mettre_a_jour(resultat.pagination)

        if not resultat.articles:
            self._tableau.vider()
            self._etiquette_statut.setText(f"{self._nom_source}: {MESSAGE_AUCUN_ARTICLE}")
            return

        self._tableau.afficher_articles(resultat.articles)
        self._etiquette_statut.setText(
            f"{self._nom_source} — {len(resultat.articles)} articles ({resultat.pagination.texte_affichage()})"
        )

    def definir_articles(self, articles: List[ModeleArticle]) -> None:
        """Méthode de compatibilité utilisant une pagination par défaut."""
        pagination = ModelePagination(page_courante=self._page_actuelle)
        self.definir_resultat(
            ResultatExtractionArticles(articles=articles, pagination=pagination)
        )

    def afficher_erreur(self, message_erreur: str) -> None:
        """Affiche le message d'erreur et réactive l'interface."""
        self.definir_etat_chargement(False)
        self._etiquette_statut.setText(f"Error ({self._nom_source}): {message_erreur}")

    def obtenir_nom_source(self) -> str:
        """Retourne le nom de la source associée à ce panneau."""
        return self._nom_source
