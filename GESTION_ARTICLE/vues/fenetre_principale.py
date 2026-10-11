"""
Fenêtre principale de l'application de gestion d'articles (PySide6).
Intègre la pagination au pied de chaque tableau de source et la navigation fluide.
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from GESTION_ARTICLE.composants.barre_etat import BarreEtat
from GESTION_ARTICLE.composants.conteneur_onglets import ConteneurOnglets
from GESTION_ARTICLE.configuration.configuration_application import (
    HAUTEUR_INITIALE,
    HAUTEUR_MINIMALE,
    LARGEUR_INITIALE,
    LARGEUR_MINIMALE,
    MESSAGE_STATUT_PRET,
    TITRE_APPLICATION,
)
from GESTION_ARTICLE.controleurs.controleur_principal import ControleurPrincipal
from GESTION_ARTICLE.modeles.modele_article import ModeleArticle
from GESTION_ARTICLE.modeles.resultat_extraction_articles import (
    ResultatExtractionArticles,
)


class FenetrePrincipale(QMainWindow):
    """
    Fenêtre principale de l'application.
    Gère la disposition des composants visuels, la pagination et le contrôleur.
    """

    def __init__(
        self,
        controleur: ControleurPrincipal,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._controleur = controleur
        self._conteneur_onglets = ConteneurOnglets(self)
        self._barre_etat = BarreEtat(self)

        self._configurer_fenetre()
        self._construire_interface()
        self._connecter_evenements()
        self._initialiser_donnees()

    def _configurer_fenetre(self) -> None:
        """Définit les dimensions et le titre de la fenêtre principale."""
        self.setWindowTitle(TITRE_APPLICATION)
        self.resize(LARGEUR_INITIALE, HAUTEUR_INITIALE)
        self.setMinimumSize(LARGEUR_MINIMALE, HAUTEUR_MINIMALE)
        self.setStatusBar(self._barre_etat)

    def _construire_interface(self) -> None:
        """Construit l'agencement responsive avec onglets alignés en haut à gauche."""
        widget_central = QWidget(self)
        mise_en_page_principale = QVBoxLayout(widget_central)
        mise_en_page_principale.setContentsMargins(12, 12, 12, 12)
        mise_en_page_principale.setSpacing(8)

        disposition_onglets = QHBoxLayout()
        disposition_onglets.setContentsMargins(0, 0, 0, 0)
        disposition_onglets.addWidget(
            self._conteneur_onglets,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )

        mise_en_page_principale.addWidget(self._conteneur_onglets, stretch=1)
        self.setCentralWidget(widget_central)

    def _connecter_evenements(self) -> None:
        """Associe les signaux des composants aux méthodes du contrôleur."""
        self._conteneur_onglets.onglet_change.connect(self._sur_changement_onglet)
        self._conteneur_onglets.demande_actualisation.connect(
            self._controleur.actualiser_source
        )
        self._conteneur_onglets.demande_changement_page.connect(
            self._controleur.changer_page_source
        )
        self._controleur.resultat_receptionne.connect(self._sur_resultat_receptionne)
        self._controleur.articles_receptionnes.connect(self._sur_articles_receptionnes)
        self._controleur.statut_modifie.connect(self._barre_etat.definir_message)
        self._controleur.etat_chargement_change.connect(self._sur_etat_chargement_change)

    def _initialiser_donnees(self) -> None:
        """Initialise les onglets et lance le chargement non volontaire uniquement au démarrage."""
        titres = self._controleur.obtenir_titres_sources()
        self._conteneur_onglets.initialiser_onglets_sources(titres)
        self._barre_etat.definir_message(MESSAGE_STATUT_PRET)

        if titres:
            premier_onglet = titres[0]
            self._controleur.traiter_selection_onglet(0, premier_onglet)

    def _sur_changement_onglet(self, index: int, titre: str) -> None:
        """Bascule d'onglet avec fluidité totale."""
        panneau = self._conteneur_onglets.obtenir_panneau_source(titre)
        if panneau and panneau.a_deja_articles():
            self._barre_etat.definir_message(f"Active source: {titre} (Cached)")
            return

        message_statut = self._controleur.traiter_selection_onglet(index, titre)
        self._barre_etat.definir_message(message_statut)

    def _sur_resultat_receptionne(
        self, nom_source: str, resultat: ResultatExtractionArticles
    ) -> None:
        """Met à jour le tableau et la barre de pagination du panneau concerné."""
        panneau = self._conteneur_onglets.obtenir_panneau_source(nom_source)
        if panneau:
            panneau.definir_resultat(resultat)

    def _sur_articles_receptionnes(
        self, nom_source: str, articles: List[ModeleArticle]
    ) -> None:
        """Injecte les articles dans le panneau (compatibilité)."""
        panneau = self._conteneur_onglets.obtenir_panneau_source(nom_source)
        if panneau and not panneau.a_deja_articles():
            panneau.definir_articles(articles)

    def _sur_etat_chargement_change(self, nom_source: str, en_cours: bool) -> None:
        """Contrôle la rotation de l'icône d'actualisation et l'état de la pagination."""
        panneau = self._conteneur_onglets.obtenir_panneau_source(nom_source)
        if panneau:
            panneau.definir_etat_chargement(en_cours)
