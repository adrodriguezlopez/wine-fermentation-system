"""
API Component for Fermentation Management
---------------------------------------
REST endpoints for fermentation and sample operations.
Handles:
- Fermentation CRUD operations
- Sample data submissions
- Status queries
- Data retrieval endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/fermentation", tags=["fermentation"])

# Endpoints will be implemented here following the REST pattern
# POST /fermentations - Create new fermentation
# GET /fermentations - List fermentations
# GET /fermentations/{id} - Get specific fermentation
# POST /fermentations/{id}/samples - Add sample to fermentation
# etc.
