# ADR-033: Code Coverage Improvement Strategy

**Status**: Draft  
**Date**: 2026-01-13  
**Author**: Development Team  
**Related**: ADR-028 (Testing Strategy), ADR-032 (Historical Data API)

## Context

Following the successful implementation of the Historical Data API (ADR-032) and achieving **100% test pass rate (1,033/1,033 tests)**, a code coverage analysis revealed significant gaps in test coverage across multiple components of the fermentation module.

**Key Finding**: The project demonstrates strong TDD discipline with 1,033 tests, but coverage is **unevenly distributed**. High coverage (90-100%) in domain/DTOs/entities, but low coverage (0-30%) in API/Service/Repository layers.

### Current Test Distribution

**Total Tests: 1,033** (all passing - 100% pass rate)
- **Fermentation**: 506 tests (344 unit + 75 integration + 87 API)
- **Fruit Origin**: 190 tests (113 unit + 43 integration + 34 API)  
- **Winery**: 79 tests (44 unit + 35 integration)
- **Shared Auth**: 183 tests (159 unit + 24 integration)
- **Shared Testing**: 52 unit tests
- **Shared Error Handling**: 23 unit tests

### Current Coverage Status

**Overall Module Coverage**: 56%

#### Critical Coverage Gaps by Layer

**API Layer (0% Coverage - CRITICAL)**:
- `sample_router.py`: 0% (72 statements) - Public API endpoints without tests
- `main.py`: 0% (34 statements) - Application entry point
- `dependencies.py`: 0% (48 statements) - Dependency injection configuration
- `error_handlers.py`: 0% (54 statements) - Global error handling

**Repository Layer (12-18% Coverage - HIGH)**:
- `sample_repository.py`: 12.2% (166/189 missing)
- `fermentation_repository.py`: 17% (88/106 missing)
- `lot_source_repository.py`: 18.3% (58/71 missing)

**Service Layer (14-30% Coverage - MEDIUM)**:
- `historical_data_service.py`: 14.5% (94/110 missing)
- `fermentation_service.py`: 16% (110/131 missing)
- `sample_service.py`: 23% (77/100 missing)
- `etl_service.py`: 29.9% (89/127 missing)
- `etl_validator.py`: 25.3% (168/225 missing)

### Business Impact

**Security Risks**:
- Untested API endpoints may have security vulnerabilities
- Multi-tenant isolation not verified in integration tests
- Error handlers not tested for proper error exposure

**Quality Risks**:
- Untested repository operations may corrupt data
- Unvalidated business logic may produce incorrect results
- ETL processes without coverage may import invalid data

**Maintenance Risks**:
- Refactoring becomes dangerous without test coverage
- Bugs harder to identify and prevent
- Regression issues likely during changes

## Decision

We will implement a phased approach to improve code coverage, prioritizing by business risk and impact. The strategy focuses on achieving **minimum 80% coverage** for critical components while maintaining 100% test pass rate.

### Coverage Targets by Component

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| API Layer | 0-9% | 85% | P0 (Critical) |
| Repository Layer | 12-18% | 80% | P1 (High) |
| Service Layer | 14-30% | 80% | P1 (High) |
| Domain/DTOs | 80-100% | 95% | P2 (Medium) |
| Validators | 27-95% | 90% | P2 (Medium) |

### Implementation Phases

#### Phase 1: API Layer Security (Priority P0)
**Duration**: 1-2 days  
**Target Coverage**: 85%

**1.1 Sample Router Tests** (`sample_router.py` 0% → 85%)
- Integration tests for all 8 endpoints
- Security tests (multi-tenant isolation, authorization)
- Request validation tests (malformed requests, edge cases)
- Error handling tests (404, 403, 400, 500)

**1.2 Error Handlers** (`error_handlers.py` 0% → 90%)
- Unit tests for each error handler
- Tests for domain error → HTTP error conversion
- Tests for error logging and structure
- Tests for error message sanitization (security)

**1.3 Dependency Injection** (`dependencies.py` 0% → 85%)
- Unit tests for service factory functions
- Tests for session management
- Tests for dependency override in testing
- Tests for configuration injection

**Deliverables**:
- `tests/integration/api/test_sample_router.py` (~200 lines)
- `tests/unit/api/test_error_handlers.py` (~150 lines)
- `tests/unit/api/test_dependencies.py` (~120 lines)
- API layer coverage report showing 85%+

#### Phase 2: Repository Layer Integrity (Priority P1)
**Duration**: 2-3 days  
**Target Coverage**: 80%

**2.1 Sample Repository** (`sample_repository.py` 12.2% → 80%)
- Integration tests for CRUD operations
- Tests for bulk operations (bulk_upsert_samples)
- Tests for complex queries (time range, fermentation filtering)
- Tests for data source filtering
- Tests for multi-tenant isolation

**2.2 Fermentation Repository** (`fermentation_repository.py` 17% → 80%)
- Tests for data_source filtering (SYSTEM, HISTORICAL, MIGRATED)
- Tests for status queries
- Tests for soft delete operations
- Tests for multi-tenant scoping

**2.3 Lot Source Repository** (`lot_source_repository.py` 18.3% → 80%)
- Tests for fermentation-lot relationships
- Tests for mass calculations
- Tests for multi-tenant isolation
- Tests for cascade deletions

**Deliverables**:
- `tests/integration/repository/test_sample_repository_integration.py` (expand from 1 to ~300 lines)
- `tests/integration/repository/test_fermentation_repository_integration.py` (expand ~150 lines)
- `tests/integration/repository/test_lot_source_repository_integration.py` (expand ~100 lines)
- Repository layer coverage report showing 80%+

#### Phase 3: Service Layer Business Logic (Priority P1)
**Duration**: 2-3 days  
**Target Coverage**: 80%

**3.1 Historical Data Service** (`historical_data_service.py` 14.5% → 85%)
- Unit tests for pattern extraction logic
- Tests for aggregation calculations
- Tests for date range filtering
- Tests for fruit origin filtering
- Tests for dashboard statistics

**3.2 Fermentation Service** (`fermentation_service.py` 16% → 80%)
- Unit tests for create with blend logic
- Tests for status transition validation
- Tests for completion criteria validation
- Tests for soft delete cascading

**3.3 Sample Service** (`sample_service.py` 23% → 80%)
- Unit tests for sample addition validation
- Tests for chronology validation
- Tests for value validation
- Tests for fermentation status checks

**Deliverables**:
- `tests/unit/service/test_historical_data_service.py` (expand ~200 lines)
- `tests/unit/service/test_fermentation_service.py` (expand ~250 lines)
- `tests/unit/service/test_sample_service.py` (expand ~200 lines)
- Service layer coverage report showing 80%+

#### Phase 4: ETL and Validation (Priority P2)
**Duration**: 2-3 days  
**Target Coverage**: 80%

**4.1 ETL Validator** (`etl_validator.py` 25.3% → 85%)
- Unit tests for pre-validation rules
- Tests for row-level validation
- Tests for post-validation (chronology, trends)
- Tests for error reporting

**4.2 ETL Service** (`etl_service.py` 29.9% → 80%)
- Unit tests for import flow
- Tests for rollback on errors
- Tests for progress tracking
- Tests for cancellation handling

**Deliverables**:
- `tests/unit/etl/test_etl_validator.py` (expand ~200 lines)
- `tests/unit/etl/test_etl_service.py` (expand ~150 lines)
- ETL coverage report showing 80%+

### Coverage Measurement and Reporting

**Tools**:
- pytest-cov for coverage measurement
- HTML reports for detailed analysis
- Terminal reports for CI/CD integration

**CI/CD Integration**:
```bash
# Minimum coverage threshold enforcement
pytest --cov=src --cov-fail-under=80 tests/

# Generate reports
pytest --cov=src --cov-report=html --cov-report=term-missing tests/
```

**Coverage Targets**:
- **Overall Module**: 80% minimum
- **API Layer**: 85% minimum (security critical)
- **Repository Layer**: 80% minimum (data integrity)
- **Service Layer**: 80% minimum (business logic)
- **Domain/DTOs**: 95% minimum (core entities)

### Maintenance Strategy

**Prevent Coverage Regression**:
1. Add coverage checks to CI/CD pipeline
2. Require 80% coverage on new code in PRs
3. Monthly coverage reports and review
4. Automated coverage badges in README

**Code Review Guidelines**:
- All new APIs must have integration tests
- All new services must have unit tests
- Complex logic requires test coverage before merge
- Coverage drops require justification and plan

## Consequences

### Positive

**Security**:
- ✅ API endpoints validated against security vulnerabilities
- ✅ Multi-tenant isolation verified in all layers
- ✅ Error handling prevents information leakage

**Quality**:
- ✅ Repository operations validated for data integrity
- ✅ Business logic verified through unit tests
- ✅ ETL processes validated for data correctness
- ✅ Refactoring becomes safer with comprehensive tests

**Confidence**:
- ✅ Deployments with higher confidence
- ✅ Faster bug detection through automated tests
- ✅ Documentation through test examples

**Metrics**:
- ✅ Measurable quality improvements
- ✅ Trend analysis for code health
- ✅ Objective code review criteria

### Negative

**Time Investment**:
- ⚠️ Estimated 8-11 days of development time
- ⚠️ Slows feature development temporarily
- ⚠️ Requires learning curve for complex testing scenarios

**Maintenance Overhead**:
- ⚠️ More tests to maintain and update
- ⚠️ Tests may become brittle if not well-designed
- ⚠️ False positives may slow down development

**Technical Debt**:
- ⚠️ Existing code may need refactoring for testability
- ⚠️ Dependencies may need mocking infrastructure
- ⚠️ Complex scenarios may be hard to test

### Mitigation Strategies

**Manage Time Investment**:
- Execute phases in parallel where possible
- Focus on high-value tests first (P0, P1)
- Use pair programming for faster test writing
- Allocate dedicated testing sprints

**Reduce Maintenance Overhead**:
- Write maintainable tests (DRY, clear naming)
- Use factories and builders for test data
- Keep tests focused (one assertion per test)
- Regular refactoring of test code

**Address Technical Debt**:
- Refactor for testability incrementally
- Build robust mocking infrastructure
- Document complex test scenarios
- Share testing patterns across team

## Implementation Notes

### Test Organization

```
tests/
├── unit/
│   ├── api/
│   │   ├── test_error_handlers.py (NEW)
│   │   ├── test_dependencies.py (NEW)
│   │   └── test_sample_router.py (NEW - unit level)
│   ├── service/
│   │   ├── test_historical_data_service.py (EXPAND)
│   │   ├── test_fermentation_service.py (EXPAND)
│   │   └── test_sample_service.py (EXPAND)
│   └── etl/
│       ├── test_etl_validator.py (EXPAND)
│       └── test_etl_service.py (EXPAND)
├── integration/
│   ├── api/
│   │   └── test_sample_router.py (NEW)
│   └── repository/
│       ├── test_sample_repository_integration.py (EXPAND)
│       ├── test_fermentation_repository_integration.py (EXPAND)
│       └── test_lot_source_repository_integration.py (EXPAND)
└── conftest.py (shared fixtures)
```

### Testing Patterns to Use

**API Tests**:
- Use TestClient from FastAPI
- Mock service layer dependencies
- Test all status codes (200, 400, 403, 404, 500)
- Test pagination, filtering, sorting
- Test multi-tenant isolation

**Repository Tests**:
- Use real database (integration tests)
- Test CRUD operations
- Test complex queries
- Test transactions and rollback
- Test constraints and foreign keys

**Service Tests**:
- Mock repository dependencies
- Test business logic in isolation
- Test validation rules
- Test error handling
- Test edge cases

### Coverage Exclusions

**Acceptable exclusions** (mark with `# pragma: no cover`):
- Abstract method definitions
- Type checking blocks (`if TYPE_CHECKING:`)
- Debug-only code
- Main entry points (if trivial)
- Generated code (Pydantic models)

**Not acceptable exclusions**:
- Complex business logic
- Error handling code
- Security-critical code
- Data manipulation code

## Success Metrics

### Quantitative

- [ ] Overall module coverage: 56% → 80%
- [ ] API layer coverage: 0-9% → 85%
- [ ] Repository layer coverage: 12-18% → 80%
- [ ] Service layer coverage: 14-30% → 80%
- [ ] All 1033 tests still passing (100%)
- [ ] Test execution time < 30 seconds

### Qualitative

- [ ] Developers confident in refactoring
- [ ] Bug detection rate increases
- [ ] Regression issues decrease
- [ ] Code review discussions focus on logic, not "where are tests?"
- [ ] New team members onboard faster with test examples

## Timeline

| Phase | Duration | Target Date | Owner |
|-------|----------|-------------|-------|
| Phase 1: API Layer | 2 days | Week 1 | TBD |
| Phase 2: Repository | 3 days | Week 1-2 | TBD |
| Phase 3: Service | 3 days | Week 2 | TBD |
| Phase 4: ETL | 3 days | Week 3 | TBD |
| **Total** | **11 days** | **Week 3** | - |

## References

- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- ADR-028: Testing Strategy and Standards
- ADR-032: Historical Data API Layer
- Coverage Report: `coverage_reports/fermentation/index.html`

## Revision History

- 2026-01-13: Initial draft with phased implementation plan
