Task List for ADR-001: Fruit Origin Model Implementation
1. Define New Domain Entities
Description: Create SQLAlchemy models/entities for Winery, Vineyard, VineyardBlock, HarvestLot, and FermentationLotSource in the domain layer. Expected Result: New Python classes with correct fields, relationships, and constraints. Comments: Follow DDD conventions; ensure all FK and uniqueness constraints are present.

2. Update Fermentation Entity
Description: Add winery_id and input_mass_kg fields to Fermentation. Update relationships to support new associations. Expected Result: Fermentation model supports links to Winery and FermentationLotSource. Comments: Refactor existing code to use new relationships.

3. Implement Association Table (FermentationLotSource)
Description: Create the FermentationLotSource entity to link Fermentation and HarvestLot, including mass_used_kg with a check constraint. Expected Result: Association table with correct FKs and business rule enforcement. Comments: Enforce that no duplicate HarvestLot per fermentation.

4. Add/Update Database Constraints ✅ COMPLETADO
Description: Implement all UNIQUE, FK, and CHECK constraints as described in the ADR. Expected Result: Database schema enforces all invariants (uniqueness, mass > 0, etc.). Comments: Use SQLAlchemy/DDL for constraints; test with migrations.

5. 🚫 BLOQUEADO - Update Domain Services and Repositories
Description: Refactor or extend repositories and services to support CRUD for new entities and associations. Expected Result: Service and repository layers can create, update, and query the new model. Comments: Ensure all business invariants are checked in service logic.
**BLOQUEADOR**: No existen domain services ni repositories base en el proyecto. Requiere decisión arquitectural.

6. 🚫 BLOQUEADO - Implement Business Invariants
Description: Enforce rules such as sum of mass_used_kg equals input_mass_kg, no duplicate lots, all lots from same winery, and harvest date ≤ fermentation start. Expected Result: Validation logic in service layer; errors raised on violation. Comments: Add unit tests for all invariants.
**BLOQUEADOR**: Depende completamente de step 5 (domain services).

7. ⚠️ EN PAUSA - Update API Schemas and Endpoints
Description: Extend Pydantic schemas and FastAPI endpoints to support new entities and relationships. Expected Result: API allows creation, update, and retrieval of full fruit origin hierarchy. Comments: Document new endpoints and update OpenAPI spec.
**EN PAUSA**: Sin services, las APIs no pueden implementar lógica de negocio correcta.

8. ⚠️ EN PAUSA - Update ERD and Documentation
Description: Add/modify diagrams and Markdown docs to reflect new model and relationships. Expected Result: Up-to-date ERD and context documentation. Comments: Sync with domain-model-guide.md and project-context.md.

9. Data Migration/Seeding (if needed)
Description: Create migration scripts or seeders for initial data (e.g., default winery, vineyards). Expected Result: Database can be initialized with valid data for testing. Comments: Use Alembic or similar tool.

10. Integration and Unit Testing
Description: Write tests for all new entities, services, and API endpoints. Expected Result: High test coverage for new model; all invariants and constraints are tested. Comments: Include edge cases (e.g., blends, invalid mass, cross-winery lots).

11. Review and Refactor Access Control
Description: Ensure user isolation and permissions are enforced for new entities (e.g., winemakers only see their own winery’s data). Expected Result: No cross-winery data leakage; permissions enforced at API/service level. Comments: Update authentication/authorization logic as needed.