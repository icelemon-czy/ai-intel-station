# Papers Capability Specification

### Requirement: List Supported AI Categories
The papers tool SHALL expose the supported AI-related arXiv categories to operators.

#### Scenario: List categories
- **WHEN** the operator runs the command with `--list`
- **THEN** the tool prints the supported category codes and labels

### Requirement: Fetch Latest Papers by Category
The papers tool SHALL fetch the newest papers for each supported requested category.

#### Scenario: Fetch one supported category
- **WHEN** the operator requests `cs.AI` with `--max 10`
- **THEN** the tool requests the newest papers for that category and prepares up to 10 summaries

### Requirement: Save One Markdown File per Paper
Each fetched paper SHALL be written as its own Markdown file containing title, authors, publication metadata, links, and abstract.

#### Scenario: Save fetched papers
- **WHEN** one or more papers are fetched for a category
- **THEN** the tool writes numbered Markdown files under `output/papers/arXiv-<category>/`

### Requirement: Continue Across Category-Level Failures
Failure in one requested category SHALL not prevent processing of other requested categories.

#### Scenario: Mixed category outcome
- **WHEN** one requested category fetch fails and another succeeds
- **THEN** the tool reports the failed category and still writes files for the successful category