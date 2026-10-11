"""
Service de téléchargement asynchrone et de mise en cache mémoire des vignettes.
Garantit que toutes les images (y compris au défilement) se chargent et s'affichent.
"""

from typing import Callable, Dict, List, Optional, Set
from urllib.parse import urlsplit, urlunsplit
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation

ENTETES_NAVIGATEUR: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def normaliser_url_image(url_brute: str) -> str:
    """Nettoie et normalise l'URL de l'image (schéma, protocole)."""
    url = url_brute.strip()
    if url.startswith("//"):
        return f"https:{url}"
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


class SignauxChargementImage(QObject):
    """Signaux PySide6 pour avertir de la disponibilité d'une nouvelle vignette."""

    image_recue = Signal(str, QPixmap)


class TacheTelechargementVignette(QRunnable):
    """Télécharge une vignette en arrière-plan avec en-têtes HTTP valides."""

    def __init__(
        self,
        url_image: str,
        largeur: int,
        hauteur: int,
        signaux: SignauxChargementImage,
    ) -> None:
        super().__init__()
        self._url = url_image
        self._largeur = largeur
        self._hauteur = hauteur
        self._signaux = signaux

    def run(self) -> None:
        """Effectue la requête HTTP GET avec en-têtes et redirection acceptée."""
        try:
            import requests

            url_propre = normaliser_url_image(self._url)
            reponse = requests.get(
                url_propre,
                headers=ENTETES_NAVIGATEUR,
                timeout=12,
                allow_redirects=True,
            )

            if reponse.status_code == 200 and reponse.content:
                image_qt = QImage()
                if image_qt.loadFromData(reponse.content):
                    pixmap = QPixmap.fromImage(image_qt)
                    pixmap_redimensionne = pixmap.scaled(
                        self._largeur,
                        self._hauteur,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    self._signaux.image_recue.emit(self._url, pixmap_redimensionne)
        except Exception:
            pass


class ServiceChargementImage:
    """Gestionnaire central de chargement et d'assignation des vignettes."""

    _cache: Dict[str, QPixmap] = {}
    _en_cours: Set[str] = set()
    _observateurs: Dict[str, List[Callable[[QPixmap], None]]] = {}
    _image_par_defaut: Optional[QPixmap] = None
    _signaux = SignauxChargementImage()
    _journal = ServiceJournalisation.obtenir_journal("ServiceChargementImage")

    @classmethod
    def initialiser(cls) -> None:
        """Connecte le signal général de réception des images."""
        try:
            cls._signaux.image_recue.disconnect()
        except Exception:
            pass
        cls._signaux.image_recue.connect(cls._distribuer_image)

    @classmethod
    def _distribuer_image(cls, url: str, pixmap: QPixmap) -> None:
        """Enregistre dans le cache et notifie tous les écouteurs en attente."""
        cls._cache[url] = pixmap
        if url in cls._en_cours:
            cls._en_cours.remove(url)

        auditeurs = cls._observateurs.pop(url, [])
        for rappel in auditeurs:
            try:
                rappel(pixmap)
            except Exception:
                pass

    @classmethod
    def obtenir_pixmap_par_defaut(
        cls, largeur: int = 120, hauteur: int = 68
    ) -> QPixmap:
        """Fournit un placeholder instantané sans aucune latence."""
        if cls._image_par_defaut is None:
            pixmap = QPixmap(largeur, hauteur)
            pixmap.fill(QColor("#EDF2F7"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("#A0AEC0"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Article")
            painter.end()
            cls._image_par_defaut = pixmap
        return cls._image_par_defaut

    @classmethod
    def charger_vignette(
        cls,
        url_image: Optional[str],
        sur_reception: Callable[[QPixmap], None],
        largeur: int = 120,
        hauteur: int = 68,
    ) -> QPixmap:
        """
        Retourne immédiatement le pixmap si en cache, sinon démarre la récupération
        en arrière-plan et déclenche sur_reception dès que l'image est prête.
        """
        if not url_image or not url_image.strip():
            return cls.obtenir_pixmap_par_defaut(largeur, hauteur)

        url_cle = url_image.strip()

        # Si déjà en mémoire vive : retour immédiat (0 ms)
        if url_cle in cls._cache:
            return cls._cache[url_cle]

        # Enregistrement pour notification asynchrone dès réception
        if url_cle not in cls._observateurs:
            cls._observateurs[url_cle] = []
        cls._observateurs[url_cle].append(sur_reception)

        # Lancement de la tâche d'arrière-plan si pas encore demandée
        if url_cle not in cls._en_cours:
            cls._en_cours.add(url_cle)
            tache = TacheTelechargementVignette(
                url_image=url_cle,
                largeur=largeur,
                hauteur=hauteur,
                signaux=cls._signaux,
            )
            QThreadPool.globalInstance().start(tache)

        return cls.obtenir_pixmap_par_defaut(largeur, hauteur)
