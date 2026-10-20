## ADDED Requirements

### Requirement: Every shipped skill SHALL be a first-class MiniMax skill

Each skill SHALL live at `skills/<skill-name>/SKILL.md` where `<skill-name>` matches
`^[A-Za-z0-9._-]+$` and contains no colon. The frontmatter `name` SHALL equal
`<skill-name>`, and `description` SHALL be non-empty and SHALL carry the activation
triggers that the retired `triggers` field used to hold.

The shipped skill set SHALL be exactly these seven, one directory each:
`kunglao` (the plugin's main entry skill, relocated from the repository root),
`kunglao-convergence` (the full convergence contract, relocated from
`skills/kunglao-agent/`), `kunglao-init`, `kunglao-analysis`, `kunglao-resume`,
`kunglao-upgrade`, and `kunglao-help`.

#### Scenario: the shipped skill set is the pinned seven

- **WHEN** the shipped skill directories are enumerated
- **THEN** they are exactly the seven named above, each appearing once, and no skill
  directory holds two skills

#### Scenario: the main entry skill does not shadow the help skill

- **WHEN** the main entry skill is renamed from the relocated router
- **THEN** its name is `kunglao`, not `kunglao-help`, because the help command skill
  already owns that name

#### Scenario: the activation surface lives in the description

- **WHEN** a user phrases a request that should start the analysis loop
- **THEN** the matching skill's `description` states both the role and the trigger
  phrases, so the runtime can select it without a separate trigger list

#### Scenario: the command surface is a set of independent skills

- **WHEN** the user asks to initialize a workspace
- **THEN** the initialization skill is selectable on its own, without routing through a
  namespace-prefixed subcommand

### Requirement: The namespace subcommand form SHALL be retired

No skill name, dispatcher argument, help text, script, or test SHALL reference the
retired namespace subcommand form. The per-command table SHALL exist as a single data
source consumed by both the skill bodies and the dispatcher.

#### Scenario: the subcommand table has exactly one source

- **WHEN** the command table is read by the skill bodies and by the dispatcher
- **THEN** both read the same single source, and no second hand-maintained list of
  commands exists in the tree

#### Scenario: no retired namespace reference remains

- **WHEN** the tree is searched for the retired namespace subcommand form
- **THEN** no live source, skill, script, or test references it; only the archived
  change history may mention it

### Requirement: Skill bodies SHALL use native runtime tool names

Every reference inside a skill body to a Claude tool mechanism SHALL use the native
runtime name and the native semantics: the background dispatch tool, the task output
reader, the task terminator, and the follow-up delivery channel.

#### Scenario: a skill instructs the orchestrator to launch a background worker

- **WHEN** a skill body describes launching a worker
- **THEN** it names the native background dispatch tool and states that the call runs in
  the background and returns a task handle

#### Scenario: a skill instructs the orchestrator to deliver a finished worker

- **WHEN** a skill body describes concluding a delivered worker
- **THEN** it names the native task terminator and the status values it accepts

#### Scenario: no Claude-only tool name survives in a skill body

- **WHEN** a skill body is searched for the retired tool names
- **THEN** none are present, and the surrounding prose still conveys the same
  operational rule

### Requirement: Root-router and convergence-contract skills SHALL not collide

The skill that presents the command menu and the skill that carries the full
convergence contract SHALL have distinct names and distinct directories, and the
frontmatter name of each SHALL equal its own directory name.

#### Scenario: no two shipped skills share a name

- **WHEN** the shipped skill directories are enumerated
- **THEN** every frontmatter `name` is unique across the set

## MODIFIED Requirements

### Requirement: The command-menu skill SHALL describe the command surface without a namespace prefix

The menu skill SHALL list the available commands by their plain skill names and SHALL
not present them as namespace-prefixed subcommands of a single parent.

#### Scenario: the menu lists the independent command skills

- **WHEN** the menu skill is loaded and no arguments were supplied
- **THEN** it prints the list of command skills and stops, waiting for the operator to
  pick one
