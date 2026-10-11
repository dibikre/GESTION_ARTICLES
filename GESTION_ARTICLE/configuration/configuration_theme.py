"""
Module de configuration graphique et de styles pour l'application PySide6.
"""

from typing import Final

# Feuilles de style QSS pour l'application desktop
FEUILLE_DE_STYLE_APPLICATION: Final[str] = """
QMainWindow {
    background-color: #F8F9FA;
    color: #1A202C;
}

QWidget {
    background-color: #F8F9FA;
    color: #1A202C;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* Barre d'onglets positionnée en haut */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background-color: #FFFFFF;
    border-radius: 4px;
    top: -1px;
}

QTabBar::tab {
    background-color: #EDF2F7;
    color: #4A5568;
    border: 1px solid #CBD5E0;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: 600;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #1A202C;
    border-color: #CBD5E0;
    border-bottom: 2px solid #DC2626;
}

QTabBar::tab:hover:!selected {
    background-color: #E2E8F0;
    color: #2D3748;
}

/* Boutons principaux rouges conformément aux directives */
QPushButton.bouton_principal {
    background-color: #DC2626;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton.bouton_principal:hover {
    background-color: #B91C1C;
}

QPushButton.bouton_principal:pressed {
    background-color: #991B1B;
}

/* Boutons secondaires */
QPushButton.bouton_secondaire {
    background-color: #FFFFFF;
    color: #1A202C;
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    padding: 8px 16px;
}

QPushButton.bouton_secondaire:hover {
    background-color: #F7FAFC;
    border-color: #A0AEC0;
}

/* Barre de statut */
QStatusBar {
    background-color: #FFFFFF;
    color: #718096;
    border-top: 1px solid #E2E8F0;
    padding: 4px 8px;
    font-size: 12px;
}
"""
