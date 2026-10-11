"""
Service de téléchargement et de mise en cache des vignettes d'articles.
"""

from typing import Dict, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ServiceChargementImage:
    """Gestionnaire de cache et de téléchargement des images des articles."""

    _cache: Dict[str, QPixmap] = {}
    _image_par_defaut: Optional[QPixmap] = None

    @classmethod
    def obtenir_pixmap_par_defaut(cls, largeur: int = 120, hauteur: int = 70) -> QPixmap:
        """Génère une image placeholder sobre pour les articles sans vignette."""
        if cls._image_par_defaut is None:
            pixmap = QPixmap(largeur, hauteur)
            pixmap.fill(QColor("#E2E8F0"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#718096"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No Image")
            painter.end()
            cls._image_par_defaut = pixmap
        return cls._image_par_defaut

    @classmethod
    def charger_pixmap_depuis_url(
        cls,
        url_image: Optional[str],
        largeur_cible: int = 120,
        hauteur_cible: int = 70,
    ) -> QPixmap:
        """
        Télécharge ou récupère du cache la vignette sous forme de QPixmap redimensionné.

        :param url_image: URL distante de l'image.
        :param largeur_cible: Largeur de la vignette.
        :param hauteur_cible: Hauteur de la vignette.
        :return: QPixmap prêt pour l'affichage dans le tableau.
        """
        if not url_image or not url_image.strip():
            return cls.obtenir_pixmap_par_defaut(largeur_cible, hauteur_cible)

        cle_cache = f"{url_image}_{largeur_cible}x{hauteur_cible}"
        if cle_cache in cls._cache:
            return cls._cache[cle_cache]

        try:
            import requests

            reponse = requests.get(url_image, timeout=8)
            if reponse.status_code == 200 and reponse.content:
                image_qt = QImage()
                if image_qt.loadFromData(reponse.content):
                    pixmap = QPixmap.fromImage(image_qt)
                    pixmap_redimensionne = pixmap.scaled(
                        largeur_cible,
                        hauteur_cible,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    cls._cache[cle_cache] = pixmap_redimensionne
                    return pixmap_redimensionne
        except Exception:
            pass

        return cls.obtenir_pixmap_par_defaut(largeur_cible, hauteur_cible)
