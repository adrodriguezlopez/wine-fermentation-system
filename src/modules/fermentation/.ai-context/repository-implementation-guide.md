# Repository Implementation Guide - Wine Fermentation System

This guide provides comprehensive instructions for implementing repository components within the Wine Fermentation System following Domain-Driven Design (DDD) principles and Test-Driven Development (TDD) practices.

## Table of Contents

1. [Repository Interfaces Overview](#1-repository-interfaces-overview)
2. [TDD Implementation Workflow](#2-tdd-implementation-workflow)
3. [Error Handling Strategy](#3-error-handling-strategy)
4. [Transaction Management](#4-transaction-management)
5. [Testing Patterns](#5-testing-patterns)
6. [Performance Considerations](#6-performance-considerations)

## 1. Repository Interfaces Overview

### Identified Repository Interfaces

The system follows a Domain-Driven Design approach where repository interfaces are defined in the domain layer:

- **IFermentationRepository**: Manages the lifecycle of fermentations and their related samples.
- **ISampleRepository**: Specialized in managing and querying samples (temperature, sugar, etc.).
- **IValueValidationService**: Validates individual data points without external dependencies.
- **IBusinessRuleValidationService**: Validates complex business rules.
- **IChronologyValidationService**: Specialized in validating sample chronology.

### Contract Patterns

Repository interfaces follow a consistent pattern:

```python
class IRepositoryName(ABC):
    @abstractmethod
    async def method_name(self, param: Type) -> ReturnType:
        """
        Clear method description.

        Args:
            param: Description

        Returns:
            ReturnType: Description

        Raises:
            SpecificError: When specific conditions occur
        """
        pass
```

### Dependency Injection Patterns

```python
# In services
class ValidationService:
    def __init__(self, sample_repository: ISampleRepository):
        self.sample_repository = sample_repository

# In Factory or IoC container
def create_validation_service(container):
    return ValidationService(container.get(ISampleRepository))
```

## 2. TDD Implementation Workflow

### Step-by-Step Implementation for `SampleRepository`

#### 1. Create Class and Test Skeletons

```python
# sample_repository.py
class SampleRepository(ISampleRepository):
    def __init__(self, session_factory):
        self.session_factory = session_factory
```

```python
# test_sample_repository.py
@pytest.fixture
def sample_repository():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    # Set up Base.metadata.create_all(engine) to create schema
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return SampleRepository(session_factory)
```

#### 2. Implement Simple Method and Its Test

```python
# In test_sample_repository.py
@pytest.mark.asyncio
async def test_create_sample(sample_repository):
    # GIVEN
    sample = SugarSample(
        fermentation_id=1,
        value=12.5,
        recorded_at=datetime.now(),
        sample_type=SampleType.SUGAR
    )
    
    # WHEN
    sample_id = await sample_repository.create(sample)
    
    # THEN
    assert sample_id > 0
    saved_sample = await sample_repository.get_by_id(sample_id)
    assert saved_sample.value == 12.5
```

```python
# In sample_repository.py
async def create(self, sample: BaseSample) -> int:
    async with self.session_factory() as session:
        try:
            db_sample = SampleModel(
                fermentation_id=sample.fermentation_id,
                value=sample.value,
                recorded_at=sample.recorded_at,
                type=sample.sample_type.value
            )
            session.add(db_sample)
            await session.commit()
            return db_sample.id
        except SQLAlchemyError as e:
            await session.rollback()
            # Convert to domain errors
            if "UNIQUE constraint" in str(e):
                raise IntegrityError("Sample already exists for this timestamp")
            raise RepositoryError(f"Failed to create sample: {str(e)}")
```

#### 3. Implement More Complex Method and Its Test

```python
@pytest.mark.asyncio
async def test_get_samples_by_fermentation_id_with_type_filter(sample_repository):
    # GIVEN
    # Setup data...
    
    # WHEN
    results = await sample_repository.get_samples_by_fermentation_id(
        fermentation_id=1,
        sample_type=SampleType.TEMPERATURE,
        start_date=yesterday,
        end_date=tomorrow
    )
    
    # THEN
    assert len(results) == 2
    assert all(s.sample_type == SampleType.TEMPERATURE for s in results)
    # Verify chronological order
    assert results[0].recorded_at < results[1].recorded_at
```

### Test Organization

```
tests/
├── unit/               # Tests for pure logic, no I/O
│   ├── domain/         # Tests for domain entities and logic
│   └── validation/     # Tests for validation services
├── integration/        # Tests requiring I/O (DB)
│   └── repository/     # Tests for repository implementations
└── fixtures/           # Shared test data
    └── samples.py      # Sample factory for tests
```

## 3. Error Handling Strategy

### Exception Hierarchy

```python
# In domain/exceptions.py
class DomainError(Exception):
    """Base for domain errors"""
    pass

class ValidationError(DomainError):
    """Error in business rule validation"""
    pass

class EntityNotFoundError(DomainError):
    """Entity not found when expected"""
    pass

# In infrastructure/exceptions.py
class InfrastructureError(Exception):
    """Base for infrastructure errors"""
    pass

class RepositoryError(InfrastructureError):
    """General error in repository operations"""
    pass

class DatabaseConnectionError(RepositoryError):
    """Database connection error"""
    pass
```

### Domain-Specific Error Handling

```python
class FermentationConstraintViolation(ValidationError):
    """Violation of specific fermentation process constraints"""
    
    def __init__(self, message, constraint_type, value=None):
        self.constraint_type = constraint_type  # e.g.: "temperature_range"
        self.value = value
        super().__init__(f"{constraint_type}: {message}")
```

### Error Transformation Example

```python
async def get_by_id(self, sample_id: int) -> BaseSample:
    async with self.session_factory() as session:
        try:
            result = await session.get(SampleModel, sample_id)
            if result is None:
                raise EntityNotFoundError(f"Sample with ID {sample_id} not found")
            return self._map_to_domain(result)
        except SQLAlchemyError as e:
            # Transform infrastructure errors but preserve original message
            raise RepositoryError(f"Database error: {str(e)}") from e
```

## 4. Transaction Management

### Recommended Boundaries

```python
# In a service coordinating multiple operations
async def update_fermentation_status(self, fermentation_id: int, new_status: str):
    async with self.unit_of_work.begin():
        # All of this executes in one transaction
        fermentation = await self.fermentation_repository.get_by_id(fermentation_id)
        
        # Domain validations
        if not self.status_validator.can_transition_to(fermentation.status, new_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition from {fermentation.status} to {new_status}"
            )
            
        # Multiple updates
        await self.fermentation_repository.update_status(fermentation_id, new_status)
        await self.audit_repository.log_status_change(
            fermentation_id, fermentation.status, new_status
        )
```

### Unit of Work Pattern

```python
# In infrastructure/unit_of_work.py
class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        
    @asynccontextmanager
    async def begin(self):
        async with self.session_factory() as session:
            async with session.begin():
                yield
```

### Batch Operation Transactions

```python
async def batch_add_samples(self, samples: List[BaseSample]) -> List[int]:
    """Add multiple samples in a single transaction"""
    async with self.session_factory() as session:
        async with session.begin():
            try:
                sample_ids = []
                for sample in samples:
                    db_sample = self._map_to_db(sample)
                    session.add(db_sample)
                    sample_ids.append(db_sample.id)
                return sample_ids
            except SQLAlchemyError as e:
                # No explicit rollback needed when using `begin()`
                self._handle_db_error(e)
```

## 5. Testing Patterns

### Mocks vs. Real Database

```python
# Test with mock to verify service behavior
@pytest.mark.asyncio
async def test_validation_service_calls_repository_correctly(mocker):
    # GIVEN
    mock_repo = Mock(spec=ISampleRepository)
    mock_repo.get_latest_sample_by_type = AsyncMock(return_value=None)
    service = ValidationService(sample_repository=mock_repo)
    
    # WHEN
    await service.validate_sample_chronology(1, sample)
    
    # THEN
    mock_repo.get_latest_sample_by_type.assert_called_once_with(
        fermentation_id=1, sample_type=sample.sample_type
    )
```

```python
# Test with real DB to verify complete implementation
@pytest.fixture
async def db_session():
    # Create in-memory DB and schema
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create and return session factory
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    try:
        yield async_session
    finally:
        await engine.dispose()
```

### Creating Test Data for Fermentation

```python
# In fixtures/sample_factory.py
class SampleFactory:
    @staticmethod
    def create_sugar_sample(fermentation_id=1, value=15.0, days_ago=0):
        """Create a sugar sample for testing"""
        return SugarSample(
            fermentation_id=fermentation_id,
            value=value,
            recorded_at=datetime.now() - timedelta(days=days_ago),
            sample_type=SampleType.SUGAR,
            unit="brix"
        )
    
    @staticmethod
    def create_temperature_sample(fermentation_id=1, value=22.5, days_ago=0):
        """Create a temperature sample for testing"""
        return TemperatureSample(
            fermentation_id=fermentation_id,
            value=value,
            recorded_at=datetime.now() - timedelta(days=days_ago),
            sample_type=SampleType.TEMPERATURE,
            unit="celsius"
        )
```

### Testing Scientific Validations

```python
@pytest.mark.parametrize("current_value,previous_value,days_diff,expected_valid", [
    (14.0, 15.0, 1, True),    # Normal sugar decrease
    (15.0, 14.0, 1, False),   # Sugar should not increase
    (10.0, 15.0, 1, False),   # Decrease too fast
    (14.9, 15.0, 1, False),   # Decrease too slow
])
@pytest.mark.asyncio
async def test_sugar_trend_validation(
    validation_service, 
    current_value, 
    previous_value,
    days_diff,
    expected_valid
):
    # GIVEN
    current_date = datetime.now()
    previous_date = current_date - timedelta(days=days_diff)
    current_sample = SampleFactory.create_sugar_sample(value=current_value)
    previous_sample = SampleFactory.create_sugar_sample(
        value=previous_value, 
        recorded_at=previous_date
    )
    
    # Configure repo mock to return previous sample
    validation_service.sample_repository.get_latest_sample_by_type.return_value = previous_sample
    
    # WHEN
    result = await validation_service.validate_sugar_trend(
        fermentation_id=1, sample=current_sample
    )
    
    # THEN
    assert result.is_valid == expected_valid
```

## 6. Performance Considerations

### Efficient Queries for Time-Series Data

```python
# Optimized for frequent time range queries
async def get_samples_in_range(
    self, 
    fermentation_id: int, 
    start_time: datetime, 
    end_time: datetime,
    sample_type: Optional[SampleType] = None
) -> List[BaseSample]:
    """Get samples within a specific time range"""
    
    async with self.session_factory() as session:
        query = select(SampleModel).where(
            SampleModel.fermentation_id == fermentation_id,
            SampleModel.recorded_at >= start_time,
            SampleModel.recorded_at <= end_time,
            SampleModel.is_deleted == False
        ).order_by(SampleModel.recorded_at)
        
        # Conditional filter by type
        if sample_type:
            query = query.where(SampleModel.type == sample_type.value)
        
        result = await session.execute(query)
        samples = result.scalars().all()
        
        return [self._map_to_domain(sample) for sample in samples]
```

### Indexing Recommendations

```python
# In SQLAlchemy model
class SampleModel(Base):
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True)
    fermentation_id = Column(Integer, ForeignKey("fermentations.id"), nullable=False)
    value = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False)
    
    # Indexes for common queries
    __table_args__ = (
        # For queries by fermentation and type
        Index('idx_samples_fermentation_type', fermentation_id, type),
        
        # For time range queries (crucial for time-series)
        Index('idx_samples_fermentation_time', fermentation_id, recorded_at),
        
        # To prevent duplicates in same fermentation, type and timestamp
        UniqueConstraint(
            'fermentation_id', 'type', 'recorded_at', 
            name='uq_sample_fermentation_type_time'
        ),
    )
```

### Batch Operations for Multiple Samples

```python
# Optimized for bulk insert operations
async def create_many(self, samples: List[BaseSample]) -> List[int]:
    """Create multiple samples in a single transaction"""
    
    if not samples:
        return []
        
    async with self.session_factory() as session:
        async with session.begin():
            try:
                # Convert to DB models
                db_samples = [
                    SampleModel(
                        fermentation_id=s.fermentation_id,
                        value=s.value,
                        type=s.sample_type.value,
                        recorded_at=s.recorded_at,
                        unit=s.unit
                    ) for s in samples
                ]
                
                # Add all at once
                session.add_all(db_samples)
                
                # Flush to generate IDs without commit
                await session.flush()
                
                # Collect generated IDs
                return [s.id for s in db_samples]
                
            except SQLAlchemyError as e:
                # Handle specific errors
                if "UNIQUE constraint" in str(e):
                    # Find which sample is duplicated
                    for sample in samples:
                        # Individual verification to identify culprit
                        duplicate = await self._find_duplicate(session, sample)
                        if duplicate:
                            raise IntegrityError(
                                f"Duplicate sample for fermentation {sample.fermentation_id} "
                                f"at {sample.recorded_at} with type {sample.sample_type}"
                            )
                
                # Generic error if problem can't be identified
                raise RepositoryError(f"Failed to create samples: {str(e)}")
```

# ... (see full guide for complete implementation examples)
