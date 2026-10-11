"""
Fenêtre principale de l'application de gestion d'articles (PySide6).
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
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


class FenetrePrincipale(QMainWindow):
    """
    Fenêtre principale de l'application.
    Gère la disposition des composants visuels et délègue les actions au contrôleur.
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

        # Disposition supérieure alignant les onglets en haut à gauche
        disposition_onglets = QHBoxLayout()
        disposition_onglets.setContentsMargins(0, 0, 0, 0)
        disposition_onglets.addWidget(
            self._conteneur_onglets,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )

        # Les onglets occupent toute la largeur disponible pour rester réactifs
        mise_en_page_principale.addWidget(self._conteneur_onglets, stretch=1)

        self.setCentralWidget(widget_central)

    def _connecter_evenements(self) -> None:
        """Associe les signaux des composants aux méthodes du contrôleur."""
        self._conteneur_onglets.onglet_change.connect(self._sur_changement_onglet)

    def _initialiser_donnees(self) -> None:
        """Injecte les sources définies par le contrôleur dans les onglets."""
        titres = self._controleur.obtenir_titres_sources()
        self._conteneur_onglets.initialiser_onglets_sources(titres)
        self._barre_etat.definir_message(MESSAGE_STATUT_PRET)

    def _sur_changement_onglet(self, index: int, titre: str) -> None:
        """Transmet l'événement au contrôleur et met à jour la barre d'état."""
        message_statut = self._controleur.traiter_selection_onglet(index, titre)
        self._barre_etat.definir_message(message_statut)
