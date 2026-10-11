"""
Composant graphique représentant un bouton d'actualisation avec icône rotative.
Dessin vectoriel pur via QPainter (sans aucun emoji ni symbole Unicode).
L'icône pivote de manière fluide pendant la mise à jour des flux.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget


class BoutonActualisation(QAbstractButton):
    """Bouton rond ou carré avec flèche circulaire vectorielle animée en rotation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._angle_rotation = 0.0
        self._est_en_rotation = False
        self._timer_animation = QTimer(self)
        self._initialiser_composant()

    def _initialiser_composant(self) -> None:
        """Configure les dimensions et le minuteur d'animation."""
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Refresh articles")

        self._timer_animation.setInterval(25)
        self._timer_animation.timeout.connect(self._animer_rotation)

    def _animer_rotation(self) -> None:
        """Incrémente l'angle de rotation et déclenche le redessin."""
        self._angle_rotation = (self._angle_rotation + 12.0) % 360.0
        self.update()

    def demarrer_rotation(self) -> None:
        """Active l'animation rotative continue et désactive temporairement le clic."""
        self._est_en_rotation = True
        self.setEnabled(False)
        self._timer_animation.start()
        self.update()

    def arreter_rotation(self) -> None:
        """Stoppe l'animation rotative et réinitialise l'orientation."""
        self._est_en_rotation = False
        self.setEnabled(True)
        self._timer_animation.stop()
        self._angle_rotation = 0.0
        self.update()

    def est_en_rotation(self) -> bool:
        """Indique si une mise à jour est activement en cours."""
        return self._est_en_rotation

    def paintEvent(self, event) -> None:
        """Dessine l'icône vectorielle de rafraîchissement avec support de rotation."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        centre_x = rect.width() / 2.0
        centre_y = rect.height() / 2.0

        # Arrière-plan au survol
        if self.underMouse() and self.isEnabled():
            painter.setBrush(QColor("#F1F5F9"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

        # Déplacement et rotation du repère graphique
        painter.translate(centre_x, centre_y)
        painter.rotate(self._angle_rotation)

        # Définition de la couleur de l'icône (rouge principal si actif ou survolé)
        couleur = QColor("#DC2626") if self._est_en_rotation or self.underMouse() else QColor("#4A5568")

        stylo = QPen(couleur, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(stylo)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Dessin de l'arc de cercle (environ 270 degrés)
        rayon = 8.0
        rect_arc = QRectF(-rayon, -rayon, rayon * 2, rayon * 2)
        angle_depart = 45 * 16
        angle_etendue = 270 * 16
        painter.drawArc(rect_arc, angle_depart, angle_etendue)

        # Flèche triangulaire à l'extrémité de l'arc
        pointe_x = rayon * 0.7
        pointe_y = -rayon * 0.7
        path_fleche = QPainterPath()
        path_fleche.moveTo(pointe_x, pointe_y - 3.5)
        path_fleche.lineTo(pointe_x + 3.5, pointe_y + 1.5)
        path_fleche.lineTo(pointe_x - 3.0, pointe_y + 1.5)
        path_fleche.closeSubpath()

        painter.setBrush(couleur)
        painter.drawPath(path_fleche)
        painter.end()
