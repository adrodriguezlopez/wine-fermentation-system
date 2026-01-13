"""
Integration tests for Historical Data API.

Tests all endpoints against real PostgreSQL database to ensure:
- End-to-end data flow from API → Service → Repository → Database
- Multi-tenant isolation (winery_id scoping)
- Data source filtering (data_source='HISTORICAL')
- Pagination and filtering work correctly
- Pattern extraction aggregates real data
- Error handling for edge cases

Database: localhost:5433/wine_fermentation_test

Related ADR: ADR-032 (Historical Data API Layer)
"""
import pytest
from datetime import datetime, date

from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus


# ============================================================================
# TEST CLASSES
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestListHistoricalFermentations:
    """Test GET /api/fermentation/historical - list historical fermentations."""
    
    async def test_list_filters_by_data_source_historical(
        self, test_client, historical_fermentation, test_models, db_session, test_user
    ):
        """Only fermentations with data_source='HISTORICAL' are returned."""
        # Create a non-historical fermentation (data_source='MANUAL')
        Fermentation = test_models['Fermentation']
        manual_ferm = Fermentation(
            winery_id=test_user.winery_id,
            fermented_by_user_id=test_user.id,
            vintage_year=2023,
            yeast_strain="EC-1118",
            vessel_code="MANUAL-001",
            input_mass_kg=500.0,
            initial_sugar_brix=22.0,
            initial_density=1.092,
            start_date=datetime(2023, 8, 1, 8, 0, 0),
            status=FermentationStatus.ACTIVE,
            data_source="MANUAL"  # Different source
        )
        db_session.add(manual_ferm)
        await db_session.flush()
        
        # List historical fermentations
        response = await test_client.get("/api/fermentation/historical")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only historical one
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == historical_fermentation.id
        assert data["items"][0]["data_source"] == "HISTORICAL"
    
    async def test_list_enforces_multi_tenant_isolation(
        self, test_client, historical_fermentation, other_winery_fermentation
    ):
        """Only fermentations from user's winery are returned."""
        response = await test_client.get("/api/fermentation/historical")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only see historical_fermentation (same winery)
        assert data["total"] == 1
        assert data["items"][0]["id"] == historical_fermentation.id
        
        # Should NOT see other_winery_fermentation
        fermentation_ids = [f["id"] for f in data["items"]]
        assert other_winery_fermentation.id not in fermentation_ids
    
    async def test_list_filters_by_date_range(
        self, test_client, multiple_historical_fermentations
    ):
        """Date range filters work correctly."""
        # Filter: Sept 2-4 (should match fermentations 1, 2, 3 - indices 1, 2, 3)
        response = await test_client.get(
            "/api/fermentation/historical",
            params={
                "start_date_from": "2023-09-02",
                "start_date_to": "2023-09-04"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        
        # Verify dates are within range
        for item in data["items"]:
            start_date = datetime.fromisoformat(item["start_date"].replace("Z", "")).date()
            assert date(2023, 9, 2) <= start_date <= date(2023, 9, 4)
    
    async def test_list_filters_by_status(
        self, test_client, multiple_historical_fermentations
    ):
        """Status filter works correctly."""
        # Filter by COMPLETED (4 out of 5)
        response = await test_client.get(
            "/api/fermentation/historical",
            params={"status": "COMPLETED"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        
        # All returned items should be COMPLETED
        for item in data["items"]:
            assert item["status"] == "COMPLETED"
    
    async def test_list_pagination_works(
        self, test_client, multiple_historical_fermentations
    ):
        """Pagination parameters limit and offset work correctly."""
        # Get first 2 items
        response1 = await test_client.get(
            "/api/fermentation/historical",
            params={"limit": 2, "offset": 0}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 2
        assert data1["limit"] == 2
        assert data1["offset"] == 0
        
        # Get next 2 items
        response2 = await test_client.get(
            "/api/fermentation/historical",
            params={"limit": 2, "offset": 2}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2
        assert data2["limit"] == 2
        assert data2["offset"] == 2
        
        # Items should be different
        ids1 = {item["id"] for item in data1["items"]}
        ids2 = {item["id"] for item in data2["items"]}
        assert ids1.isdisjoint(ids2)  # No overlap


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetHistoricalFermentationById:
    """Test GET /api/fermentation/historical/{id} - get single fermentation."""
    
    async def test_get_by_id_returns_fermentation(
        self, test_client, historical_fermentation
    ):
        """Successfully retrieves fermentation by ID."""
        response = await test_client.get(
            f"/api/fermentation/historical/{historical_fermentation.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == historical_fermentation.id
        assert data["data_source"] == "HISTORICAL"
        assert data["vessel_code"] == "HIST-001"
        assert data["status"] == "COMPLETED"
    
    async def test_get_by_id_returns_404_when_not_found(self, test_client):
        """Returns 404 for non-existent fermentation."""
        response = await test_client.get("/api/fermentation/historical/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_get_by_id_enforces_multi_tenant_isolation(
        self, test_client, other_winery_fermentation
    ):
        """Returns 404 when accessing fermentation from different winery."""
        response = await test_client.get(
            f"/api/fermentation/historical/{other_winery_fermentation.id}"
        )
        
        assert response.status_code == 404
        # Repository enforces winery_id, so it's treated as not found


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetFermentationSamples:
    """Test GET /api/fermentation/historical/{id}/samples - get fermentation samples."""
    
    async def test_get_samples_returns_historical_samples_only(
        self, test_client, historical_fermentation, historical_samples,
        test_models_with_samples, db_session, test_user
    ):
        """Only samples with data_source='HISTORICAL' are returned."""
        # Add a manual sample (different data_source)
        DensitySample = test_models_with_samples['DensitySample']
        manual_sample = DensitySample(
            fermentation_id=historical_fermentation.id,
            recorded_by_user_id=test_user.id,
            recorded_at=datetime(2023, 9, 10, 12, 0, 0),
            value=1.02,
            data_source="MANUAL"  # Different source
        )
        db_session.add(manual_sample)
        await db_session.flush()
        
        # Get samples
        response = await test_client.get(
            f"/api/fermentation/historical/{historical_fermentation.id}/samples"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Response is a list directly, not a dict with "samples" key
        assert isinstance(data, list)
        assert len(data) == 4  # Should only return HISTORICAL samples (4), not the manual one
        for sample in data:
            assert sample["data_source"] == "HISTORICAL"
    
    async def test_get_samples_returns_404_when_fermentation_not_found(
        self, test_client
    ):
        """Returns 404 when fermentation doesn't exist."""
        response = await test_client.get(
            "/api/fermentation/historical/99999/samples"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestExtractPatterns:
    """Test GET /api/fermentation/historical/patterns/extract - aggregate historical data."""
    
    async def test_extract_patterns_aggregates_real_data(
        self, test_client, multiple_historical_fermentations,
        test_models_with_samples, db_session, test_user
    ):
        """Calculates metrics from real fermentation data."""
        # Add samples to fermentations for pattern extraction
        DensitySample = test_models_with_samples['DensitySample']
        SugarSample = test_models_with_samples['SugarSample']
        
        from datetime import timedelta
        
        for i, ferm in enumerate(multiple_historical_fermentations):
            # Initial readings
            db_session.add(DensitySample(
                fermentation_id=ferm.id,
                recorded_by_user_id=test_user.id,
                recorded_at=ferm.start_date,
                value=ferm.initial_density,
                data_source="HISTORICAL"
            ))
            db_session.add(SugarSample(
                fermentation_id=ferm.id,
                recorded_by_user_id=test_user.id,
                recorded_at=ferm.start_date,
                value=ferm.initial_sugar_brix,
                data_source="HISTORICAL"
            ))
            
            # Final readings (after 11+i days)
            final_date = ferm.start_date + timedelta(days=11 + i)
            db_session.add(DensitySample(
                fermentation_id=ferm.id,
                recorded_by_user_id=test_user.id,
                recorded_at=final_date,
                value=0.993,
                data_source="HISTORICAL"
            ))
            db_session.add(SugarSample(
                fermentation_id=ferm.id,
                recorded_by_user_id=test_user.id,
                recorded_at=final_date,
                value=0.5,
                data_source="HISTORICAL"
            ))
        
        await db_session.flush()
        
        # Extract patterns
        response = await test_client.get(
            "/api/fermentation/historical/patterns/extract"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify aggregated metrics
        assert data["total_fermentations"] == 5
        assert data["completed_count"] == 4
        assert data["stuck_count"] == 1
        assert data["success_rate"] == 0.8  # 4/5
        assert data["avg_initial_density"] > 0
        assert data["avg_final_density"] > 0
        assert data["avg_duration_days"] > 0
    
    async def test_extract_patterns_filters_by_date_range(
        self, test_client, multiple_historical_fermentations
    ):
        """Date range filter limits aggregation."""
        # Filter to first 3 fermentations (Sept 1-3)
        response = await test_client.get(
            "/api/fermentation/historical/patterns/extract",
            params={
                "start_date": "2023-09-01",
                "end_date": "2023-09-03"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_fermentations"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
class TestDashboardStatistics:
    """Test GET /api/fermentation/historical/statistics/dashboard - dashboard metrics."""
    
    async def test_dashboard_returns_statistics(
        self, test_client, multiple_historical_fermentations
    ):
        """Returns dashboard statistics from real data."""
        response = await test_client.get(
            "/api/fermentation/historical/statistics/dashboard"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Basic structure check (exact values depend on extract_patterns implementation)
        assert "total_fermentations" in data
        assert "success_rate" in data
        assert data["total_fermentations"] == 5
