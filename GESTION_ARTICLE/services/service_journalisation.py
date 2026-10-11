"""
Service de journalisation centralisé de l'application.
Fournit une configuration standardisée des journaux (logs).
"""

import logging
import sys
from typing import Optional


class ServiceJournalisation:
    """Gestionnaire central de journalisation pour l'application."""

    _journal_principal: Optional[logging.Logger] = None

    @classmethod
    def initialiser(cls, niveau: int = logging.INFO) -> logging.Logger:
        """
        Configure et retourne le journal principal de l'application.

        :param niveau: Niveau de sévérité du journal.
        :return: Instance configurée de logging.Logger.
        """
        if cls._journal_principal is not None:
            return cls._journal_principal

        logger = logging.getLogger("GESTION_ARTICLE")
        logger.setLevel(niveau)

        # Nettoyage d'anciens gestionnaires s'il y en a
        if not logger.handlers:
            gestionnaire_flux = logging.StreamHandler(sys.stdout)
            format_journal = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            gestionnaire_flux.setFormatter(format_journal)
            logger.addHandler(gestionnaire_flux)

        cls._journal_principal = logger
        logger.info("Application logging system initialized successfully.")
        return logger

    @classmethod
    def obtenir_journal(cls, nom_module: str) -> logging.Logger:
        """
        Retourne un sous-journal pour un module spécifique.

        :param nom_module: Nom du module appelant.
        :return: Instance de logging.Logger.
        """
        if cls._journal_principal is None:
            cls.initialiser()
        return logging.getLogger(f"GESTION_ARTICLE.{nom_module}")
