"""
Guard interface for vineyard existence checks from the Winery module.

Anti-Corruption Layer (ACL) pattern: Winery defines its own minimal interface
for querying vineyard data it needs (deletion protection), without coupling to
the fruit_origin module's domain.

This interface is implemented by fruit_origin's VineyardRepository — injected
at the composition root (dependencies/services.py) via Dependency Inversion.
"""
from abc import ABC, abstractmethod
from typing import List


class IVineyardGuard(ABC):
    """
    Minimal interface for vineyard existence checks needed by Winery.

    Only exposes what Winery actually needs: checking whether a winery
    has active vineyards before allowing deletion.
    """

    @abstractmethod
    async def get_by_winery(self, winery_id: int) -> List:
        """
        Return active vineyards belonging to a winery.

        Args:
            winery_id: Winery ID to query

        Returns:
            List of vineyard records (may be empty).
            Non-empty list means winery has active vineyard data.
        """
        ...
