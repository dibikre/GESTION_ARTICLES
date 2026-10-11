"""
Fabrique pour instancier les extracteurs selon le nom de la source (SOLID / OCP).
"""

from typing import Dict, Optional
from GESTION_ARTICLE.services.extracteurs.extracteur_aircargoweek import (
    ExtracteurAirCargoWeek,
)
from GESTION_ARTICLE.services.extracteurs.extracteur_freightwaves import (
    ExtracteurFreightWaves,
)
from GESTION_ARTICLE.services.extracteurs.extracteur_seatrade import (
    ExtracteurSeatrade,
)
from GESTION_ARTICLE.services.extracteurs.extracteur_stattimes import (
    ExtracteurStatTimes,
)
from GESTION_ARTICLE.services.extracteurs.extracteur_supplychaindive import (
    ExtracteurSupplyChainDive,
)
from GESTION_ARTICLE.services.extracteurs.interface_extracteur import (
    InterfaceExtracteurArticles,
)


class FabriqueExtracteurs:
    """Fournit l'extracteur approprié en fonction du nom de l'onglet source."""

    _instances: Dict[str, InterfaceExtracteurArticles] = {}

    @classmethod
    def obtenir_extracteur(cls, nom_source: str) -> Optional[InterfaceExtracteurArticles]:
        """
        Retourne l'extracteur correspondant au nom de la source.

        :param nom_source: Titre de la source (ex. STATTIMES, FREIGHTWAVES).
        :return: Instance de InterfaceExtracteurArticles ou None si inconnu.
        """
        cle = nom_source.upper().strip()
        if cle in cls._instances:
            return cls._instances[cle]

        extracteur: Optional[InterfaceExtracteurArticles] = None

        if cle == "AIRCARGOWEEK":
            extracteur = ExtracteurAirCargoWeek()
        elif cle == "FREIGHTWAVES":
            extracteur = ExtracteurFreightWaves()
        elif cle == "SEATRADE-MARITIME":
            extracteur = ExtracteurSeatrade()
        elif cle == "STATTIMES":
            extracteur = ExtracteurStatTimes()
        elif cle == "SUPPLYCHAINDIVE":
            extracteur = ExtracteurSupplyChainDive()

        if extracteur is not None:
            cls._instances[cle] = extracteur

        return extracteur
