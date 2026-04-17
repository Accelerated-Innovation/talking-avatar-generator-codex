# Non-Functional Requirements

## Feature
Talking Avatar Generation

## Scope
These non-functional requirements apply to the workshop slice for a web application that accepts a portrait image and short script, creates a talking avatar generation job, tracks processing status, and displays the completed generated video using a mock avatar provider.

## Assumptions
- The first implementation uses a mock avatar provider.
- The application is intended for local workshop use, not production deployment.
- The application supports one portrait image and one generated clip per avatar job.
- Authentication and authorization are out of scope for this workshop slice.
- Recent jobs, retry behavior, and provider switching are out of scope for the core slice.

## Usability

### NFR-U1
The submission page shall present the required inputs for image upload, script entry, and voice selection on a single page.

### NFR-U2
The application shall display validation messages on the same page as the submission form.

### NFR-U3
The application shall display validation messages close to the relevant input when possible.

### NFR-U4
The avatar job detail page shall display the current status, submitted script, selected voice, and original image in a clear and readable layout.

### NFR-U5
The application shall use status labels limited to `pending`, `processing`, `complete`, and `failed`.

## Performance

### NFR-P1
In the local workshop environment, the submission request shall return a response within 2 seconds for valid requests, excluding simulated provider completion time.

### NFR-P2
In the local workshop environment, the avatar job status endpoint shall return a response within 1 second under normal workshop usage.

### NFR-P3
The initial submission page shall render within 2 seconds after the application is ready.

## Reliability

### NFR-R1
The application shall not create an avatar job when submission validation fails.

### NFR-R2
The application shall preserve avatar job status and metadata after page refresh.

### NFR-R3
If avatar generation fails, the application shall set the avatar job status to `failed` and retain the failure reason.

### NFR-R4
If avatar generation succeeds, the application shall set the avatar job status to `complete` and retain the generated video path.

### NFR-R5
The application shall return a not found response for unknown avatar job identifiers.

## Maintainability

### NFR-M1
Routing logic, validation logic, persistence logic, and avatar provider logic shall be separated into distinct modules or services.

### NFR-M2
The application shall define business rules for file validation and script validation in a centralized location.

### NFR-M3
The application shall isolate avatar generation behind a provider service abstraction so the mock provider can be replaced later without major route changes.

### NFR-M4
The application shall use typed Python models and schemas for request handling and domain data.


## Security

### NFR-S1
The application shall accept only `jpg`, `jpeg`, and `png` image uploads.

### NFR-S2
The application shall reject image uploads larger than 5 MB.

### NFR-S3
The application shall reject submissions with scripts longer than 300 characters.

### NFR-S4
The application shall generate stored file names independently of user-supplied file names.

### NFR-S5
The application shall validate uploaded files by both declared type and file content checks that are feasible for the workshop stack.

### NFR-S6
The application shall safely render submitted content in templates without unsafe HTML execution.

## Observability

### NFR-O1
The application shall log avatar job creation events with job identifier and timestamp.

### NFR-O2
The application shall log avatar job status transitions with job identifier, prior status, new status, and timestamp.

### NFR-O3
The application shall log avatar provider failures with job identifier, failure reason, and timestamp.

### NFR-O4
The application shall log validation failures with enough detail for debugging without storing unnecessary sensitive content.

## Data Integrity

### NFR-D1
Each avatar job shall have a unique identifier.

### NFR-D2
Each avatar job shall persist the submitted script, selected voice, current status, and image reference.

### NFR-D3
A generated video path shall only be stored for avatar jobs with status `complete`.

### NFR-D4
A provider error message shall only be stored for avatar jobs with status `failed`.

## Testability

### NFR-T1
The application shall support automated tests for validation rules, avatar job lifecycle, and job detail behavior.

### NFR-T2
The mock avatar provider shall support deterministic success and failure behavior for automated tests.

### NFR-T3
The core happy path and core validation failures shall be traceable to acceptance scenarios in `acceptance.feature`.

## Out of Scope
The following are explicitly out of scope for this workshop slice:
- real-time conversational avatars
- voice cloning
- webcam capture
- authentication and authorization
- video editing
- multi-scene output
- recent jobs history in the core slice
- retrying failed jobs
- production-grade deployment and scaling concerns