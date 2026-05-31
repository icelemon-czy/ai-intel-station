# Research Reporting Delta Spec

## ADDED Requirements

### Requirement: Generate Obsidian-Friendly Briefings

The workspace SHALL generate derived Markdown briefings suitable for reading in Obsidian.

#### Scenario: Generate a time-scoped digest

- **WHEN** the operator requests a digest over a topic or time window
- **THEN** the system generates a Markdown briefing that groups relevant local research items for Obsidian reading

#### Scenario: Generate a thematic reading list

- **WHEN** the operator requests a reading list for a topic or keyword
- **THEN** the system generates a Markdown artifact that organizes matching items into a readable selection for follow-up reading

### Requirement: Allow Partial Briefing Success With Explicit Source Gaps

The reporting layer SHALL allow partial success when some sources are unavailable, while explicitly calling out the missing coverage.

#### Scenario: One source missing during briefing generation

- **WHEN** the system can build a briefing from some sources but one requested source is missing, empty, or unavailable
- **THEN** it still generates the Markdown briefing and includes an explicit note describing the missing source coverage
