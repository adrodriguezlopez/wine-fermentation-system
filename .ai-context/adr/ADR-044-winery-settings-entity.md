# ADR-044: WinerySettings Entity Design

**Status:** Proposed  
**Date:** 2026-04-19  
**Authors:** Wine Fermentation System Team

> **📋 Context:** [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md)

---

## Context

The system currently stores winery identity in the `Winery` entity (`code`, `name`, `location`, `notes`) but has no per-winery configuration layer. As the platform matures, wineries need to configure notification preferences (e.g. alert channels, thresholds), select default fermentation protocols, and set alert sensitivity thresholds. Embedding these fields directly into `Winery` would mix organizational identity with operational configuration, violating SRP and making the entity harder to evolve. ADR-016 (Winery Service Layer) and ADR-017 (Winery API) established the existing winery architecture and serve as the base this ADR extends. ADR-040 (Notifications & Alerts) defined alert strategy but deferred per-winery configuration to a future decision — this ADR makes that decision.

---

## Decision

1. Introduce a `WinerySettings` entity as a **1:1 owned extension** of `Winery`, stored in a separate `winery_settings` table with `winery_id` as both FK and PK (no surrogate key needed).
2. `WinerySettings` is owned exclusively by the `winery` module; no other module queries the `winery_settings` table directly — they call `WineryService.get_settings(winery_id)`.
3. The entity stores three categories of configuration: notification preferences (channel, frequency, enabled flags), default protocol reference (`default_protocol_id` as a nullable UUID — no FK constraint to avoid cross-module coupling), and alert thresholds (a JSON/JSONB column `alert_thresholds` for flexible key-value pairs).
4. Settings are created automatically (with defaults) when a `Winery` is created; they are never independently created or deleted — lifecycle is fully tied to the parent `Winery`.
5. Multi-tenancy scoping is enforced identically to `Winery`: all access is gated by `winery_id` from the JWT context, consistent with ADR-007 and the system-wide multi-tenancy rule.
6. `WinerySettingsRepository` is added to the winery module following the repository interface pattern from ADR-002; it exposes `get_by_winery_id()` and `update()` only (no create/delete — lifecycle is managed by `WineryService`).
7. Two new API endpoints are added under the existing `/admin/wineries/{id}` namespace: `GET /admin/wineries/{id}/settings` and `PATCH /admin/wineries/{id}/settings`, following ADR-017 authorization rules (ADMIN or own winery).

---

## Architectural Notes

> Seguimos [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) por defecto

**Cross-module reference without FK**: `default_protocol_id` is stored as a plain UUID with no database-level FK to the protocols table. This avoids a cross-module DB dependency (ADR-028, ADR-031 patterns). Validity is enforced at the service layer when protocols module is available.

**JSON for alert thresholds**: Using JSONB (PostgreSQL) for `alert_thresholds` accepts schema flexibility over strict typing. This is intentional — threshold keys are expected to evolve with new protocol types and anomaly detectors (ADR-020, ADR-038) without requiring migrations.

**1:1 as separate table (not columns on `wineries`)**: Keeps `wineries` table stable, avoids wide-table growth, and allows independent migration of settings schema.

---

## Consequences

- ✅ Clean separation: `Winery` = identity, `WinerySettings` = operational config
- ✅ Notification and protocol modules can read settings via `WineryService` without direct DB coupling
- ✅ JSONB `alert_thresholds` absorbs future threshold additions without migrations
- ✅ Follows all established patterns (ADR-002 repos, ADR-007 auth, ADR-016/017 winery layer)
- ⚠️ `default_protocol_id` referential integrity is not enforced at the DB level — service must validate on read/write
- ⚠️ JSONB `alert_thresholds` requires documented key conventions; no schema enforcement until a validator is added
- ❌ No support for per-user overrides of settings within a winery — winery-level granularity only (acceptable for MVP)

---

## Related ADRs

- [ADR-016: Winery Service Layer](./ADR-016-winery-service-layer.md) — extended by this ADR
- [ADR-017: Winery API Design](./ADR-017-winery-api-design.md) — new endpoints follow its patterns
- [ADR-002: Repository Architecture](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md) — `WinerySettingsRepository` follows this pattern
- [ADR-007: Auth Module](./ADR-007-auth-module-design.md) — winery_id scoping enforced via JWT
- [ADR-040: Notifications & Alerts Strategy](./ADR-040-notifications-alerts.md) — per-winery notification prefs fulfill deferred config decision
- [ADR-020: Analysis Engine Architecture](./ADR-020-analysis-engine-architecture.md) — alert thresholds consumed by anomaly detection
- [ADR-028: Module Dependency Management](./ADR-028-module-dependency-management.md) — cross-module reference via service, not DB FK

---

## Status

Proposed
