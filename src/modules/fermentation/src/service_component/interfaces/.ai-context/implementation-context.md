# Implementation Context: Interfaces (Service Component - Fermentation Management Module)

## GLOBAL INTERACTION RULES
These rules are MANDATORY for ALL interactions in this conversation:

1. **Strict TDD Development**:
   - ALL code changes MUST follow TDD methodology
   - NO exceptions to Red-Green-Refactor cycle
   - Every feature MUST start with a failing test

2. **Sequential Development**:
   - Work on ONE file at a time
   - Complete current implementation before moving on
   - NO parallel development allowed

3. **Explicit Approval Protocol**:
   - MUST get approval before starting new file
   - MUST get confirmation after each TDD cycle
   - MUST get explicit go-ahead for refactoring
   - NO implicit approvals or assumptions

These rules are PERMANENT and apply to ALL future interactions.

## Interfaces responsibility
**Contract definitions and abstractions** for all interfaces within the Service Component of Fermentation Management Module.

**Architectural scope**: All interface contracts that define service abstractions, repository contracts, and external integration points.

## CRITICAL DEVELOPMENT RULES
These rules are MANDATORY and UNCHANGEABLE for all development work:

1. **TDD First**: 
   - STRICT Test-Driven Development methodology
   - NO exceptions to Red-Green-Refactor cycle
   - ALL code must start with a failing test

2. **File-by-File Development**:
   - Work on ONE file at a time
   - Complete current file before moving to next
   - NO parallel implementation allowed

3. **Explicit Approval Required**:
   - MUST get approval before moving to next file
   - MUST get approval after completing each TDD cycle
   - MUST get approval before any major refactoring
   - NO assumptions about implicit approval

These rules are NON-NEGOTIABLE and will be followed for the ENTIRE project lifecycle.

## Interface architecture
- **IFermentationService**: Contract for fermentation lifecycle management and business operations
- **ISampleService**: Contract for sample management and validation operations
- **IValidationService**: Contract for cross-cutting validation rules and data integrity
- **IFermentationRepository**: Contract for fermentation data persistence operations
- **ISampleRepository**: Contract for sample data persistence operations
- **IAnalysisEngineClient**: Contract for communication with Analysis Engine Module

## Interface categories

### **Service Layer Interfaces**
- **Purpose**: Define business logic contracts that API layer can depend on
- **Pattern**: Abstract base classes with business operation methods
- **Responsibility**: Enforce business rules, coordinate workflows, manage domain logic
- **Dependencies**: Repository interfaces, external service interfaces

### **Repository Layer Interfaces** 
- **Purpose**: Define data persistence contracts that services can depend on
- **Pattern**: Abstract base classes with CRUD and query operations
- **Responsibility**: Data access, entity persistence, query operations
- **Dependencies**: Domain entities, database abstractions

### **External Integration Interfaces**
- **Purpose**: Define contracts for communication with other modules
- **Pattern**: Abstract base classes with integration operation methods
- **Responsibility**: External service calls, data transformation, error handling
- **Dependencies**: External service DTOs, network abstractions

## Key interface patterns

### **Naming conventions**
- Service interfaces: `I[DomainName]Service` (IFermentationService, ISampleService)
- Repository interfaces: `I[EntityName]Repository` (IFermentationRepository, ISampleRepository)
- Client interfaces: `I[ExternalService]Client` (IAnalysisEngineClient)
- All interfaces prefixed with `I` for clear identification

### **Method patterns**
- **Async operations**: All I/O operations (database, external services) must be async
- **Sync operations**: Pure business logic and validation can be synchronous
- **Return types**: Use specific DTOs and domain entities, avoid generic types
- **Parameters**: Accept domain entities and specific DTOs, not generic dictionaries

### **Error handling patterns**
- **Service interfaces**: Raise specific business exceptions with detailed messages
- **Repository interfaces**: Return None for not-found, raise exceptions for errors
- **Client interfaces**: Handle network failures gracefully, provide fallback responses
- **Validation interfaces**: Return detailed ValidationResult objects, don't raise exceptions

### **Dependency injection patterns**
- All interfaces designed for constructor injection
- Services depend on repository interfaces, never concrete implementations
- Repository interfaces depend on database abstractions
- Client interfaces depend on network/HTTP abstractions

## Interface relationships
- **Service → Repository**: Services use repository interfaces for data persistence
- **Service → Client**: Services use client interfaces for external coordination
- **Service → Validation**: Services use validation interface for business rule enforcement
- **API → Service**: API layer depends on service interfaces, never repositories directly

## Implementation guidelines
- **Interface segregation**: Each interface focuses on single responsibility
- **Dependency inversion**: High-level modules depend on abstractions, not implementations
- **Contract documentation**: All interface methods have clear docstrings explaining purpose
- **Type safety**: Comprehensive type hints for all parameters and return types
- **Evolution strategy**: Add new methods with default implementations for backward compatibility

## Development Methodology
- **TDD Approach**: Strict Test-Driven Development methodology
- **Red-Green-Refactor Cycle**: 
  1. Write failing test first (Red)
  2. Implement minimum code to pass (Green)
  3. Improve code without changing behavior (Refactor)
- **Contract Testing**: Ensure implementations fulfill interface contracts
- **Mock Strategy**: Create test doubles for isolation during development

## Implementation Process
- **Step-by-Step Development**:
  1. Work on one file at a time
  2. Complete TDD cycle for each component
  3. Request explicit confirmation before moving to next file
  4. No parallel implementation to maintain focus
  
- **Confirmation Points**:
  1. Before starting each new interface implementation
  2. After completing contract tests
  3. After implementing mock classes
  4. Before moving to the next component
  5. After major refactoring phases

- **Development Order**:
  1. Start with core domain interfaces (IFermentationService)
  2. Move to supporting services (ISampleService, IValidationService)
  3. Implement repository interfaces
  4. Finally, external integration interfaces

## Testing Structure
```
tests/
├── unit/
│   ├── interfaces/
│   │   ├── test_fermentation_service_contract.py
│   │   ├── test_sample_service_contract.py
│   │   └── test_validation_service_contract.py
│   └── mocks/
│       ├── mock_fermentation_service.py
│       ├── mock_sample_service.py
│       └── mock_validation_service.py
└── integration/
    └── interfaces/
        ├── test_repository_implementations.py
        └── test_service_implementations.py
```

## Implementation status
- **NOT YET IMPLEMENTED**: All interfaces ready for definition
- **Implementation priority**: Repository interfaces → Service interfaces → Integration interfaces
- **Testing approach**: 
  1. Define interface contracts
  2. Create contract test cases
  3. Implement mock classes
  4. Develop real implementations

## Key implementation considerations
- **Backward compatibility**: Design interfaces to support future extension without breaking changes
- **Performance contracts**: Document expected performance characteristics in interface docstrings
- **Transaction boundaries**: Clearly define which operations should be transactional
- **Error propagation**: Define clear error handling contracts that implementations must follow

## TDD Testing Guidelines
- **Contract Tests**: 
  - Define expected behavior for each interface method
  - Verify error conditions and edge cases
  - Document performance expectations
  - Test async behavior correctly

- **Mock Implementation Tests**:
  - Verify mock behavior matches interface contract
  - Test error simulation capabilities
  - Ensure thread safety in async operations
  - Document mock behavior limitations

- **Test Categories**:
  1. **Contract Verification**: Ensure implementations follow interface specifications
  2. **Edge Cases**: Test boundary conditions and error scenarios
  3. **Async Behavior**: Verify proper async/await patterns
  4. **Integration Points**: Test interaction between components
  5. **Performance Requirements**: Validate timing and resource usage constraints