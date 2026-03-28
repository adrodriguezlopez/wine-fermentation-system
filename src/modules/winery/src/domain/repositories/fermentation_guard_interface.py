"""
Guard interface for fermentation existence checks from the Winery module.

Anti-Corruption Layer (ACL) pattern: Winery defines its own minimal interface
for querying fermentation data it needs (deletion protection), without coupling
to the fermentation module's domain.

This interface is implemented by fermentation's FermentationRepository —
injected at the composition root (dependencies/services.py) via Dependency
Inversion.
"""
from abc import ABC, abstractmethod
from typing import List


class IFermentationGuard(ABC):
    """
    Minimal interface for fermentation existence checks needed by Winery.

    Only exposes what Winery actually needs: checking whether a winery
    has active fermentations before allowing deletion.
    """

    @abstractmethod
    async def get_by_winery(self, winery_id: int) -> List:
        """
        Return active fermentations belonging to a winery.

        Args:
            winery_id: Winery ID to query

        Returns:
            List of fermentation records (may be empty).
            Non-empty list means winery has active fermentation data.
        """
        ...
