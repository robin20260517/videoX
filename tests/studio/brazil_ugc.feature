Feature: Single-photo fifteen-second Brazil UGC
  Scenario: One supplied actor and scene
    Given one uploaded actor image and one scene reference
    And a video theme and configured multimodal director
    When the user requests a draft
    Then dialogue is written in Brazilian Portuguese from the theme
    And ambient sound, background movement, actor action and camera framing derive from the scene
    And the timeline covers a single uninterrupted 15 seconds

  Scenario: Optional fixed game screen
    Given a supplied game image
    When the approved draft is submitted
    Then reference images are ordered actor, scene, game
    And only the game reference may control the phone screen
    And the provider receives one 15-second 9:16 generation

  Scenario: Repeated generate click
    Given an approved draft
    When two generation requests arrive together
    Then only one paid provider submission is permitted

  Scenario: Unknown submission result
    Given a provider POST times out after submission
    When the user reopens the studio
    Then the task is marked submission_unknown
    And no automatic paid retry occurs

  Scenario: Restore known provider task
    Given a saved provider task id
    When the local server restarts
    Then it resumes querying that task
    And successful output is saved locally

  Scenario: Missing credentials
    Given the director credential is not configured
    When a user requests a draft
    Then the missing configuration is shown
    And no fabricated draft is created
