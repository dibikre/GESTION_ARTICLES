"""
Contrôleur principal orchestrant les interactions utilisateur et le flux de données.
"""

from typing import List, Optional
from GESTION_ARTICLE.configuration.configuration_application import (
    LISTE_ONGLETS_SOURCES,
    MESSAGE_ONGLET_SELECTIONNE,
    MESSAGE_STATUT_PRET,
)
from GESTION_ARTICLE.modeles.modele_source_article import ModeleSourceArticle
from GESTION_ARTICLE.services.service_journalisation import ServiceJournalisation


class ControleurPrincipal:
    """Orchestre la navigation entre onglets et la gestion des articles."""

    def __init__(self) -> None:
        self._journal = ServiceJournalisation.obtenir_journal("ControleurPrincipal")
        self._sources: List[ModeleSourceArticle] = []
        self._source_active: Optional[ModeleSourceArticle] = None
        self._initialiser_sources()

    def _initialiser_sources(self) -> None:
        """Initialise la liste des sources d'articles à partir de la configuration."""
        self._sources = [
            ModeleSourceArticle(identifiant=titre, titre_affichage=titre)
            for titre in LISTE_ONGLETS_SOURCES
        ]
        if self._sources:
            self._source_active = self._sources[0]
        self._journal.info(
            "Initialized %d article sources successfully.", len(self._sources)
        )

    def obtenir_titres_sources(self) -> List[str]:
        """Retourne la liste ordonnée des titres de sources."""
        return [source.titre_affichage for source in self._sources]

    def traiter_selection_onglet(self, index: int, titre: str) -> str:
        """
        Traite le changement d'onglet déclenché par l'utilisateur.

        :param index: Index de l'onglet sélectionné.
        :param titre: Nom de la source sélectionnée.
        :return: Message de statut formaté en anglais pour la barre d'état.
        """
        self._journal.info("Tab selected by user: index=%d, source='%s'", index, titre)

        source_trouvee = next(
            (s for s in self._sources if s.titre_affichage == titre), None
        )
        if source_trouvee:
            self._source_active = source_trouvee
            return f"{MESSAGE_ONGLET_SELECTIONNE}{titre}"

        return MESSAGE_STATUT_PRET

    def obtenir_source_active(self) -> Optional[ModeleSourceArticle]:
        """Retourne le modèle de la source actuellement active."""
        return self._source_active
