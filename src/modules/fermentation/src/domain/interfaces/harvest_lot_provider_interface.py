"""
Harvest lot provider interface for the Fermentation module's ETL service.

Anti-Corruption Layer (ACL) pattern: Fermentation defines its own minimal
interface for the single operation it needs from the fruit_origin module
during ETL import, without coupling to fruit_origin's full service contract.

This interface is implemented by fruit_origin's FruitOriginService — injected
at the composition root via Dependency Inversion.
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional


class IHarvestLotProvider(ABC):
    """
    Minimal interface for harvest lot orchestration needed by ETL import.

    Only exposes the single method that the ETL service requires:
    ensuring a complete vineyard → block → harvest lot hierarchy exists
    for a given import row.
    """

    @abstractmethod
    async def ensure_harvest_lot_for_import(
        self,
        winery_id: int,
        vineyard_name: Optional[str],
        grape_variety: Optional[str],
        harvest_date: date,
        harvest_mass_kg: Optional[Decimal],
    ):
        """
        Ensure a complete fruit-origin hierarchy exists for an ETL import row.

        Orchestrates creation of vineyard, vineyard block, and harvest lot
        as needed, reusing existing records where possible.

        Args:
            winery_id: Winery ID for multi-tenancy
            vineyard_name: Optional vineyard name (defaults to UNKNOWN)
            grape_variety: Optional grape variety (defaults to UNKNOWN)
            harvest_date: Harvest date
            harvest_mass_kg: Optional harvest mass in kilograms

        Returns:
            HarvestLot — created or existing record.
        """
        ...
