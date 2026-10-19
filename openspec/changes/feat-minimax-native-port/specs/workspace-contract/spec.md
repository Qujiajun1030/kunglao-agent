## ADDED Requirements

### Requirement: The analysis workspace SHALL carry an AGENTS.md contract

The workspace template SHALL render `AGENTS.md` instead of `CLAUDE.md`. The rendered
contract SHALL keep the existing content structure — workspace type, the file index, the
persistent loop-enforcement channel, the orchestrator entry point, the state files, and
the evidence rules — and SHALL inject the plugin root through the existing template
variable.

#### Scenario: the workspace contract is written at initialization

- **WHEN** a workspace is initialized
- **THEN** `AGENTS.md` exists at the workspace root, and no `CLAUDE.md` is written

#### Scenario: the injected root points at the active plugin

- **WHEN** the contract is rendered
- **THEN** every script path in the contract resolves under the active plugin root, and
  a stale root from an older install does not appear

#### Scenario: the contract carries the disk-is-truth rule

- **WHEN** the rendered contract is read
- **THEN** it states the post-compaction re-entry rule and the heartbeat staleness rule
  exactly as the previous contract did

### Requirement: The install-reference scanner SHALL target the MiniMax-side carriers

The scanner's carrier list SHALL contain the MiniMax-side workspace carriers — the
workspace contract file and the workspace hook table — and SHALL NOT contain the
retired settings carrier.

#### Scenario: a stale install reference is found in a live carrier

- **WHEN** a workspace carrier references an install root other than the active one
- **THEN** the scanner reports the carrier and the stale span, and the rewriter points
  the reference at the active plugin root

#### Scenario: the retired carrier is no longer scanned

- **WHEN** the scanner walks a workspace
- **THEN** it does not look for a project-level settings file, because that file is no
  longer produced or consumed

### Requirement: The workspace hook table SHALL live in the workspace state directory

The workspace hook table SHALL be written under the workspace state directory beside
the hook activation state, and SHALL be the input the dispatcher reads to decide which
gates to run for an event.

#### Scenario: the dispatcher finds the table in the resolved workspace

- **WHEN** the dispatcher resolves a workspace and reads its hook table
- **THEN** the table lists the gate-to-event bindings for that workspace and is
  generated from the shipped registry rather than hand-edited

#### Scenario: the table is regenerated idempotently

- **WHEN** the table is regenerated for a workspace that already has one
- **THEN** the result is identical to the previous content and no duplicate bindings
  accumulate

## REMOVED Requirements

### Requirement: The Claude-agent-teams environment gate SHALL be retired

The environment gate's check for the Claude agent-teams environment flag SHALL be
removed, along with the initialization-time rejection that depends on it. That flag is
never set by the MiniMax runtime, so the check can never fire and the rejection path is
dead code.

#### Scenario: initialization is not rejected by a flag the runtime never sets

- **WHEN** a workspace is initialized in an environment where the retired flag is unset
- **THEN** initialization proceeds normally and does not report a flag conflict

#### Scenario: the retired flag is not named in the environment gate

- **WHEN** the environment gate source is inspected
- **THEN** the retired flag name does not appear
