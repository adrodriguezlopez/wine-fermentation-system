
# Component Context: Service Component (Fermentation Management Module)

> **Parent Context**: See `../module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
Business logic and validation for fermentation workflows. Orchestrates business rules, coordinates between API and Repository components, and enforces data validation and fermentation lifecycle management.

## Architecture pattern
Service Layer Pattern with dependency injection and clear separation of concerns.


## Arquitectura específica del componente
- **Services**: ValidationOrchestrator, ValidationService, ValueValidationService, BusinessRuleValidationService, ChronologyValidationService (en el futuro: FermentationService, SampleService, etc.)
- **Interfaces**: IFermentationService, ISampleService, IValidationService, IValidationOrchestrator, IValueValidationService, IBusinessRuleValidationService, IChronologyValidationService, IAnalysisEngineClient
- **Data flow**: Request → Validation → DomainService → (Repository via domain interfaces) → Response
- **Extension points**: Nuevas reglas de validación, servicios de dominio adicionales, lógica de negocio personalizada
- **Integration strategy**: Coordinación async con otros módulos vía interfaces de servicio

## Component interfaces

### **Receives from (API Component)**
- CreateFermentationRequest: New fermentation data
- AddSampleRequest: New measurement data
- GetFermentationRequest: Status/history retrieval

### **Provides to (API Component)**
- FermentationResult: Processed fermentation data
- SampleAdditionResult: Confirmation and validation results
- ValidationError: Error details when business rules fail


### **Uses (Repository Component)**
- Acceso a persistencia a través de interfaces ubicadas en `domain` (ej: IFermentationRepository, ISampleRepository), compartidas entre componentes para desacoplar la lógica de negocio de la infraestructura.
- Coordinación de transacciones multi-entidad mediante estas interfaces.

## Key patterns implemented
- Domain Service Pattern: Business logic in domain-specific services
- Dependency Injection: Services receive repository interfaces
- Transaction Coordination: Ensures data consistency
- Event Coordination: Triggers analysis workflows after data updates


## Interfaces resumen (nombre: uso - métodos/campos clave)
- IValidationOrchestrator: Orquesta validaciones - validate_sample_complete(fermentation_id, sample), validate_sample_batch(fermentation_id, samples)
- IValidationService: Validación de muestras y reglas - validate_samples, validate_chronology, validate_sample_value, validate_sugar_trend
- IValueValidationService: Validación de valores - validate_sample_value(sample_type, value), validate_numeric_value
- IBusinessRuleValidationService: Reglas de negocio - validate_sugar_trend, validate_temperature_range
- IChronologyValidationService: Cronología de muestras - validate_sample_chronology(fermentation_id, new_sample)
- IFermentationService: Gestión de fermentaciones - create_fermentation, get_fermentation, add_sample
- ISampleService: Gestión de muestras - validate_sample, get_sample, get_samples_in_range, get_latest_sample
- IAnalysisEngineClient: Motor de análisis externo - analyze_sample, get_trend_analysis, predict_completion, detect_anomalies, get_recommendations

> **Nota:** Las interfaces de repositorio (ej: IFermentationRepository, ISampleRepository) residen en la carpeta `domain` para permitir acceso desacoplado y compartido entre Service y Repository Component, facilitando mantenibilidad y escalabilidad.

## Business rules enforced
- Sample chronology: Enforce time-ordered sample addition
- Data trends: Validate glucose/ethanol progression
- User isolation: Ensure operations respect user boundaries
- Status transitions: Manage ACTIVE → SLOW → STUCK → COMPLETED
- Measurement validation: Enforce realistic ranges and detect anomalies

## Connection with other components
API Component: Receives business requests, returns processed results
Repository Component: Uses interfaces for persistence, manages transactions
Analysis Engine Module: Calls external analysis after sample addition

## Implementation status
- **Implemented**: Core service classes and interfaces present
- **Next steps**: Extender lógica de negocio y validaciones según necesidades

## Key implementation considerations
- Async operations: All service methods are async
- Error handling: Business rule violations return detailed messages
- Testing: Service classes are unit testable with mocked repositories
- Performance: Batch operations supported for multiple samples