# ADR-002: Talking Avatar Generation Ports, Persistence, and Mock Provider Boundaries

## Status
Accepted

## Date
2026-04-16

## Authors
- Marty / Feature owner
- Codex / Draft author

---

## 1. Context

The `talking_avatar_generator` feature introduces a workshop web application slice that accepts a portrait image and short script, creates a talking-avatar job, tracks job status, and displays a generated clip using a deterministic mock provider.

Relevant architectural constraints:

- `docs/backend/architecture/ARCH_CONTRACT.md` Section 2 `Layering` requires business logic to remain framework-agnostic and adapter dependencies to stay out of the domain.
- `docs/backend/architecture/ARCH_CONTRACT.md` Section 5 `ADR Rules` requires an ADR when adding a new port or adapter.
- `docs/backend/architecture/BOUNDARIES.md` Sections 2-4 require API handlers to call inbound ports only, services to own orchestration, and adapters to implement infrastructure concerns only.
- `docs/backend/architecture/API_CONVENTIONS.md` requires thin FastAPI handlers, standard response envelopes, centralized error translation, and OpenAPI coverage.
- `docs/backend/architecture/SECURITY_AUTH_PATTERNS.md` and `docs/backend/architecture/CROSS_CUTTING_CONCERNS.md` require public-upload validation, safe rendering, and sanitized logging to stay at the proper boundaries.

This decision addresses the boundary question raised by the feature: where upload validation, avatar job lifecycle orchestration, persistence, asset storage, and deterministic provider behavior should live so the feature stays testable, swappable, and compliant with Hexagonal Architecture.

Reference:
- `features/talking_avatar_generator/plan.md`
- `features/talking_avatar_generator/architecture_preflight.md`
- `features/talking_avatar_generator/acceptance.feature`
- `features/talking_avatar_generator/nfrs.md`

---

## 2. Decision

We will implement the talking avatar generator as a hexagonal feature slice with inbound ports for submission, job query, and processing; domain services that own validation and status transitions; and outbound ports for repository persistence, asset storage, mock avatar generation, clock access, and observability.

FastAPI + Jinja2 handlers will remain thin inbound adapters that translate multipart requests and page queries into domain inputs and invoke inbound ports only. SQLAlchemy/SQLite persistence, local asset storage, and the deterministic mock avatar provider will be isolated in outbound adapters. The mock provider will expose deterministic success and failure behavior for automated tests and will remain swappable without route-level changes.

---

## 3. Architectural Impact

### 3.1 Boundaries
- Layers/services affected:
  - `api/` for submission and detail handlers
  - `ports/inbound/` for avatar submission, query, and processing contracts
  - `ports/outbound/` for repository, provider, asset storage, clock, and observability contracts
  - `services/` for validation and lifecycle orchestration
  - `adapters/` for SQLite persistence, local storage, mock provider, and observability implementations
- Dependency direction changes:
  - None. The decision formalizes new feature-local ports and adapters without changing the repository's allowed dependency rules.
- New modules introduced:
  - `AvatarSubmissionPort`
  - `AvatarJobQueryPort`
  - `AvatarProcessingPort`
  - `AvatarJobRepositoryPort`
  - `AvatarProviderPort`
  - `AvatarAssetStoragePort`
  - `AvatarGenerationService`
  - `AvatarJobQueryService`
  - Feature-specific API route modules and adapter implementations

Confirm:
- No forbidden cross-layer access is introduced.
- Dependency direction complies with `BOUNDARIES.md`.

### 3.2 API Impact
- Route changes:
  - New `v1` submission and job-detail routes for the talking avatar feature
- Versioning impact:
  - New `v1` routes only
- Error model impact:
  - Validation, not-found, and provider failures must map through the centralized domain-error-to-HTTP rules
- OpenAPI updates required:
  - yes

### 3.3 Security Impact
- Auth pattern used:
  - Public workshop routes; authentication remains out of scope for this slice
- Authorization changes:
  - none
- Token handling implications:
  - none
- Data classification considerations:
  - Uploaded portrait images and submitted scripts are user-provided content and must be treated as sensitive input for logging/redaction purposes
- Logging/redaction implications:
  - No raw image bytes, original filenames, or full script content in logs
  - Only sanitized identifiers, statuses, and summarized failure reasons should be emitted

---

## 4. Alternatives Considered

### Option A
- Description:
  - Keep submission validation, persistence, and provider calls directly inside FastAPI route handlers
- Pros:
  - Fewer files and less initial setup
- Cons:
  - Violates thin-adapter expectations
  - Mixes HTTP, validation, storage, and business-state concerns
  - Makes unit testing and provider swapping harder
- Why rejected:
  - It breaks the repository's hexagonal boundary rules and would likely reduce FIRST and Virtue scores

### Option B
- Description:
  - Keep a service layer, but let services depend directly on SQLAlchemy sessions, filesystem paths, and the mock provider implementation
- Pros:
  - Simpler than defining full outbound ports
  - Fewer translation layers in the short term
- Cons:
  - Leaks infrastructure into the domain
  - Makes the mock provider and storage implementation non-swappable
  - Complicates contract tests and future provider replacement
- Why rejected:
  - It violates `ARCH_CONTRACT.md` and `BOUNDARIES.md`, which require abstractions between the domain and infrastructure

---

## 5. Evaluation Impact

This decision affects deterministic evaluation checks and CI enforcement rules.

- Affected criteria from `features/talking_avatar_generator/eval_criteria.yaml`:
  - `unit_tests.enforce_FIRST`
  - `unit_tests.minimum_FIRST_average`
  - `code_quality.enforce_virtues`
  - `code_quality.minimum_virtue_average`
- Changes required:
  - Preserve deterministic adapter boundaries so unit tests stay fast and isolated
  - Add BDD integration tests for the tagged Gherkin scenarios
  - Add contract tests for the new API routes and error envelopes

No LLM evaluation impact.

---

## 6. Risks and Tradeoffs

- Technical risks:
  - The feature introduces several ports and adapters for a small workshop slice, which increases initial setup
- Operational risks:
  - Local asset storage and SQLite paths can drift across environments if composition-root configuration is inconsistent
- Security risks:
  - Public upload handling increases the risk of invalid file input, unsafe filenames, and accidental sensitive logging
- Performance implications:
  - Additional abstraction layers add some implementation overhead, but the design keeps the response-time targets realistic for local workshop usage

Mitigations:

- Keep ports narrow and feature-specific
- Inject configuration centrally via the composition root
- Enforce extension and content validation plus generated filenames
- Use deterministic mock-provider controls and temporary directories/datastores in tests

---

## 7. Plan Alignment

Reference:

- Feature plan increments impacted:
  - Increment 1 for submission, validation, and pending-job creation
  - Increment 2 for deterministic processing and lifecycle transitions
  - Increment 3 for detail retrieval, error mapping, observability, and route contracts
- New increment required?
  - no
- Scope adjustments required?
  - no

If implementation details change the boundary placement defined here, `plan.md` must be updated and this ADR revisited.

---

## 8. Consequences

### Positive
- Keeps validation and lifecycle logic testable and framework-agnostic
- Preserves a clean seam for replacing the mock provider later
- Supports FIRST-compliant tests and contract-focused API verification

### Negative
- Adds more interfaces and wiring than a single-file workshop demo
- Requires careful composition-root setup for repository, storage, and provider adapters

### Neutral
- The workshop slice remains public and local-only; this ADR does not expand auth scope

---

## 9. Follow-Up Actions

- Code changes required:
  - Implement the ports, services, adapters, routes, and tests described in the feature plan
- Documentation updates required:
  - Keep `features/talking_avatar_generator/plan.md` aligned to this ADR
  - Update OpenAPI output when routes are added
- CI updates required:
  - none beyond exercising the existing unit, BDD, contract, lint, and boundary gates
- Security review required:
  - review upload-validation and logging behavior during implementation, even though auth scope is unchanged

---

## 10. Approval

Approved by:
- Architect: accepted on 2026-04-16
- Security (if applicable): pending implementation review for upload handling
- Product (if scope impact): not required
