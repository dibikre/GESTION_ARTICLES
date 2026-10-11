#!/usr/bin/env python3
"""
Point d'entrée principal pour le lancement de l'application PySide6.
"""

import os
import sys

# Assure que le dossier parent est présent dans sys.path
DOSSIER_COURANT = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PARENT = os.path.dirname(DOSSIER_COURANT)
if DOSSIER_PARENT not in sys.path:
    sys.path.insert(0, DOSSIER_PARENT)
if DOSSIER_COURANT not in sys.path:
    sys.path.insert(0, DOSSIER_COURANT)

try:
    from PySide6.QtWidgets import QApplication
    PYSIDE6_DISPONIBLE = True
except ImportError:
    PYSIDE6_DISPONIBLE = False

from GESTION_ARTICLE.configuration.configuration_theme import (
    FEUILLE_DE_STYLE_APPLICATION,
)
from GESTION_ARTICLE.controleurs.controleur_principal import ControleurPrincipal
from GESTION_ARTICLE.services.service_chargement_image import ServiceChargementImage
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation
from GESTION_ARTICLE.vues.fenetre_principale import FenetrePrincipale


def demarrer_application() -> int:
    """Initialise et exécute l'application PySide6."""
    journal = ServiceJournalisation.initialiser()
    journal.info("Starting Article Management Desktop GUI Application...")

    if not PYSIDE6_DISPONIBLE:
        journal.critical(
            "PySide6 is not installed. Please run: pip install -r requirements.txt"
        )
        return 1

    application = QApplication(sys.argv)
    application.setStyleSheet(FEUILLE_DE_STYLE_APPLICATION)

    ServiceChargementImage.initialiser()

    controleur = ControleurPrincipal()
    fenetre = FenetrePrincipale(controleur=controleur)
    fenetre.show()

    journal.info("Main window displayed with tabs configured.")
    return application.exec()


if __name__ == "__main__":
    code_sortie = demarrer_application()
    sys.exit(code_sortie)
