"""
Service de téléchargement asynchrone et de mise en cache mémoire des vignettes.
Garantit que le thread principal de l'interface graphique ne ralentit jamais.
"""

from typing import Dict, Optional, Set
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap


class SignauxChargementImage(QObject):
    """Signaux PySide6 pour la transmission asynchrone des vignettes téléchargées."""

    image_disponible = Signal(str, QPixmap)


class TacheTelechargementVignette(QRunnable):
    """Tâche d'arrière-plan exécutée dans le pool de threads pour charger une image."""

    def __init__(
        self,
        url_image: str,
        largeur_cible: int,
        hauteur_cible: int,
        signaux: SignauxChargementImage,
    ) -> None:
        super().__init__()
        self._url_image = url_image
        self._largeur = largeur_cible
        self._hauteur = hauteur_cible
        self._signaux = signaux

    def run(self) -> None:
        """Télécharge et redimensionne la vignette hors du thread d'affichage."""
        try:
            import requests

            reponse = requests.get(self._url_image, timeout=6)
            if reponse.status_code == 200 and reponse.content:
                image_qt = QImage()
                if image_qt.loadFromData(reponse.content):
                    pixmap = QPixmap.fromImage(image_qt)
                    pixmap_final = pixmap.scaled(
                        self._largeur,
                        self._hauteur,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self._signaux.image_disponible.emit(self._url_image, pixmap_final)
        except Exception:
            pass


class ServiceChargementImage:
    """Gestionnaire performant de vignettes en mémoire avec chargement en arrière-plan."""

    _cache: Dict[str, QPixmap] = {}
    _en_cours: Set[str] = set()
    _image_par_defaut: Optional[QPixmap] = None
    _signaux = SignauxChargementImage()

    @classmethod
    def initialiser(cls) -> None:
        """Connecte les signaux d'achèvement de téléchargement."""
        try:
            cls._signaux.image_disponible.connect(cls._enregistrer_dans_cache)
        except Exception:
            pass

    @classmethod
    def _enregistrer_dans_cache(cls, url: str, pixmap: QPixmap) -> None:
        """Conserve la vignette en mémoire vive."""
        cls._cache[url] = pixmap
        if url in cls._en_cours:
            cls._en_cours.remove(url)

    @classmethod
    def obtenir_pixmap_par_defaut(
        cls, largeur: int = 120, hauteur: int = 70
    ) -> QPixmap:
        """Placeholder instantané sans latence."""
        if cls._image_par_defaut is None:
            pixmap = QPixmap(largeur, hauteur)
            pixmap.fill(QColor("#EDF2F7"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#A0AEC0"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Image")
            painter.end()
            cls._image_par_defaut = pixmap
        return cls._image_par_defaut

    @classmethod
    def obtenir_pixmap(
        cls,
        url_image: Optional[str],
        largeur_cible: int = 120,
        hauteur_cible: int = 68,
        sur_image_prete=None,
    ) -> QPixmap:
        """
        Retourne immédiatement le pixmap (en cache ou défaut) SANS bloquer l'affichage.
        Si non en cache, démarre un thread d'arrière-plan discret.
        """
        if not url_image or not url_image.strip():
            return cls.obtenir_pixmap_par_defaut(largeur_cible, hauteur_cible)

        # Restitution immédiate depuis le cache mémoire (0 ms)
        if url_image in cls._cache:
            return cls._cache[url_image]

        # Lancement asynchrone non-bloquant en arrière-plan
        if url_image not in cls._en_cours:
            cls._en_cours.add(url_image)
            if sur_image_prete:
                cls._signaux.image_disponible.connect(sur_image_prete)

            tache = TacheTelechargementVignette(
                url_image=url_image,
                largeur_cible=largeur_cible,
                hauteur_cible=hauteur_cible,
                signaux=cls._signaux,
            )
            QThreadPool.globalInstance().start(tache)

        return cls.obtenir_pixmap_par_defaut(largeur_cible, hauteur_cible)
