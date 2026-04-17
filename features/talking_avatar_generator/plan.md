# Feature Plan: talking_avatar_generator

---

## Objective

- Deliver a workshop web flow where a business user can upload a portrait image, enter a short script, submit a talking-avatar request, and later view job status or a completed generated clip.
- Provide a governed first slice that demonstrates Hexagonal Architecture with deterministic processing, file-validation rules, persistent job state, and a swappable mock provider.
- Meet the measurable success criteria defined in `features/talking_avatar_generator/acceptance.feature` and `features/talking_avatar_generator/nfrs.md`, including response-time targets, validation guarantees, deterministic tests, and threshold-passing FIRST/Virtue predictions.

---

## Scope Boundaries

### In scope
- Portrait image upload, script entry, and default-voice selection on a single submission page
- Validation for required image/script inputs, supported file types, file size, and maximum script length
- Pending job creation with persisted metadata and generated internal asset names
- Deterministic mock-provider processing for success and failure outcomes
- Job detail/status display for `pending`, `processing`, `complete`, and `failed`
- Structured logging for creation, lifecycle transitions, provider failures, and validation failures
- Automated unit, BDD integration, and API contract tests for the governed workshop slice

### Out of scope
- Real avatar providers, voice cloning, webcam capture, retries, and recent-job history
- Authentication and authorization workflows
- Multi-scene output, video editing, and production-grade deployment/scaling concerns
- Shared contract publication for downstream services or agents

### Assumptions
- The first implementation uses FastAPI + Jinja2 + SQLite + SQLAlchemy from the approved stack
- Local filesystem storage is sufficient for workshop assets
- The mock provider exposes deterministic success/failure controls for tests and local runs
- Public routes are acceptable for the workshop slice as long as upload validation and sanitized logging are enforced

---

## Architecture Alignment

### Relevant contracts
- docs/backend/architecture/ARCH_CONTRACT.md: Sections 1-3, 5, 7-9 require Hexagonal Architecture, strict boundaries, new-port ADR coverage, secure adapter-level concerns, and automated testing
- docs/backend/architecture/BOUNDARIES.md: Sections 2-4 require `api/` to call inbound ports only, services to own orchestration, and adapters to remain infrastructure-only
- docs/backend/architecture/API_CONVENTIONS.md: Sections 0-4 and 6-8 require thin FastAPI handlers, versioned routes, response envelopes, centralized error mapping, observability, and route tests
- docs/backend/architecture/SECURITY_AUTH_PATTERNS.md: Sections 3-4 and 8 require public-route declaration, adapter-level input handling, and no raw token or framework leakage into the domain
- docs/backend/evaluation/eval_criteria.md: Sections 1-4 and 7 require FIRST-compliant tests, 7 Virtue thresholds >= 4, and deterministic feature-level eval configuration

### ADRs

- New ADRs required:
  - ADR-002: Talking Avatar Generation Ports, Persistence, and Mock Provider Boundaries - Accepted
- Existing ADRs referenced:
  - none

### Interfaces and dependencies

- Inbound ports:
  - `AvatarSubmissionPort`
  - `AvatarJobQueryPort`
  - `AvatarProcessingPort`
- Domain services:
  - `AvatarGenerationService`
  - `AvatarJobQueryService`
  - Validation/value-object module for file and script rules
- Outbound ports:
  - `AvatarJobRepositoryPort`
  - `AvatarProviderPort`
  - `AvatarAssetStoragePort`
  - `ObservabilityPort`
  - `Clock`
- Adapters:
  - FastAPI + Jinja2 inbound handlers
  - SQLite/SQLAlchemy repository adapter
  - Local filesystem asset storage adapter
  - Deterministic mock avatar provider adapter
  - Structured logging / observability adapter
- Data stores/events touched:
  - SQLite job store
  - Local asset directory for uploaded portraits and generated videos
  - Structured application logs for lifecycle events
- External dependencies:
  - FastAPI
  - Jinja2
  - SQLAlchemy
  - SQLite
  - Pillow
  - python-multipart
  - pytest, pytest-bdd, pytest-mock

### Shared contract artifacts

Artifacts produced by this feature that other features, services, or agents will consume.

- Shared artifacts produced: none
- Artifact type(s): n/a
- Downstream consumers: none
- Versioning strategy: n/a
- Breaking change policy: n/a
- ADR reference (if required): n/a

### Security and compliance

- AuthN/AuthZ considerations:
  - Routes are public for the workshop slice; no JWT/RBAC flow is introduced by this feature
- Data classification and PII handling:
  - Uploaded portraits and user-entered scripts are user-provided content and must not be logged verbatim
- Threats and mitigations:
  - Unsupported or spoofed files -> validate extension and feasible content signature checks
  - Oversized uploads -> reject before job creation
  - Path traversal / unsafe filenames -> generate internal asset names independently of user filenames
  - Unsafe rendering -> rely on template escaping and avoid unsafe HTML execution
  - Overexposed errors -> map domain failures to sanitized response envelopes only

---

## Evaluation Compliance Summary (MANDATORY)

Predicted BEFORE implementation begins. All score and evidence fields must be populated - null values are not permitted at plan finalization.

```yaml
evaluation_prediction:
  first:
    fast:           { score: 4.0, evidence: "Unit tests will isolate services with mocked repository/provider/storage dependencies and avoid real network calls." }
    isolated:       { score: 4.0, evidence: "Dependency injection, temporary storage fixtures, and explicit fakes keep tests independent of shared mutable state." }
    repeatable:     { score: 4.0, evidence: "Deterministic mock-provider outcomes, injected clocks, and controlled temporary paths make test runs reproducible." }
    self_verifying: { score: 5.0, evidence: "BDD, unit, and contract tests assert explicit status, payload, and error outcomes without manual inspection." }
    timely:         { score: 4.0, evidence: "Tests are planned increment-by-increment alongside implementation, preserving the red-green-refactor loop." }
    average: 4.2
  virtues:
    working:   { score: 4.0, evidence: "The design covers all tagged scenarios, validation failures, lifecycle states, and not-found handling." }
    unique:    { score: 4.0, evidence: "Centralized validation and lifecycle services reduce the risk of duplicate rule logic across routes and adapters." }
    simple:    { score: 4.0, evidence: "Separating submission, processing, and query concerns limits branching and keeps each service focused." }
    clear:     { score: 4.0, evidence: "Feature-specific ports and status-oriented models keep route, service, and adapter responsibilities understandable." }
    easy:      { score: 4.0, evidence: "Mock provider, storage, and repository seams create clear extension points for future provider replacement." }
    developed: { score: 5.0, evidence: "The plan includes unit, BDD integration, and contract tests for every architectural slice that changes." }
    brief:     { score: 4.0, evidence: "The design introduces only the abstractions required for this feature and avoids speculative production-only infrastructure." }
    average: 4.1
  thresholds_met: true
```

### Refactor Triggers Identified

- Structural complexity risks:
  - Status-transition handling could become too branch-heavy if success/failure logic and detail-page rules live in one service
- Duplication risks:
  - Validation logic could be repeated between multipart request parsing, service rules, and adapter checks
- Boundary risks:
  - Routes may be tempted to access repository/storage/provider adapters directly for convenience
- Test fragility risks:
  - Processing tests could become timing-sensitive if lifecycle progression is simulated with sleeps instead of deterministic controls

If `thresholds_met` is false or any average is below 4.0, this plan must be revised before implementation begins.

---

## Implementation Checklist

### Feature Summary

- Business goal:
  - Let a business user submit a portrait and short script, create a talking-avatar job, and later view processing status or a finished generated clip.
- User value:
  - The workshop user gets an end-to-end talking-avatar flow without waiting on a real provider integration.
- Success criteria:
  - All tagged acceptance scenarios pass, NFR validation and lifecycle guarantees are met, and the feature clears FIRST and 7 Virtue thresholds defined in `eval_criteria.yaml`.

### Architecture Mapping

- Inbound ports:
  - `AvatarSubmissionPort` for request intake and pending-job creation
  - `AvatarProcessingPort` for deterministic lifecycle progression
  - `AvatarJobQueryPort` for status/detail retrieval
- Domain services:
  - `AvatarGenerationService`
  - `AvatarJobQueryService`
  - Validation/value-object helpers for file and script rules
- Outbound ports:
  - `AvatarJobRepositoryPort`
  - `AvatarProviderPort`
  - `AvatarAssetStoragePort`
  - `ObservabilityPort`
  - `Clock`
- Adapters:
  - FastAPI + Jinja2 route modules
  - SQLite/SQLAlchemy repository adapter
  - Local filesystem asset storage adapter
  - Deterministic mock provider adapter
  - Observability adapter and centralized exception handler
- API routes:
  - `v1` avatar submission route
  - `v1` avatar job detail route
- Boundary confirmation:
  - No boundary violations are planned; `api/` stays inbound-only, services own orchestration, and infrastructure concerns remain behind outbound ports per `ARCH_CONTRACT.md` and `BOUNDARIES.md`.

### Task Breakdown (Ordered Checklist)

1. Define the domain models, status enum/value objects, and validation rule helpers for avatar jobs, submission inputs, and status-dependent media fields.
   Files/modules touched:
   `services/` domain models module, validation/value-object module, shared typing module if needed.
   Driven by:
   `nfrs.md` NFR-M2, NFR-M4, NFR-D1 to NFR-D4; `CROSS_CUTTING_CONCERNS.md` Sections 1-2.
   Code Virtue at risk:
   `clear`, `unique`.
   ADR required flag:
   no, covered by ADR-002.

2. Define inbound and outbound port interfaces for submission, processing, query, repository, provider, storage, observability, and clock dependencies.
   Files/modules touched:
   `ports/inbound/`, `ports/outbound/`.
   Driven by:
   `ARCH_CONTRACT.md` Sections 2-3, `BOUNDARIES.md` Sections 2-4, ADR-002.
   Code Virtue at risk:
   `easy`, `brief`.
   ADR required flag:
   no, covered by accepted ADR-002.

3. Write unit tests first for validation behavior and pending-job creation using fakes/mocks for repository, storage, observability, and clock dependencies.
   Files/modules touched:
   `tests/unit/` for validation/service tests.
   Driven by:
   acceptance scenarios for valid submission and validation failures; `TESTING.md` Sections 2-4.
   FIRST principle supported:
   `fast`, `isolated`, `repeatable`, `self_verifying`, `timely`.
   Code Virtue at risk:
   `working`.
   ADR required flag:
   no.

4. Implement the submission service and submission route wiring, including multipart mapping, generated filenames, and pending-job persistence.
   Files/modules touched:
   `services/`, `api/`, repository/storage adapters, composition root wiring.
   Driven by:
   acceptance submission scenarios; NFR-R1, NFR-S1 to NFR-S5, NFR-D1 to NFR-D2; `API_CONVENTIONS.md`.
   Code Virtue at risk:
   `simple`, `clear`.
   ADR required flag:
   no.

5. Add BDD integration tests and route contract tests for submission success and validation failures.
   Files/modules touched:
   `tests/bdd/`, `tests/integration/`, `tests/contract/`.
   Driven by:
   tagged scenarios for submission and validation failures; `TESTING.md` Sections 2, 6, 7.
   FIRST principle supported:
   `self_verifying`, `timely`.
   Code Virtue at risk:
   `developed`.
   ADR required flag:
   no.

6. Write unit tests first for lifecycle transitions and terminal-state persistence rules using deterministic provider outcomes.
   Files/modules touched:
   `tests/unit/` lifecycle/service/provider-contract tests.
   Driven by:
   processing success/failure scenarios; NFR-R3, NFR-R4, NFR-O2, NFR-O3, NFR-D3, NFR-D4.
   FIRST principle supported:
   `fast`, `repeatable`, `timely`.
   Code Virtue at risk:
   `working`, `simple`.
   ADR required flag:
   no.

7. Implement processing logic, deterministic mock provider adapter, repository state updates, and observability calls for lifecycle transitions and failures.
   Files/modules touched:
   `services/`, `adapters/`, `ports/outbound/` implementations, composition root wiring.
   Driven by:
   lifecycle scenarios and ADR-002 boundary placement.
   Code Virtue at risk:
   `simple`, `easy`, `unique`.
   ADR required flag:
   no.

8. Add BDD and contract coverage for processing success/failure behavior and provider-port expectations.
   Files/modules touched:
   `tests/bdd/`, `tests/contract/`, `tests/integration/`.
   Driven by:
   processing scenarios; `TESTING.md` Sections 2 and 6.
   FIRST principle supported:
   `self_verifying`, `repeatable`.
   Code Virtue at risk:
   `developed`.
   ADR required flag:
   no.

9. Write unit tests first for detail-query shaping, pending/no-video behavior, and unknown-job translation.
   Files/modules touched:
   `tests/unit/`.
   Driven by:
   detail and not-found scenarios; NFR-R2, NFR-R5, NFR-U4, NFR-U5.
   FIRST principle supported:
   `isolated`, `self_verifying`, `timely`.
   Code Virtue at risk:
   `clear`.
   ADR required flag:
   no.

10. Implement the query service, detail route, templates, centralized error mapping, and OpenAPI metadata for final route contracts.
    Files/modules touched:
    `services/`, `api/`, templates, exception handling modules, route metadata.
    Driven by:
    detail scenarios; `API_CONVENTIONS.md`, `ERROR_MAPPING.md`, NFR-S6, NFR-P2, NFR-P3.
    Code Virtue at risk:
    `clear`, `brief`.
    ADR required flag:
    no.

11. Add BDD integration and contract tests for detail rendering, not-found behavior, response envelopes, and documented status codes.
    Files/modules touched:
    `tests/bdd/`, `tests/integration/`, `tests/contract/`.
    Driven by:
    remaining detail scenarios and `API_CONVENTIONS.md` Section 8.
    FIRST principle supported:
    `self_verifying`, `timely`.
    Code Virtue at risk:
    `developed`.
    ADR required flag:
    no.

12. Run static analysis, architecture-boundary checks, and the full automated test suite after each increment; refactor immediately if duplication, complexity, or test fragility appears.
    Files/modules touched:
    repo-wide quality tooling configuration and affected feature files.
    Driven by:
    `TECH_STACK.md` Section 9, `eval_criteria.md`, `TESTING.md`, AGENTS commit discipline.
    FIRST principle supported:
    `fast`, `repeatable`.
    Code Virtue at risk:
    all virtues, especially `unique` and `simple`.
    ADR required flag:
    no, unless the implementation tries to change an approved boundary.

### Test & Evaluation Plan

- FIRST satisfaction strategy:
  - Use dependency injection everywhere in services.
  - Replace repository, storage, provider, observability, and clock dependencies with fakes/mocks in unit tests.
  - Use temporary directories and isolated SQLite test databases for adapter and integration tests.
  - Avoid sleeps and poll loops; provider behavior must be deterministic and directly triggered in tests.
- Simplicity and duplication risks:
  - Validation logic is the highest duplication risk and should remain centralized.
  - Processing transitions are the highest complexity risk and should remain in a small service surface with explicit states.
  - Detail-page shaping should remain separate from submission/processing orchestration.
- LLM evaluation dimensions from `eval_criteria.yaml`:
  - None. The feature is deterministic.
- CI gate expectations:
  - Unit tests, BDD integration tests, and contract tests must pass.
  - FIRST average must remain >= 4 with no individual score below 3.
  - Virtue average must remain >= 4 with no individual score below 3.
  - Static analysis and architecture boundary checks must pass before moving to the next increment.

### Evaluation Compliance Summary

- Expected FIRST average score:
  - 4.2, because the design relies on isolated dependencies, deterministic provider outcomes, and explicit assertions across unit, BDD, and contract suites.
- Expected 7 Virtue average score:
  - 4.1, because the accepted ADR keeps responsibilities separated and the increments are scoped to limit duplication and structural complexity.
- Identified refactor triggers likely to occur:
  - Validation rules duplicated across API and services
  - Status transition branching growing beyond a focused service
  - Template/detail logic leaking into routes
  - Tests becoming timing-sensitive or environment-coupled
- Threshold confirmation:
  - `features/talking_avatar_generator/eval_criteria.yaml` thresholds are satisfied by design.

### Refactor Triggers

- Refactor immediately if duplicate validation or lifecycle logic appears across routes, services, or adapters.
- Refactor immediately if service methods exceed simple status transitions and begin accumulating deep branching or mutable state.
- Refactor immediately if any FIRST or Virtue score is predicted or observed below the required threshold.
- Refactor immediately if tests require ordering, sleep-based timing, or shared mutable fixtures.

### Risks & Unknowns

- Missing constraints:
  - The exact filesystem layout for local asset storage still needs to be chosen during implementation.
- Integration risks:
  - Multipart upload handling plus file-content validation can drift between API parsing and domain rules if the boundary is not kept clean.
- Performance concerns:
  - Local image validation and persistence must still satisfy NFR-P1 to NFR-P3 without introducing unnecessary I/O in the request path.
- Security implications:
  - Public upload routes require careful filename generation, content validation, and sanitized logging.

---

## Increments

### Increment 1: Submission and Validation

**Goal**
- Accept valid submissions, reject invalid inputs, and persist a new `pending` avatar job with sanitized asset naming.

**Deliverables**
- Submission request/response models and route wiring for the avatar submission page
- `AvatarSubmissionPort` and `AvatarGenerationService` submission behavior
- File and script validation policy/value objects
- Repository and asset-storage outbound port definitions
- Initial SQLite repository + local storage adapters sufficient for pending-job creation

**Implementation notes**
- Map Gherkin scenarios:
  - `Submit a valid avatar generation request with the default voice`
  - `Create an avatar job only after validation passes`
  - `Reject a submission when no image is provided`
  - `Reject a submission when the image type is not supported`
  - `Reject a submission when the image exceeds the maximum size`
  - `Reject a submission when no script is provided`
  - `Reject a submission when the script exceeds the maximum length`
- Keep original filenames out of persisted asset identifiers.
- Keep validation rules centralized in service/value-object code, not in route handlers.

**Architecture impact**
- Ports affected:
  - `AvatarSubmissionPort`
  - `AvatarJobRepositoryPort`
  - `AvatarAssetStoragePort`
  - `ObservabilityPort`
- Adapters affected:
  - submission route handler
  - SQLite repository adapter
  - local asset storage adapter
  - logging adapter
- Boundary risks:
  - multipart parsing and validation responsibilities could blur without strict mapping at the API boundary

**Tests**
- Unit (FIRST compliant):
  - validation-rule tests for required file/script, max size, supported types, script length, generated filenames
  - service tests for pending-job creation and no-create-on-validation-failure
- Integration:
  - BDD tests for submission happy path and validation failures using FastAPI test clients
- Contract:
  - submission route contract for status codes, response envelope, and error payload shape

**Evaluation impact**
- LLM eval required? (yes/no)
  - no
- Criteria names impacted:
  - FIRST fast, isolated, repeatable, self_verifying, timely
  - Virtues working, unique, simple, clear, easy, developed, brief
- Threshold impact:
  - Centralized validation is the main control for keeping `unique`, `simple`, and `clear` above threshold
- Eval dataset reference:
  - n/a

**Definition of Done**
- Valid submission creates one `pending` job with persisted metadata and internal asset names
- Invalid submission paths return validation feedback and create no job
- Submission route contract tests pass

---

### Increment 2: Processing Lifecycle and Provider Failure Handling

**Goal**
- Advance jobs through deterministic mock-provider processing, including success and failure outcomes with persisted lifecycle state.

**Deliverables**
- `AvatarProcessingPort` and lifecycle behavior in `AvatarGenerationService`
- `AvatarProviderPort` contract and deterministic mock provider adapter
- Repository update behavior for `processing`, `complete`, and `failed`
- Observability calls for creation, status transitions, and provider failures
- Clock usage for timestamped lifecycle events where needed

**Implementation notes**
- Map Gherkin scenarios:
  - `Move an avatar job from pending to processing to complete`
  - `Show failed status when avatar generation fails`
- Keep provider-specific behavior behind the port boundary; the service should own state transition rules.
- Preserve NFR-D3 and NFR-D4 by storing generated video paths only for `complete` jobs and provider error messages only for `failed` jobs.

**Architecture impact**
- Ports affected:
  - `AvatarProcessingPort`
  - `AvatarProviderPort`
  - `AvatarJobRepositoryPort`
  - `ObservabilityPort`
  - `Clock`
- Adapters affected:
  - mock avatar provider adapter
  - repository update adapter logic
  - observability adapter
- Boundary risks:
  - status-transition rules could leak into the provider adapter if the service boundary is not preserved

**Tests**
- Unit (FIRST compliant):
  - lifecycle transition tests for pending -> processing -> complete and pending -> failed
  - service tests ensuring video path and error message are stored only in valid terminal states
- Integration:
  - BDD tests for success and failure processing flows
- Contract:
  - provider-port behavior tests using deterministic fake implementations

**Evaluation impact**
- LLM eval required? (yes/no)
  - no
- Criteria names impacted:
  - FIRST fast, repeatable
  - Virtues working, simple, easy, developed
- Threshold impact:
  - Deterministic provider controls are the main control for preserving `fast` and `repeatable`
- Eval dataset reference:
  - n/a

**Definition of Done**
- Jobs move through valid lifecycle states only
- Successful processing stores a generated video path
- Failed processing stores a provider failure reason and no generated video path
- Lifecycle observability hooks are exercised by tests

---

### Increment 3: Job Detail, Error Mapping, and Contract Hardening

**Goal**
- Expose the avatar job detail experience and finalize route-level contracts, observability coverage, and not-found handling.

**Deliverables**
- `AvatarJobQueryPort` and detail-query service behavior
- Detail/status route and Jinja2 rendering for pending, processing, complete, and failed views
- Centralized domain-error mapping for validation and not-found outcomes
- OpenAPI metadata and response-envelope coverage for introduced routes
- Final contract-test and BDD coverage for detail-page and error scenarios

**Implementation notes**
- Map Gherkin scenarios:
  - `View a completed avatar result`
  - `Show processing status while avatar generation is in progress`
  - `Return not found when the user requests an unknown avatar job`
  - `Display submission details for a completed avatar job`
  - `Do not display a generated video when the avatar job is not complete`
- Keep detail-page shaping in the query service so the route remains a thin adapter.
- Verify status-dependent rendering rules do not bypass the standardized error and response model.

**Architecture impact**
- Ports affected:
  - `AvatarJobQueryPort`
  - `AvatarJobRepositoryPort`
  - `ObservabilityPort`
- Adapters affected:
  - detail route handler
  - Jinja templates
  - centralized exception handler
  - OpenAPI route metadata
- Boundary risks:
  - query shaping and template concerns could become coupled if route handlers overreach

**Tests**
- Unit (FIRST compliant):
  - query-service tests for status-dependent detail shaping and not-found translation
- Integration:
  - BDD tests for completed, processing, pending/no-video, and unknown-job detail views
- Contract:
  - detail route contract for response envelope, not-found error shape, and OpenAPI-documented status codes

**Evaluation impact**
- LLM eval required? (yes/no)
  - no
- Criteria names impacted:
  - FIRST self_verifying, timely
  - Virtues clear, developed, brief
- Threshold impact:
  - Detail-query separation is the main control for preserving `clear` and `brief`
- Eval dataset reference:
  - n/a

**Definition of Done**
- Detail route renders the correct status-dependent information for pending, processing, complete, and failed jobs
- Unknown job requests return the standardized not-found response
- Route contracts, OpenAPI docs, and observability coverage are aligned with the architecture contracts

---

## Risks

- Risk:
  - Multipart upload validation may become split across route parsing and service logic
  - Impact:
    - Duplicate rules and lower `unique` / `clear` scores
  - Mitigation:
    - Keep route validation limited to schema concerns and centralize business rules in services/value objects

- Risk:
  - The workshop feature could be over-engineered with too many abstractions for its size
  - Impact:
    - Slower delivery and reduced `brief` score
  - Mitigation:
    - Keep ports narrow, feature-specific, and limited to proven responsibilities only

- Risk:
  - Deterministic processing tests may drift into timing-based implementations
  - Impact:
    - Flaky CI and reduced FIRST repeatability
  - Mitigation:
    - Use explicit provider outcome controls and injected clocks instead of sleeps or polling loops

- Risk:
  - Public upload endpoints increase input-handling risk
  - Impact:
    - Security regressions through unsafe filenames, invalid files, or verbose logs
  - Mitigation:
    - Enforce extension/content checks, generated filenames, and sanitized logging in adapters and services

---

## Definition of Done (Feature-Level)

- Acceptance criteria satisfied (`acceptance.feature`)
- NFRs satisfied (`nfrs.md`)
- Evaluation criteria satisfied (`eval_criteria.yaml`)
- FIRST principles satisfied
- 7 Virtue thresholds satisfied
- CI passes (tests, quality, eval gates)
- No boundary violations
- ADR-002 accepted before implementation proceeds
- PR includes links to plan/spec artifacts
