"""
Tests for EntityFactory

Validates the behavior and API of the entity factory.
Follows TDD principles from ADR-012.
"""

import pytest
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock

from src.shared.testing.unit.builders.entity_factory import (
    EntityFactory,
    EntityDefaults,
    create_mock_entity,
    create_mock_entities,
)


# Mock entity classes for testing
class Fermentation:
    """Mock Fermentation entity"""
    pass


class FermentationNote:
    """Mock FermentationNote entity"""
    pass


class Sample:
    """Mock Sample entity"""
    pass


class TestEntityDefaults:
    """Test suite for EntityDefaults registry"""
    
    def test_get_common_defaults(self):
        """Should include common defaults for all entities"""
        # Act
        defaults = EntityDefaults.get_defaults('UnknownEntity')
        
        # Assert
        assert 'id' in defaults
        assert 'created_at' in defaults
        assert 'updated_at' in defaults
        assert 'created_by' in defaults
        assert 'updated_by' in defaults
    
    def test_get_entity_specific_defaults(self):
        """Should include entity-specific defaults"""
        # Act
        defaults = EntityDefaults.get_defaults('Fermentation')
        
        # Assert
        assert 'name' in defaults
        assert 'vintage_year' in defaults
        assert 'lot_number' in defaults
        assert 'is_active' in defaults
    
    def test_defaults_are_callable(self):
        """Should support callable defaults for dynamic values"""
        # Act
        defaults = EntityDefaults.get_defaults('Fermentation')
        
        # Assert - Callables should be present
        assert callable(defaults['id'])
        assert callable(defaults['created_at'])
        assert callable(defaults['name'])
        
        # Should generate different values
        id1 = defaults['id']()
        id2 = defaults['id']()
        assert id1 != id2
    
    def test_register_custom_defaults(self):
        """Should allow registering custom entity defaults"""
        # Arrange
        custom_defaults = {
            'custom_field': lambda: 'custom_value',
            'another_field': 42,
        }
        
        # Act
        EntityDefaults.register('CustomEntity', custom_defaults)
        defaults = EntityDefaults.get_defaults('CustomEntity')
        
        # Assert
        assert 'custom_field' in defaults
        assert 'another_field' in defaults
        assert defaults['custom_field']() == 'custom_value'
        assert defaults['another_field'] == 42


class TestEntityFactory:
    """Test suite for EntityFactory"""
    
    def test_create_simple_entity(self):
        """Should create entity with default values"""
        # Act
        entity = EntityFactory.create(Fermentation)
        
        # Assert
        assert entity is not None
        assert hasattr(entity, 'id')
        assert hasattr(entity, 'created_at')
        assert isinstance(entity.id, UUID)
        assert isinstance(entity.created_at, datetime)
    
    def test_create_with_overrides(self):
        """Should override default values"""
        # Arrange
        custom_id = UUID('12345678-1234-1234-1234-123456789012')
        custom_name = 'Custom Fermentation'
        
        # Act
        entity = EntityFactory.create(
            Fermentation,
            id=custom_id,
            name=custom_name
        )
        
        # Assert
        assert entity.id == custom_id
        assert entity.name == custom_name
    
    def test_create_fermentation_entity(self):
        """Should create Fermentation with correct defaults"""
        # Act
        entity = EntityFactory.create(Fermentation)
        
        # Assert
        assert hasattr(entity, 'name')
        assert hasattr(entity, 'vintage_year')
        assert hasattr(entity, 'lot_number')
        assert hasattr(entity, 'is_active')
        assert entity.vintage_year == 2024
        assert entity.is_active is True
    
    def test_create_note_entity(self):
        """Should create FermentationNote with correct defaults"""
        # Act
        entity = EntityFactory.create(FermentationNote)
        
        # Assert
        assert hasattr(entity, 'note')
        assert hasattr(entity, 'note_type')
        assert hasattr(entity, 'recorded_at')
        assert entity.note_type == 'OBSERVATION'
        assert isinstance(entity.recorded_at, datetime)
    
    def test_create_sample_entity(self):
        """Should create Sample with correct defaults"""
        # Act
        entity = EntityFactory.create(Sample)
        
        # Assert
        assert hasattr(entity, 'value')
        assert hasattr(entity, 'recorded_at')
        assert isinstance(entity.value, Decimal)
        assert isinstance(entity.recorded_at, datetime)
    
    def test_entity_has_spec(self):
        """Should create entity as MagicMock with spec"""
        # Act
        entity = EntityFactory.create(Fermentation)
        
        # Assert
        assert isinstance(entity, MagicMock)
    
    def test_unique_ids_per_entity(self):
        """Should generate unique IDs for each entity"""
        # Act
        entity1 = EntityFactory.create(Fermentation)
        entity2 = EntityFactory.create(Fermentation)
        
        # Assert
        assert entity1.id != entity2.id
    
    def test_unique_names_per_entity(self):
        """Should generate unique names for each entity"""
        # Act
        entity1 = EntityFactory.create(Fermentation)
        entity2 = EntityFactory.create(Fermentation)
        
        # Assert
        assert entity1.name != entity2.name
        assert 'Test Fermentation' in entity1.name
    
    def test_create_batch(self):
        """Should create multiple entities"""
        # Act
        entities = EntityFactory.create_batch(Fermentation, count=5)
        
        # Assert
        assert len(entities) == 5
        assert all(isinstance(e, MagicMock) for e in entities)
        assert all(hasattr(e, 'id') for e in entities)
        
        # All should have unique IDs
        ids = [e.id for e in entities]
        assert len(ids) == len(set(ids))
    
    def test_create_batch_with_overrides(self):
        """Should create multiple entities with same overrides"""
        # Arrange
        vintage_year = 2023
        
        # Act
        entities = EntityFactory.create_batch(
            Fermentation,
            count=3,
            vintage_year=vintage_year
        )
        
        # Assert
        assert len(entities) == 3
        assert all(e.vintage_year == vintage_year for e in entities)
    
    def test_create_sequence(self):
        """Should create entities with sequential field values"""
        # Act
        entities = EntityFactory.create_sequence(
            Fermentation,
            count=5,
            sequence_field='vintage_year',
            start=2020
        )
        
        # Assert
        assert len(entities) == 5
        assert entities[0].vintage_year == 2020
        assert entities[1].vintage_year == 2021
        assert entities[2].vintage_year == 2022
        assert entities[3].vintage_year == 2023
        assert entities[4].vintage_year == 2024
    
    def test_create_sequence_with_common_overrides(self):
        """Should create sequence with common overrides"""
        # Act
        entities = EntityFactory.create_sequence(
            Fermentation,
            count=3,
            sequence_field='vintage_year',
            start=2020,
            is_active=False
        )
        
        # Assert
        assert len(entities) == 3
        assert all(not e.is_active for e in entities)
        assert entities[0].vintage_year == 2020
        assert entities[1].vintage_year == 2021
        assert entities[2].vintage_year == 2022


class TestConvenienceFunctions:
    """Test convenience factory functions"""
    
    def test_create_mock_entity(self):
        """Should create single entity via convenience function"""
        # Act
        entity = create_mock_entity(Fermentation)
        
        # Assert
        assert entity is not None
        assert hasattr(entity, 'id')
        assert hasattr(entity, 'vintage_year')
    
    def test_create_mock_entity_with_overrides(self):
        """Should create entity with overrides via convenience function"""
        # Act
        entity = create_mock_entity(Fermentation, vintage_year=2023)
        
        # Assert
        assert entity.vintage_year == 2023
    
    def test_create_mock_entities(self):
        """Should create multiple entities via convenience function"""
        # Act
        entities = create_mock_entities(Fermentation, 5)
        
        # Assert
        assert len(entities) == 5
        assert all(hasattr(e, 'id') for e in entities)
    
    def test_create_mock_entities_with_overrides(self):
        """Should create multiple entities with overrides"""
        # Act
        entities = create_mock_entities(
            Fermentation,
            3,
            vintage_year=2023,
            is_active=False
        )
        
        # Assert
        assert len(entities) == 3
        assert all(e.vintage_year == 2023 for e in entities)
        assert all(not e.is_active for e in entities)


class TestRealWorldScenarios:
    """Test realistic usage scenarios"""
    
    def test_repository_test_scenario(self):
        """Should support typical repository test setup"""
        # Arrange - Create test entities
        fermentation1 = create_mock_entity(
            Fermentation,
            id=UUID('12345678-1234-1234-1234-123456789012'),
            name='Fermentation 1'
        )
        fermentation2 = create_mock_entity(
            Fermentation,
            id=UUID('87654321-4321-4321-4321-210987654321'),
            name='Fermentation 2'
        )
        
        # Act - Use in test
        fermentations = [fermentation1, fermentation2]
        
        # Assert - Validate setup
        assert len(fermentations) == 2
        assert fermentations[0].id != fermentations[1].id
        assert fermentations[0].name != fermentations[1].name
    
    def test_service_test_scenario(self):
        """Should support typical service test setup"""
        # Arrange - Create related entities
        fermentation = create_mock_entity(Fermentation, vintage_year=2023)
        notes = create_mock_entities(
            FermentationNote,
            3,
            note_type='OBSERVATION'
        )
        
        # Act - Simulate test
        fermentation.notes = notes
        
        # Assert
        assert len(fermentation.notes) == 3
        assert all(n.note_type == 'OBSERVATION' for n in fermentation.notes)
    
    def test_batch_creation_for_list_tests(self):
        """Should easily create batches for list/pagination tests"""
        # Arrange & Act
        fermentations = create_mock_entities(Fermentation, 10)
        
        # Simulate pagination
        page1 = fermentations[:5]
        page2 = fermentations[5:]
        
        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        assert len(set(f.id for f in fermentations)) == 10
