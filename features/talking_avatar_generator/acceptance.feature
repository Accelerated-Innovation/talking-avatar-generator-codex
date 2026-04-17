Feature: Talking Avatar Generation
  As a business user
  I want to upload a portrait image and enter a short script
  So that I can generate and view a talking avatar clip

  Background:
    Given the Talking Avatar Generation application is available
    And the default voice is "Default Voice"
    And the maximum script length is 300 characters
    And supported image types are jpg, jpeg, and png
    And the maximum image size is 5 MB

  @happy-path @nfr-performance @nfr-reliability
  Scenario: Submit a valid avatar generation request with the default voice
    Given I am on the avatar submission page
    When I upload a valid png portrait image
    And I enter a script that is 300 characters or fewer
    And I submit the avatar generation request
    Then the system should accept the request
    And the system should create a new avatar job
    And the avatar job should use the default voice
    And the avatar job status should be "pending"

  @happy-path @nfr-reliability
  Scenario: Create an avatar job only after validation passes
    Given I am on the avatar submission page
    When I upload a valid jpg portrait image
    And I enter a valid script
    And I submit the avatar generation request
    Then the system should create a unique avatar job identifier
    And the system should store the submitted image reference
    And the system should store the submitted script
    And the system should store the selected voice
    And the avatar job status should be "pending"

  @happy-path @nfr-reliability @nfr-observability
  Scenario: Move an avatar job from pending to processing to complete
    Given an avatar job exists with status "pending"
    And the mock avatar provider is configured to succeed
    When avatar generation processing starts for the job
    Then the avatar job status should change to "processing"
    When avatar generation processing completes successfully
    Then the avatar job status should change to "complete"
    And the avatar job should store a generated video path

  @happy-path @nfr-performance
  Scenario: View a completed avatar result
    Given an avatar job exists with status "complete"
    And the avatar job has a generated video path
    When I open the avatar job detail page
    Then I should see the original portrait image
    And I should see the submitted script
    And I should see the selected voice
    And I should see the generated avatar video

  @error @nfr-reliability
  Scenario: Reject a submission when no image is provided
    Given I am on the avatar submission page
    When I enter a valid script
    And I submit the avatar generation request without an image
    Then the system should reject the request
    And I should see a validation message for the missing image
    And no avatar job should be created

  @error @nfr-security
  Scenario: Reject a submission when the image type is not supported
    Given I am on the avatar submission page
    When I upload a portrait image with an unsupported file type
    And I enter a valid script
    And I submit the avatar generation request
    Then the system should reject the request
    And I should see a validation message for unsupported image type
    And no avatar job should be created

  @error @nfr-security
  Scenario: Reject a submission when the image exceeds the maximum size
    Given I am on the avatar submission page
    When I upload a portrait image larger than 5 MB
    And I enter a valid script
    And I submit the avatar generation request
    Then the system should reject the request
    And I should see a validation message for image size
    And no avatar job should be created

  @error @nfr-reliability
  Scenario: Reject a submission when no script is provided
    Given I am on the avatar submission page
    When I upload a valid jpeg portrait image
    And I submit the avatar generation request without a script
    Then the system should reject the request
    And I should see a validation message for the missing script
    And no avatar job should be created

  @error @nfr-security
  Scenario: Reject a submission when the script exceeds the maximum length
    Given I am on the avatar submission page
    When I upload a valid png portrait image
    And I enter a script longer than 300 characters
    And I submit the avatar generation request
    Then the system should reject the request
    And I should see a validation message for script length
    And no avatar job should be created

  @edge-case @nfr-performance @nfr-reliability
  Scenario: Show processing status while avatar generation is in progress
    Given an avatar job exists with status "processing"
    When I open the avatar job detail page
    Then I should see the avatar job status as "processing"
    And I should not see a generated avatar video yet

  @error @nfr-reliability @nfr-observability
  Scenario: Show failed status when avatar generation fails
    Given an avatar job exists with status "pending"
    And the mock avatar provider is configured to fail
    When avatar generation processing starts for the job
    And avatar generation processing fails
    Then the avatar job status should change to "failed"
    And the avatar job should store a provider error message

  @error @nfr-reliability
  Scenario: Return not found when the user requests an unknown avatar job
    Given no avatar job exists for the requested identifier
    When I request the avatar job detail page
    Then the system should return not found

  @happy-path @nfr-performance
  Scenario: Display submission details for a completed avatar job
    Given an avatar job exists with status "complete"
    When I open the avatar job detail page
    Then I should see the avatar job identifier
    And I should see the submitted script
    And I should see the selected voice
    And I should see the current avatar job status

  @edge-case @nfr-reliability
  Scenario: Do not display a generated video when the avatar job is not complete
    Given an avatar job exists with status "pending"
    When I open the avatar job detail page
    Then I should not see a generated avatar video
