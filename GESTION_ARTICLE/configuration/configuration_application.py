"""
Module de configuration générale de l'application.
"""

from typing import Final, List

# Paramètres de la fenêtre principale
TITRE_APPLICATION: Final[str] = "Article Management"
LARGEUR_INITIALE: Final[int] = 1100
HAUTEUR_INITIALE: Final[int] = 750
LARGEUR_MINIMALE: Final[int] = 800
HAUTEUR_MINIMALE: Final[int] = 500

# Liste des onglets de sources d'articles
LISTE_ONGLETS_SOURCES: Final[List[str]] = [
    "STATTIMES",
    "SUPPLYCHAINDIVE",
    "AIRCARGOWEEK",
    "FREIGHTWAVES",
    "SEATRADE-MARITIME",
]

# Messages de l'interface utilisateur (en anglais)
MESSAGE_STATUT_PRET: Final[str] = "Ready"
MESSAGE_ONGLET_SELECTIONNE: Final[str] = "Active source: "
