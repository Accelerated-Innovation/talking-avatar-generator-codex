# Architecture Preflight: talking_avatar_generator

This document validates architectural, security, and evaluation alignment
before implementation begins.

Preflight is required once per feature and must be updated if scope materially changes.

---

## 1. Artifact Review

Feature folder: `features/talking_avatar_generator/`

- acceptance.feature reviewed: yes
- nfrs.md reviewed: yes - no TBD entries: yes
- eval_criteria.yaml exists: yes
- plan.md exists: yes
- Gherkin scenarios cover all populated NFR categories per `docs/backend/architecture/GHERKIN_CONVENTIONS.md`: yes
- `@contract` scenario present (if feature produces shared artifact): n/a

Current status notes:

- Required Gherkin coverage is present for populated `Performance`, `Reliability`, `Security`, and `Observability` categories.
- `features/talking_avatar_generator/eval_criteria.yaml` now matches the deterministic workshop scope.
- `features/talking_avatar_generator/plan.md` must remain aligned to the final ADR and maintain populated evaluation predictions before implementation begins.

---

## 2. Standards Referenced

- `docs/backend/architecture/ARCH_CONTRACT.md`
  - Section 1 `Architectural Style`
  - Section 2 `Layering`
  - Section 3 `Boundaries`
  - Section 5 `ADR Rules`
  - Section 7 `Security`
  - Section 8 `Observability`
  - Section 9 `Testing Policy`
- `docs/backend/architecture/BOUNDARIES.md`
  - Section 1 `Architectural Model`
  - Section 2 `Allowed Dependencies`
  - Section 3 `Communication Rules`
  - Section 4 `Module Isolation`
  - Section 6 `Enforcement`
- `docs/backend/architecture/API_CONVENTIONS.md`
  - Section 0 `Interaction with Domain`
  - Section 1 `Routing`
  - Section 2 `HTTP Verbs & Status Codes`
  - Section 3 `Request & Response Format`
  - Section 4 `Error Handling`
  - Section 6 `Observability`
  - Section 7 `OpenAPI Spec`
  - Section 8 `Testing`
- `docs/backend/architecture/SECURITY_AUTH_PATTERNS.md`
  - Section 3 `Cross-Cutting Security Rules`
  - Section 4 `Identity Propagation`
  - Section 8 `Domain Constraints`
- `docs/backend/architecture/ERROR_MAPPING.md`
  - Section 1 `Principle`
  - Section 3 `HTTP Error Response Shape`
  - Section 4 `API Exception Handler`
  - Section 5 `Rules`
- `docs/backend/architecture/CROSS_CUTTING_CONCERNS.md`
  - Section 1 `Data Transfer Objects (DTOs)`
  - Section 2 `Validation Boundaries`
  - Section 4 `Timestamps and Time Handling`
  - Section 7 `Configuration`
- `docs/backend/architecture/TECH_STACK.md`
  - Section 2 `Architecture Model`
  - Section 3 `API Framework`
  - Section 8 `Testing Stack`
  - Section 9 `Development Tooling`
  - Section 11 `Observability`
  - Section 15 `When an ADR Is Required`
- `docs/backend/architecture/TESTING.md`
  - Section 2 `Test Types`
  - Section 3 `FIRST Principles for Unit Tests`
  - Section 6 `BDD Integration Testing`
  - Section 7 `Hexagonal Architecture Testing`
  - Section 11 `Definition of Done`
- `docs/backend/architecture/GHERKIN_CONVENTIONS.md`
  - Section 2 `Required NFR Tags`
  - Section 3 `Shared Contract Tag`
  - Section 4 `Coverage Rule`
  - Section 7 `Enforcement`
- `docs/backend/evaluation/eval_criteria.md`
  - Section 1 `Unit Test Principles - FIRST`
  - Section 2 `Implementation Quality - 7 Code Virtues`
  - Section 4 `Scoring Model`
  - Section 7 `Feature-Level Eval YAML Schema`

---

## 3. Boundary Analysis

- Inbound ports impacted:
  - Avatar submission use case port for validation, asset intake, and job creation.
  - Avatar job query port for detail-page reads and not-found handling.
  - Avatar processing port for deterministic mock-provider lifecycle progression.
- Domain services impacted:
  - Avatar generation service for submission rules and lifecycle transitions.
  - Avatar job query service for detail shaping and status-dependent rendering data.
  - Central validation policy/value objects for file and script rules.
- Outbound ports impacted:
  - Avatar job repository port for create/read/update persistence.
  - Avatar provider port for the mock generation workflow.
  - Asset storage port for uploaded portraits and generated clip paths.
  - Observability port for creation, status-transition, validation, and provider-failure events.
  - Clock abstraction for timestamped transitions and logs.
- Adapters impacted:
  - FastAPI + Jinja2 inbound adapter(s) for submission and detail routes.
  - SQLAlchemy/SQLite repository adapter.
  - Local filesystem storage adapter.
  - Mock avatar provider adapter with deterministic success/failure behavior.
  - Structured logging / observability adapter.
- Dependency direction:
  - `api/` -> `ports/inbound/`
  - `services/` depends on ports and dependency-light domain/common types only
  - `adapters/` implement outbound ports and may depend on approved infrastructure libraries
- Cross-layer violations introduced: no, if implemented per the cited contracts
- Boundary risks identified:
  - File validation drifting into route handlers instead of centralized service rules.
  - Mock-provider orchestration leaking into adapters rather than staying service-owned.
  - SQLAlchemy, filesystem, Pillow, or FastAPI types leaking into ports or services.
  - Detail-page rendering rules becoming mixed with persistence lookups or provider state handling.
- Mitigations:
  - Keep route handlers thin and port-driven per `API_CONVENTIONS.md` Section 0.
  - Centralize business rules in services and value objects per `CROSS_CUTTING_CONCERNS.md` Section 2.
  - Keep ports interface-only and domain-typed per `BOUNDARIES.md` Sections 2-4.
  - Translate infrastructure errors in adapters and re-raise clean domain errors per `ERROR_MAPPING.md`.

Confirm compliance with `BOUNDARIES.md`:

- The planned feature slice can comply with the repository boundary rules if services remain the orchestration layer and every infrastructure dependency is introduced behind an outbound port.

---

## 4. API Impact

- API changes required: yes
- Routes affected:
  - A `v1` submission route for avatar-job creation.
  - A `v1` detail route for avatar-job retrieval and status display.
- Versioning impact:
  - New `v1` routes only; no existing route migration is implied.
- Request/response structure changes:
  - Submission requires multipart file upload plus typed script and voice fields.
  - Detail retrieval returns a standard response envelope with status, identifiers, and conditional media references.
  - Page-rendering routes must map API-layer models to domain inputs and outputs without leaking framework types into the domain.
- Error model impact:
  - Validation, not-found, and provider-related domain failures must map through the centralized error model in `ERROR_MAPPING.md`.
  - Planning must keep request-schema validation and domain-rule validation distinct so route tests and OpenAPI docs remain consistent.
- OpenAPI updates required: yes

---

## 5. Security Impact

- Auth pattern used:
  - No authenticated workflow is in scope for this workshop slice, so routes are public by design and must be documented as such.
- Authorization enforcement points:
  - None for the current scope.
- Identity propagation impact:
  - No user identity is required, but request correlation identifiers should still be captured at the adapter boundary.
- Token handling implications:
  - None for the current slice.
- Logging/redaction considerations:
  - Do not log raw image bytes, full script bodies, original filenames, or internal exception traces in user-facing responses.
  - Log only sanitized identifiers, status values, validation categories, and provider failure summaries.
- Threat considerations:
  - MIME spoofing and invalid-image uploads.
  - Oversized uploads.
  - Unsafe filename/path handling.
  - Unsafe template rendering of submitted script content.
  - Leaking provider/internal error details to the user.

Security conclusion:

- Security alignment is compliant for planning, provided implementation enforces extension and content validation, generated filenames, template escaping, and sanitized logging.

---

## 6. Evaluation Impact

From `eval_criteria.yaml` and `docs/backend/evaluation/eval_criteria.md`:

- Mode: deterministic
- FIRST enforcement required: yes
- 7 Virtue enforcement required: yes
- LLM criteria affected:
  - None
- Threshold implications:
  - FIRST average must be >= 4 with no individual score below 3.
  - Virtue average must be >= 4 with no individual score below 3.
- CI evaluation gate impact:
  - Unit tests, BDD integration tests, contract tests, static analysis, and FIRST/Virtue thresholds remain binding.
- Refactor risk areas identified:
  - Repeated validation checks between form handling and services.
  - Overgrown status-transition logic in the processing workflow.
  - Fragile tests that depend on timing instead of deterministic provider controls.
  - Mixed UI and domain responsibilities in detail-page shaping.

Evaluation conclusion:

- Evaluation alignment is compliant for planning. The finalized plan must keep populated prediction scores above threshold and preserve deterministic test design.

---

## 7. ADR Determination

ADR required: yes

If yes:
- Proposed title:
  - `ADR-002: Talking Avatar Generation Ports, Persistence, and Mock Provider Boundaries`
- Scope:
  - Introduce the feature's inbound ports, outbound persistence/storage/provider contracts, and the boundary rules for the mock avatar generation workflow.
- Trigger condition:
  - `docs/backend/architecture/ARCH_CONTRACT.md` Section 5 `ADR Rules` requires an ADR when adding a new port or adapter.
  - `docs/backend/architecture/TECH_STACK.md` Section 15 `When an ADR Is Required` also requires ADR coverage for new external dependencies or architectural patterns.
- ADR status:
  - Accepted at `docs/backend/architecture/ADR/ADR-002-talking-avatar-generation-boundaries.md`.

---

## 8. Shared Contract Analysis

Does this feature produce an artifact consumed by other features, services, or agents?

- Produces shared artifact: no
- Artifact type:
  - n/a
- Artifact location (path or registry):
  - n/a
- Downstream consumers identified:
  - none outside the feature's own UI flow
- Versioning strategy:
  - Initial version:
    - n/a
  - Breaking change policy:
    - n/a
- Backward compatibility requirement: no
- Contract validation mechanism:
  - Route contract tests and OpenAPI validation cover the feature's own HTTP surface.
- ADR required for contract ownership: no

No shared contract produced.

---

## 9. Preflight Conclusion

- Architecture alignment: compliant
- Security alignment: compliant
- Evaluation alignment: compliant

Final status:

- Approved for planning

Planning is complete. Implementation may proceed incrementally under `plan.md`, subject to tests, static analysis, and architecture gates passing for each increment.
