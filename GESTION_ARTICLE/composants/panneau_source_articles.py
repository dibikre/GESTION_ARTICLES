"""
Composant représentant le panneau de contenu d'un onglet de source d'articles.
Intègre le tableau d'articles et le bouton d'actualisation rotatif en haut à droite.
Optimisé pour garantir un affichage fluide et immédiat lors des changements d'onglets.
"""

from typing import List, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from GESTION_ARTICLE.composants.bouton_actualisation import BoutonActualisation
from GESTION_ARTICLE.composants.tableau_articles import TableauArticles
from GESTION_ARTICLE.configuration.configuration_application import (
    MESSAGE_AUCUN_ARTICLE,
    MESSAGE_CHARGEMENT_EN_COURS,
)
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle


class PanneauSourceArticles(QWidget):
    """Vue d'un onglet : en-tête avec bouton d'actualisation en haut à droite et tableau."""

    demande_actualisation = Signal(str)

    def __init__(self, nom_source: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._nom_source = nom_source
        self._tableau = TableauArticles(self)
        self._etiquette_statut = QLabel(self)
        self._bouton_actualisation = BoutonActualisation(self)
        self._initialiser_interface()
        self._connecter_signaux()

    def _initialiser_interface(self) -> None:
        """Dispose les éléments : barre supérieure (titre + bouton en haut à droite) et tableau."""
        mise_en_page = QVBoxLayout(self)
        mise_en_page.setContentsMargins(8, 8, 8, 8)
        mise_en_page.setSpacing(6)

        # En-tête horizontal : libellé à gauche, bouton d'actualisation en haut à droite
        en_tete_horizontal = QHBoxLayout()
        en_tete_horizontal.setContentsMargins(4, 0, 4, 0)

        self._etiquette_statut.setStyleSheet("color: #4A5568; font-size: 12px; font-weight: 500;")
        self._etiquette_statut.setText(f"{MESSAGE_CHARGEMENT_EN_COURS}{self._nom_source}...")
        en_tete_horizontal.addWidget(self._etiquette_statut)

        en_tete_horizontal.addStretch(1)

        # Bouton d'actualisation placé en haut à droite dans l'onglet
        en_tete_horizontal.addWidget(self._bouton_actualisation)
        mise_en_page.addLayout(en_tete_horizontal)

        # Tableau des articles occupant l'espace restant
        mise_en_page.addWidget(self._tableau, stretch=1)
        self.setLayout(mise_en_page)

    def _connecter_signaux(self) -> None:
        """Transmet l'événement de clic du bouton d'actualisation vers le contrôleur."""
        self._bouton_actualisation.clicked.connect(self._sur_clic_actualiser)

    def _sur_clic_actualiser(self) -> None:
        """Déclenche la demande de rafraîchissement manuel pour cette source."""
        self.demande_actualisation.emit(self._nom_source)

    def a_deja_articles(self) -> bool:
        """Indique si le panneau a déjà ses données prêtes et affichées (pour zéro latence)."""
        return self._tableau.a_articles_affiches()

    def definir_etat_chargement(self, en_cours: bool) -> None:
        """
        Active ou désactive la rotation de l'icône pendant l'appel réseau.

        :param en_cours: True si la mise à jour est en cours, False une fois terminée.
        """
        if en_cours:
            self._bouton_actualisation.demarrer_rotation()
            self._etiquette_statut.setText(f"Updating {self._nom_source}...")
        else:
            self._bouton_actualisation.arreter_rotation()

    def definir_articles(self, articles: List[ModeleArticle]) -> None:
        """
        Met à jour le tableau avec les articles et stoppe la rotation de l'icône.

        :param articles: Liste d'articles à afficher.
        """
        self.definir_etat_chargement(False)
        if not articles:
            self._tableau.vider()
            self._etiquette_statut.setText(f"{self._nom_source}: {MESSAGE_AUCUN_ARTICLE}")
            return

        self._tableau.afficher_articles(articles)
        self._etiquette_statut.setText(
            f"{self._nom_source} — {len(articles)} articles loaded"
        )

    def afficher_erreur(self, message_erreur: str) -> None:
        """Affiche le message d'erreur et arrête la rotation de l'icône."""
        self.definir_etat_chargement(False)
        self._etiquette_statut.setText(f"Error ({self._nom_source}): {message_erreur}")

    def obtenir_nom_source(self) -> str:
        """Retourne le nom de la source associée à ce panneau."""
        return self._nom_source
