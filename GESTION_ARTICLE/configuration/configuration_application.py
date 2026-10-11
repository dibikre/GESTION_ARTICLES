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

# Paramètres des colonnes du tableau d'articles
ENTETES_COLONNES_ARTICLES: Final[List[str]] = ["Image", "Title", "Date"]
INDEX_COLONNE_IMAGE: Final[int] = 0
INDEX_COLONNE_TITRE: Final[int] = 1
INDEX_COLONNE_DATE: Final[int] = 2

LARGEUR_COLONNE_IMAGE: Final[int] = 140
LARGEUR_COLONNE_DATE: Final[int] = 130
HAUTEUR_LIGNE_ARTICLE: Final[int] = 85

# Messages de l'interface utilisateur (en anglais)
MESSAGE_STATUT_PRET: Final[str] = "Ready"
MESSAGE_ONGLET_SELECTIONNE: Final[str] = "Active source: "
MESSAGE_CHARGEMENT_EN_COURS: Final[str] = "Loading articles from "
MESSAGE_CHARGEMENT_SUCCES: Final[str] = " articles loaded successfully from "
MESSAGE_AUCUN_ARTICLE: Final[str] = "No articles available."
MESSAGE_ERREUR_CHARGEMENT: Final[str] = "Failed to load articles from "

