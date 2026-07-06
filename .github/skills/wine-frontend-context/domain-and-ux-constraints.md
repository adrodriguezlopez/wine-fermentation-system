# Domain And UX Constraints

## Fermentation Lifecycle In The UI

A fermentation is the central production entity. The UI should expect it to have:

- a status lifecycle such as `ACTIVE`, `SLOW`, `STUCK`, `COMPLETED`
- multiple samples over time
- optional protocol execution tracking
- user-recorded actions
- protocol alerts
- one or more analyses

This means detail screens should be designed around a timeline of related data, not a flat record.

## Protocol System Language

Use these terms consistently:

- **Protocol**: a reusable template or recipe
- **ProtocolExecution**: a specific protocol being run for one fermentation
- **StepCompletion**: evidence that a step was completed
- **ProtocolAlert**: a deviation, overdue step, or issue raised by execution logic

## Analysis Engine Language

Analysis results can include:

- anomalies
- recommendations
- advisories

Keep these separate in the UI. A recommendation is not the same thing as an advisory.

## Polling Constraint

No WebSockets currently exist.

Use polling where live monitoring matters, especially for:

- fermentation lists or active status views
- latest sample display
- active execution alert counts

Stop or reduce polling when the entity is no longer active, especially for completed fermentations.

## Alert Lifecycle Constraint

Two distinct actions exist and should not be collapsed into one button:

- acknowledge: marks the alert as seen while keeping it in the list
- dismiss: removes it from the active list after the user acts on it

Any alert UI must preserve that semantic distinction.

## Multi-Tenancy Constraint

The frontend should assume winery scoping is automatic for most standard flows.

Do not design the normal UI around manually choosing or injecting `winery_id` into every write request.

## Historical Data Constraint

Historical fermentation endpoints use a different auth/scoping pattern through `X-Winery-ID`.

Treat historical views as a special integration path, not as identical to the main authenticated CRUD flows.

## Screen Planning Inputs

Useful screen families implied by the backend surface include:

- dashboard / active fermentations overview
- fermentation list and detail
- sample recording and sample history
- protocol template management
- protocol execution tracking
- alerts and actions
- analysis detail and recommendation workflows
- vineyard and harvest lot management
- admin winery management

These are planning inputs, not proof that all screens already exist in the frontend.

## Design Constraints

1. mobile-first matters because winemakers may use the UI in the field
2. role-based UI matters because admin and winemaker actions diverge
3. connectivity may be imperfect, so optimistic or resilient UI is valuable where safe
4. data-heavy screens should be organized around trends, status, and chronology rather than single-form CRUD only