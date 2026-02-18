# Sequence Diagrams

> **Overview**: Detailed workflow sequences showing interactions between components for key operations.

## Create Fermentation Sequence

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant FermService as Fermentation Service
    participant Validator as Validation Orchestrator
    participant FermRepo as Fermentation Repository
    participant DB as PostgreSQL
    
    User->>API: POST /fermentations<br/>{vintage_year, yeast_strain, ...}
    activate API
    
    API->>API: Extract winery_id<br/>from JWT token
    
    API->>FermService: create_fermentation(data, winery_id, user_id)
    activate FermService
    
    FermService->>FermService: validate_fermentation_data(data)
    
    FermService->>Validator: orchestrate_validations(data, context)
    activate Validator
    
    Validator->>Validator: check_value_ranges()
    Validator->>Validator: validate_business_rules()
    Validator->>Validator: check_duplicate_vessel_code()
    
    Validator-->>FermService: ValidationResult(valid=true)
    deactivate Validator
    
    alt Data Invalid
        FermService-->>API: ValidationError
        API-->>User: 400 Bad Request
    else Data Valid
        FermService->>FermRepo: create(fermentation_entity, user_id)
        activate FermRepo
        
        FermRepo->>FermRepo: map_to_orm_model()
        FermRepo->>DB: INSERT INTO fermentations (...)
        activate DB
        
        DB-->>FermRepo: id (generated)
        deactivate DB
        
        FermRepo->>DB: COMMIT
        FermRepo-->>FermService: Fermentation(id=123, ...)
        deactivate FermRepo
        
        FermService-->>API: Fermentation entity
        deactivate FermService
        
        API->>API: serialize_to_response(fermentation)
        API-->>User: 201 Created<br/>{id, status, start_date, ...}
        deactivate API
    end
```

---

## Add Sample to Fermentation Sequence

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant SampleService as Sample Service
    participant Validator as Validation Orchestrator
    participant FermRepo as Fermentation Repo
    participant SampleRepo as Sample Repository
    participant DB as PostgreSQL
    participant Analysis as Analysis Engine<br/>(async)
    
    User->>API: POST /fermentations/{id}/samples<br/>{measurement_date, value, ...}
    activate API
    
    API->>API: Extract winery_id, user_id
    
    API->>SampleService: create_sample(ferm_id, data, winery_id)
    activate SampleService
    
    SampleService->>FermRepo: get_fermentation(ferm_id, winery_id)
    activate FermRepo
    FermRepo->>DB: SELECT * FROM fermentations WHERE id=? AND winery_id=?
    FermRepo-->>SampleService: Fermentation entity
    deactivate FermRepo
    
    alt Fermentation Not Found or Wrong Winery
        SampleService-->>API: NotFoundError
        API-->>User: 404 Not Found
    else Fermentation Valid
        SampleService->>SampleService: map_sample_type(data)
        
        SampleService->>Validator: orchestrate_validations(sample, fermentation)
        activate Validator
        
        Validator->>Validator: value_validation()
        Note over Validator: Check: min/max range<br/>Check: valid type
        
        Validator->>Validator: chronology_validation()
        Note over Validator: Get previous sample<br/>Check: measurements in order<br/>Check: time gaps
        
        Validator->>Validator: business_rule_validation()
        Note over Validator: Check: fermentation status<br/>Check: sample consistency
        
        Validator-->>SampleService: ValidationResult(valid=true)
        deactivate Validator
        
        alt Validation Failed
            SampleService-->>API: ValidationError(reason)
            API-->>User: 400 Bad Request
        else Validation Passed
            SampleService->>SampleRepo: create(sample_entity)
            activate SampleRepo
            
            SampleRepo->>DB: INSERT INTO samples (...)
            activate DB
            DB-->>SampleRepo: sample_id (generated)
            deactivate DB
            
            SampleRepo-->>SampleService: Sample entity
            deactivate SampleRepo
            
            SampleService-->>API: Sample entity
            deactivate SampleService
            
            API->>API: serialize_to_response()
            API-->>User: 201 Created<br/>{id, value, measurement_date, ...}
            deactivate API
            
            Note over Analysis: Async trigger
            par Async Processing
                Analysis->>Analysis: analyze_fermentation(ferm_id)
                Analysis->>Analysis: detect_anomalies()
                Analysis->>Analysis: generate_recommendations()
            end
        end
    end
```

---

## Fermentation Analysis Sequence

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant OrchestratorService as Analysis Orchestrator
    participant AnomalyDetector as Anomaly Detection Service
    participant PatternService as Pattern Analysis Service
    participant RecommendationService as Recommendation Service
    participant AnalysisRepo as Analysis Repository
    participant TemplateRepo as Template Repository
    participant DB as PostgreSQL
    
    User->>API: POST /fermentations/{id}/analyze
    activate API
    
    API->>OrchestratorService: orchestrate_analysis(ferm_id, winery_id)
    activate OrchestratorService
    
    OrchestratorService->>OrchestratorService: create_analysis_record()
    OrchestratorService->>AnalysisRepo: save_initial_analysis()
    
    OrchestratorService->>AnomalyDetector: run_all_detections(fermentation)
    activate AnomalyDetector
    
    AnomalyDetector->>PatternService: compare_vs_historical(fermentation)
    activate PatternService
    
    PatternService->>DB: SELECT * FROM historical_samples WHERE winery_id=?
    PatternService->>PatternService: calculate_z_scores()
    PatternService->>PatternService: extract_trend_pattern()
    PatternService-->>AnomalyDetector: PatternAnalysis(percentile, deviation)
    deactivate PatternService
    
    AnomalyDetector->>AnomalyDetector: detect_slow_fermentation()
    AnomalyDetector->>AnomalyDetector: detect_stuck_fermentation()
    AnomalyDetector->>AnomalyDetector: detect_temperature_issues()
    AnomalyDetector->>AnomalyDetector: detect_h2s_production()
    
    AnomalyDetector->>AnomalyDetector: aggregate_anomalies()
    AnomalyDetector-->>OrchestratorService: [Anomaly, Anomaly, ...]
    deactivate AnomalyDetector
    
    OrchestratorService->>AnalysisRepo: add_anomalies(anomalies)
    
    alt Anomalies Detected
        OrchestratorService->>RecommendationService: generate_recommendations(anomalies)
        activate RecommendationService
        
        loop For each Anomaly
            RecommendationService->>TemplateRepo: get_templates_for_anomaly(type, severity)
            TemplateRepo->>DB: SELECT * FROM templates WHERE type=? AND severity=?
            TemplateRepo-->>RecommendationService: [Template, Template, ...]
            
            RecommendationService->>RecommendationService: rank_by_historical_success()
            RecommendationService->>RecommendationService: filter_by_winery_context()
        end
        
        RecommendationService-->>OrchestratorService: [Recommendation, ...]
        deactivate RecommendationService
        
        OrchestratorService->>AnalysisRepo: add_recommendations(recommendations)
    end
    
    OrchestratorService->>AnalysisRepo: update_status(COMPLETED)
    OrchestratorService->>AnalysisRepo: save_confidence_scores()
    
    OrchestratorService-->>API: AnalysisResult(anomalies, recommendations)
    deactivate OrchestratorService
    
    API->>API: serialize_to_response()
    API-->>User: 200 OK<br/>{status: COMPLETED,<br/>anomalies: [...],<br/>recommendations: [...]}
    deactivate API
```

---

## User Login Sequence

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant AuthService as Auth Service
    participant UserRepo as User Repository
    participant PasswordService as Password Service
    participant JwtService as JWT Service
    participant DB as PostgreSQL
    
    User->>API: POST /auth/login<br/>{email, password}
    activate API
    
    API->>AuthService: login(email, password)
    activate AuthService
    
    AuthService->>UserRepo: get_by_email(email)
    activate UserRepo
    
    UserRepo->>DB: SELECT * FROM users WHERE email=?
    activate DB
    DB-->>UserRepo: User record
    deactivate DB
    
    alt User Not Found
        UserRepo-->>AuthService: UserNotFoundError
        AuthService-->>API: InvalidCredentialsError
        API-->>User: 401 Unauthorized
    else User Found
        deactivate UserRepo
        
        alt User is Inactive
            AuthService-->>API: UserInactiveError
            API-->>User: 403 Forbidden
        else User is Active
            AuthService->>PasswordService: verify_password(password, hashed_pw)
            activate PasswordService
            
            PasswordService->>PasswordService: bcrypt.verify()
            
            alt Password Invalid
                PasswordService-->>AuthService: False
                AuthService-->>API: InvalidCredentialsError
                API-->>User: 401 Unauthorized
            else Password Valid
                PasswordService-->>AuthService: True
                deactivate PasswordService
                
                AuthService->>JwtService: encode_token(user_context)
                activate JwtService
                
                JwtService->>JwtService: create_claims_from_user()
                JwtService->>JwtService: jwt.encode(claims, secret, algorithm)
                
                JwtService-->>AuthService: AccessToken, RefreshToken
                deactivate JwtService
                
                AuthService->>UserRepo: update_last_login(user_id)
                
                AuthService-->>API: LoginResponse(access_token, refresh_token)
                deactivate AuthService
                
                API-->>User: 200 OK<br/>{access_token,<br/>refresh_token,<br/>token_type: bearer}
            end
        end
    end
    deactivate API
```

---

## Historical Data Comparison Sequence

```mermaid
sequenceDiagram
    participant User
    participant API as API Layer
    participant HistoricalService as Historical Service
    participant FermService as Fermentation Service
    participant PatternService as Pattern Analysis
    participant HistoricalRepo as Historical Repository
    participant DB as PostgreSQL
    
    User->>API: GET /fermentations/{id}/compare<br/>?days=30&varietal=Cabernet
    activate API
    
    API->>FermService: get_fermentation(id, winery_id)
    
    FermService->>FermService: Extract current samples
    
    API->>HistoricalService: compare_with_historical(current, filters)
    activate HistoricalService
    
    HistoricalService->>HistoricalRepo: get_similar_fermentations(criteria)
    activate HistoricalRepo
    
    HistoricalRepo->>DB: SELECT * FROM historical_data<br/>WHERE winery_id=?<br/>AND varietal=?<br/>AND created_at > (now - 30 days)
    activate DB
    
    DB-->>HistoricalRepo: [HistoricalSample, ...]
    deactivate DB
    
    HistoricalRepo-->>HistoricalService: List[HistoricalPattern]
    deactivate HistoricalRepo
    
    HistoricalService->>PatternService: extract_percentiles(historical_samples)
    activate PatternService
    
    PatternService->>PatternService: calculate_p25, p50, p75, p90
    PatternService->>PatternService: extract_trend_curves()
    PatternService->>PatternService: identify_deviation_thresholds()
    
    PatternService-->>HistoricalService: PatternProfile(percentiles, trends)
    deactivate PatternService
    
    HistoricalService->>HistoricalService: compare_current_vs_profile()
    HistoricalService->>HistoricalService: calculate_confidence_scores()
    
    HistoricalService-->>API: ComparisonResult(expected_range, actual_value, percentile)
    deactivate HistoricalService
    
    API->>API: serialize_to_response()
    API-->>User: 200 OK<br/>{current_value,<br/>expected_min,<br/>expected_max,<br/>percentile_rank,<br/>similar_batches_count}
```

---

## Multi-Winery Data Isolation Sequence

```mermaid
sequenceDiagram
    actor WineryA_User
    actor WineryB_User
    participant API as API Layer
    participant FermService as Fermentation Service
    participant FermRepo as Fermentation Repository
    participant DB as PostgreSQL
    
    WineryA_User->>API: GET /fermentations<br/>Header: Authorization: Bearer token_A
    activate API
    
    API->>API: decode_jwt(token_A)
    API->>API: Extract: winery_id=1, user_id=100
    
    API->>FermService: list_fermentations(winery_id=1)
    activate FermService
    
    FermService->>FermRepo: list_by_winery(winery_id=1)
    activate FermRepo
    
    FermRepo->>DB: SELECT * FROM fermentations<br/>WHERE winery_id=1 AND is_deleted=false
    activate DB
    
    DB-->>FermRepo: [Fermentation_A1, Fermentation_A2, ...]
    deactivate DB
    
    FermRepo-->>FermService: Results
    deactivate FermRepo
    
    FermService-->>API: Results
    deactivate FermService
    
    API-->>WineryA_User: 200 OK<br/>[Fermentation_A1, Fermentation_A2]
    deactivate API
    
    par Parallel Request from Winery B
        WineryB_User->>API: GET /fermentations<br/>Header: Authorization: Bearer token_B
        activate API
        
        API->>API: decode_jwt(token_B)
        API->>API: Extract: winery_id=2, user_id=200
        
        API->>FermService: list_fermentations(winery_id=2)
        activate FermService
        
        FermService->>FermRepo: list_by_winery(winery_id=2)
        activate FermRepo
        
        FermRepo->>DB: SELECT * FROM fermentations<br/>WHERE winery_id=2 AND is_deleted=false
        activate DB
        
        DB-->>FermRepo: [Fermentation_B1, Fermentation_B2, ...]
        deactivate DB
        
        FermRepo-->>FermService: Results
        deactivate FermRepo
        
        FermService-->>API: Results
        deactivate FermService
        
        API-->>WineryB_User: 200 OK<br/>[Fermentation_B1, Fermentation_B2]
        deactivate API
    end
    
    Note over DB: Winery A only sees their data<br/>Winery B only sees their data<br/>COMPLETE DATA ISOLATION
```

---

## Soft Delete Sequence

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant FermService as Fermentation Service
    participant FermRepo as Fermentation Repository
    participant DB as PostgreSQL
    
    User->>API: DELETE /fermentations/{id}
    activate API
    
    API->>FermService: delete_fermentation(id, winery_id, user_id)
    activate FermService
    
    FermService->>FermRepo: delete(id, winery_id, user_id)
    activate FermRepo
    
    FermRepo->>FermRepo: Load current entity
    FermRepo->>DB: SELECT * FROM fermentations WHERE id=? AND winery_id=?
    activate DB
    DB-->>FermRepo: Fermentation record
    deactivate DB
    
    FermRepo->>FermRepo: Set deleted_at = NOW()
    FermRepo->>DB: UPDATE fermentations SET deleted_at=NOW()<br/>WHERE id=? AND winery_id=?
    activate DB
    DB-->>FermRepo: Rows affected: 1
    deactivate DB
    
    FermRepo-->>FermService: Soft-deleted entity
    deactivate FermRepo
    
    FermService-->>API: Success
    deactivate FermService
    
    API-->>User: 204 No Content
    deactivate API
    
    Note over DB: Data still in DB but marked deleted<br/>WHERE clauses filter IS_DELETED=false<br/>Admin can still recover if needed
    
    User->>API: GET /fermentations
    API->>FermRepo: list_by_winery(winery_id=1)
    FermRepo->>DB: SELECT * FROM fermentations<br/>WHERE winery_id=1 AND is_deleted=false
    DB-->>FermRepo: [Other fermentations only]
    API-->>User: Deleted fermentation NOT included
```

---

## Start Protocol Execution Sequence (ADR-021)

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant ProtocolService as Protocol Service
    participant ProtocolRepo as Protocol Repository
    participant ExecutionRepo as Execution Repository
    participant DB as PostgreSQL
    
    User->>API: POST /fermentations/{id}/protocol/start<br/>{protocol_id}
    activate API
    
    API->>API: Extract winery_id from JWT
    
    API->>ProtocolService: start_protocol_execution(ferm_id, protocol_id, winery_id)
    activate ProtocolService
    
    ProtocolService->>ProtocolRepo: get_protocol(protocol_id, winery_id)
    activate ProtocolRepo
    
    ProtocolRepo->>DB: SELECT * FROM fermentation_protocols<br/>WHERE id=? AND winery_id=?
    activate DB
    DB-->>ProtocolRepo: Protocol + Steps
    deactivate DB
    
    ProtocolRepo-->>ProtocolService: FermentationProtocol(steps=8)
    deactivate ProtocolRepo
    
    alt Protocol Not Found
        ProtocolService-->>API: NotFoundError
        API-->>User: 404 Not Found
    else Protocol Valid
        ProtocolService->>ProtocolService: validate_protocol_applicable()
        
        ProtocolService->>ExecutionRepo: create_execution(fermentation, protocol)
        activate ExecutionRepo
        
        ExecutionRepo->>DB: INSERT INTO protocol_executions<br/>(fermentation_id, protocol_id, winery_id,<br/>start_date, status, compliance_score=0)
        activate DB
        
        DB-->>ExecutionRepo: execution_id (generated)
        deactivate DB
        
        ExecutionRepo->>DB: INSERT INTO step_completions<br/>(AUDIT LOG READY)
        activate DB
        DB-->>ExecutionRepo: Ready for step logging
        deactivate DB
        
        ExecutionRepo-->>ProtocolService: ProtocolExecution(id=456, steps_pending=8)
        deactivate ExecutionRepo
        
        ProtocolService-->>API: ProtocolExecution(status=ACTIVE)
        deactivate ProtocolService
        
        API->>API: serialize_to_response()
        API-->>User: 201 Created<br/>{execution_id, total_steps,<br/>steps_completed: 0,<br/>compliance_score: 0%}
        deactivate API
    end
```

---

## Log Step Completion Sequence (ADR-021)

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant ProtocolService as Protocol Service
    participant ComplianceService as Compliance Tracking Service
    participant ExecutionRepo as Execution Repository
    participant StepRepo as Step Completion Repository
    participant DB as PostgreSQL
    
    User->>API: POST /fermentations/{id}/protocol/steps/{step_id}/complete<br/>{notes, verified_by}
    activate API
    
    API->>API: Extract winery_id, user_id
    
    API->>ProtocolService: log_step_completion(exec_id, step_id, notes, user_id)
    activate ProtocolService
    
    ProtocolService->>ExecutionRepo: get_execution(exec_id, winery_id)
    activate ExecutionRepo
    
    ExecutionRepo->>DB: SELECT * FROM protocol_executions<br/>WHERE id=? AND winery_id=?
    activate DB
    DB-->>ExecutionRepo: Execution record
    deactivate DB
    
    ExecutionRepo-->>ProtocolService: ProtocolExecution
    deactivate ExecutionRepo
    
    alt Execution Not Found or Completed
        ProtocolService-->>API: InvalidStateError
        API-->>User: 400 Bad Request
    else Execution Active
        ProtocolService->>ProtocolService: validate_step_exists_in_protocol()
        ProtocolService->>ProtocolService: check_step_not_already_completed()
        
        ProtocolService->>ProtocolService: Get expected_day for step
        ProtocolService->>ProtocolService: Calculate: on_schedule = (actual_date <= expected_date + 1)
        
        ProtocolService->>StepRepo: create_step_completion(step_id, exec_id, notes, on_schedule)
        activate StepRepo
        
        StepRepo->>DB: INSERT INTO step_completions<br/>(execution_id, step_id, completed_at, notes,<br/>on_schedule, verified_by)
        activate DB
        
        DB-->>StepRepo: completion_id (generated)
        deactivate DB
        
        StepRepo-->>ProtocolService: StepCompletion(on_schedule=true)
        deactivate StepRepo
        
        ProtocolService->>ComplianceService: calculate_compliance_score(exec_id)
        activate ComplianceService
        
        ComplianceService->>DB: SELECT COUNT(*) FROM step_completions<br/>WHERE execution_id=? (completed_steps)
        activate DB
        DB-->>ComplianceService: completed_steps=5
        deactivate DB
        
        ComplianceService->>DB: SELECT total_steps FROM fermentation_protocols (total=8)
        activate DB
        DB-->>ComplianceService: total_steps=8
        deactivate DB
        
        ComplianceService->>ComplianceService: base_score = (5/8) * 100 = 62.5%
        ComplianceService->>ComplianceService: on_schedule_steps = 4/5
        ComplianceService->>ComplianceService: Apply penalties for skipped critical steps
        ComplianceService->>ComplianceService: final_score = 62.5% - penalties = 58%
        
        ComplianceService-->>ProtocolService: compliance_score=58%
        deactivate ComplianceService
        
        ProtocolService->>ExecutionRepo: update_compliance_score(exec_id, 58)
        activate ExecutionRepo
        
        ExecutionRepo->>DB: UPDATE protocol_executions<br/>SET compliance_score=58, updated_at=NOW()<br/>WHERE id=?
        activate DB
        DB-->>ExecutionRepo: Updated
        deactivate DB
        
        ExecutionRepo-->>ProtocolService: Updated execution
        deactivate ExecutionRepo
        
        ProtocolService-->>API: StepCompletion(compliance_updated=58%)
        deactivate ProtocolService
        
        API-->>User: 200 OK<br/>{step_id, completed_at,<br/>on_schedule: true,<br/>new_compliance_score: 58%,<br/>steps_remaining: 3}
        deactivate API
    end
```

---

## Create Harvest Lot & Link to Fermentation Sequence

```mermaid
sequenceDiagram
    actor User
    participant API as API Layer
    participant HarvestService as Harvest Lot Service
    participant FermService as Fermentation Service
    participant HarvestRepo as Harvest Repository
    participant FermRepo as Fermentation Repository
    participant LotSourceRepo as Lot Source Repository
    participant DB as PostgreSQL
    
    User->>API: POST /harvest-lots<br/>{vineyard_id, quantity_kg, harvest_date, ...}
    activate API
    
    API->>HarvestService: create_harvest_lot(data, winery_id, user_id)
    activate HarvestService
    
    HarvestService->>HarvestService: validate_harvest_data()
    
    HarvestService->>HarvestRepo: create(harvest_lot_entity)
    activate HarvestRepo
    
    HarvestRepo->>DB: INSERT INTO harvest_lots<br/>(vineyard_id, winery_id, harvest_date, ...)<br/>VALUES (...)
    activate DB
    
    DB-->>HarvestRepo: harvest_lot_id (generated)
    deactivate DB
    
    HarvestRepo-->>HarvestService: HarvestLot(id=789, status=AVAILABLE)
    deactivate HarvestRepo
    
    HarvestService-->>API: HarvestLot
    deactivate HarvestService
    
    API-->>User: 201 Created<br/>{id: 789, status: AVAILABLE, ...}
    deactivate API
    
    Note over User: Later: Link to Fermentation
    
    User->>API: POST /fermentations/{ferm_id}/sources<br/>{harvest_lot_id, percentage}
    activate API
    
    API->>FermService: link_harvest_sources(ferm_id, sources)
    activate FermService
    
    FermService->>FermRepo: get_fermentation(ferm_id, winery_id)
    FermService->>HarvestRepo: verify_harvest_lot(harvest_lot_id, winery_id)
    
    FermService->>FermService: validate_percentages_total_100()
    
    FermService->>LotSourceRepo: create_bulk(fermentation_id, harvest_sources)
    activate LotSourceRepo
    
    LotSourceRepo->>DB: INSERT INTO fermentation_lot_sources<br/>(fermentation_id, harvest_lot_id, percentage)
    activate DB
    
    DB-->>LotSourceRepo: source_id (generated)
    deactivate DB
    
    LotSourceRepo-->>FermService: [LotSource, ...]
    deactivate LotSourceRepo
    
    FermService-->>API: Links created
    deactivate FermService
    
    API-->>User: 200 OK<br/>{fermentation_id: {ferm_id},<br/>sources: [{harvest_lot_id, percentage}],<br/>traceability_complete: true}
    deactivate API
```

---

## Manage User Roles & Permissions Sequence

```mermaid
sequenceDiagram
    actor Admin
    participant API as API Layer
    participant UserService as User Service
    participant UserRepo as User Repository
    participant AuditRepo as Audit Repository
    participant DB as PostgreSQL
    
    Admin->>API: PUT /users/{user_id}/role<br/>{new_role: WINEMAKER}
    activate API
    
    API->>API: Extract admin_user_id, winery_id from JWT
    API->>API: Verify role=ADMIN
    
    API->>UserService: update_user_role(user_id, new_role, admin_user_id, winery_id)
    activate UserService
    
    UserService->>UserRepo: get_user(user_id, winery_id)
    activate UserRepo
    
    UserRepo->>DB: SELECT * FROM users<br/>WHERE id=? AND winery_id=?
    activate DB
    DB-->>UserRepo: User record
    deactivate DB
    
    UserRepo-->>UserService: User(current_role=OPERATOR)
    deactivate UserRepo
    
    alt User Not Found or Wrong Winery
        UserService-->>API: NotFoundError
        API-->>Admin: 404 Not Found
    else User Valid
        UserService->>UserService: validate_role_hierarchy()
        Note over UserService: Admin can only assign<br/>roles <= their own level
        
        alt Invalid Role Assignment
            UserService-->>API: PermissionDeniedError
            API-->>Admin: 403 Forbidden
        else Valid Assignment
            UserService->>UserRepo: update_role(user_id, new_role)
            activate UserRepo
            
            UserRepo->>DB: UPDATE users<br/>SET role=?, updated_at=NOW()<br/>WHERE id=? AND winery_id=?
            activate DB
            
            DB-->>UserRepo: Rows affected: 1
            deactivate DB
            
            UserRepo-->>UserService: Updated user
            deactivate UserRepo
            
            UserService->>AuditRepo: log_role_change(user_id, old_role, new_role, admin_id)
            activate AuditRepo
            
            AuditRepo->>DB: INSERT INTO audit_log<br/>(action, user_id, changes, performed_by)
            activate DB
            
            DB-->>AuditRepo: audit_id
            deactivate DB
            
            AuditRepo-->>UserService: Audit logged
            deactivate AuditRepo
            
            UserService-->>API: Updated user(role=WINEMAKER)
            deactivate UserService
            
            API-->>Admin: 200 OK<br/>{user_id, new_role: WINEMAKER,<br/>permissions_updated: true,<br/>effective_from: next_login}
            deactivate API
            
            Note over DB: Change takes effect at next login<br/>Current session keeps old permissions
        end
    end
```

---

## Refresh Access Token Sequence

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Frontend Client
    participant API as API Layer
    participant AuthService as Auth Service
    participant JwtService as JWT Service
    participant UserRepo as User Repository
    participant DB as PostgreSQL
    
    Frontend->>Frontend: Check access_token expiry
    Frontend->>Frontend: If < 5min remaining, refresh
    
    Frontend->>API: POST /auth/refresh<br/>Body: {refresh_token}
    activate API
    
    API->>AuthService: refresh_access_token(refresh_token)
    activate AuthService
    
    AuthService->>JwtService: decode_refresh_token(refresh_token)
    activate JwtService
    
    JwtService->>JwtService: jwt.decode(refresh_token, secret)
    
    alt Token Invalid or Expired
        JwtService-->>AuthService: TokenInvalidError
        AuthService-->>API: UnauthorizedError
        API-->>Frontend: 401 Unauthorized
    else Token Valid
        JwtService-->>AuthService: user_id, winery_id
        deactivate JwtService
        
        AuthService->>UserRepo: get_user(user_id, winery_id)
        activate UserRepo
        
        UserRepo->>DB: SELECT * FROM users WHERE id=?
        activate DB
        DB-->>UserRepo: User record
        deactivate DB
        
        UserRepo-->>AuthService: User(is_active=true)
        deactivate UserRepo
        
        alt User Deactivated Since Login
            AuthService-->>API: UserInactiveError
            API-->>Frontend: 403 Forbidden
        else User Still Active
            AuthService->>JwtService: encode_token(user_context)
            activate JwtService
            
            JwtService->>JwtService: Create new claims
            JwtService->>JwtService: jwt.encode(claims, secret)
            
            JwtService-->>AuthService: New AccessToken
            deactivate JwtService
            
            AuthService-->>API: LoginResponse(new_access_token)
            deactivate AuthService
            
            API-->>Frontend: 200 OK<br/>{access_token: NEW_TOKEN,<br/>token_type: bearer,<br/>expires_in: 3600}
            deactivate API
            
            Frontend->>Frontend: Store new access_token
            Frontend->>Frontend: Update Authorization header
        end
    end
```

---

## Status

| Sequence | Status | Details |
|----------|--------|---------|
| **Create Fermentation** | ✅ Complete | Create + Validation + Persistence |
| **Add Sample** | ✅ Complete | Multi-level validation + Async analysis trigger |
| **Fermentation Analysis** | ✅ Complete | Anomaly detection + Recommendations |
| **User Login** | ✅ Complete | Auth + JWT token generation |
| **Historical Comparison** | ✅ Complete | Pattern extraction + Comparison |
| **Multi-Tenancy Isolation** | ✅ Complete | Winery ID scoping at all layers |
| **Soft Delete** | ✅ Complete | Logical deletion + Recovery support |
| **Start Protocol Execution** | 📋 Proposed | Protocol setup + tracking |
| **Log Step Completion** | 📋 Proposed | Step audit + Compliance scoring |
| **Create & Link Harvest** | ✅ Complete | Traceability chain |
| **Manage User Roles** | ✅ Complete | Role hierarchy + Audit logging |
| **Refresh Token** | ✅ Complete | Token renewal + Session continuity |

