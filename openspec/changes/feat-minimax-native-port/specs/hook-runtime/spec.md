## ADDED Requirements

### Requirement: Plugin hooks SHALL be assembled by a single workspace-aware dispatcher

The plugin SHALL register exactly one command handler per hook event, implemented by a
dispatcher script. The dispatcher SHALL read the hook event payload from stdin, resolve
the active kunglao analysis workspace from the payload `cwd`, read the shipped
single-source registration table, and invoke every matching gate. When no kunglao
workspace resolves, the dispatcher SHALL exit 0 without producing output and without
spawning a gate.

#### Scenario: a non-kunglao session pays no gate cost

- **WHEN** the dispatcher runs in a directory that carries no kunglao analysis workspace
- **THEN** it exits 0, writes nothing to stdout, and spawns no gate process

#### Scenario: a kunglao workspace runs only its matching gates

- **WHEN** the dispatcher runs inside an active kunglao workspace and the event is
  `PreToolUse` with tool name `bash`
- **THEN** only the gates registered for `PreToolUse` with a matching `bash` matcher
  are invoked

#### Scenario: the dispatcher reads the shipped registration table

- **WHEN** the dispatcher decides which gates to invoke for an event
- **THEN** it reads the shipped single-source registration table, and no second
  hand-maintained list of gate-to-event bindings and no per-workspace hook table file
  exists

### Requirement: Hook commands SHALL use a portable interpreter invocation form

Every registered hook command SHALL invoke the gate through
`uv run --project <root> python -X utf8 <script>`. No command SHALL rely on a
POSIX-style `NAME=value command` environment prefix, which is not portable to the
Windows shell.

#### Scenario: the command form carries UTF-8 through the interpreter

- **WHEN** a registered hook command is inspected
- **THEN** it invokes `python -X utf8` and contains no `PYTHONUTF8=` prefix

#### Scenario: the interpreter degrades observably when uv is unavailable

- **WHEN** `uv` cannot be resolved in the runtime environment
- **THEN** the dispatcher falls back to the workspace virtualenv interpreter and records
  the degradation in the environment readiness snapshot, so the environment gate can
  observe it

### Requirement: Hook matchers SHALL use native MiniMax tool names

Every registered matcher SHALL use the native tool name the model sees: `task` for
subagent dispatch, `bash` for shell execution, and `edit` / `write` for file mutation.
The retired names `Agent`, `Bash`, and `MultiEdit` SHALL NOT appear in any registered
matcher.

#### Scenario: a subagent dispatch reaches the task-scoped gates

- **WHEN** a `task` tool call occurs in an active kunglao workspace
- **THEN** the gates registered for the `task` matcher are invoked

#### Scenario: a file mutation reaches the write gate

- **WHEN** an `edit` or `write` tool call occurs
- **THEN** the write gate is invoked, and no matcher names a tool that does not exist
  in the native runtime

### Requirement: The dispatcher SHALL run inside the MiniMax event budget

The dispatcher SHALL resolve its interpreter and gate paths without spawning a
per-gate process chain, and SHALL keep the number of spawned processes per event
within the runtime's concurrency budget.

#### Scenario: one dispatch event does not fan out into one process per gate

- **WHEN** a `PreToolUse` event matches three gates
- **THEN** the dispatcher spawns exactly one process, reads the payload once, and
  invokes the three gates in-process without re-resolving the environment or
  re-reading stdin for each one

#### Scenario: the gates expose a payload seam so the dispatcher can call them in-process

- **WHEN** a gate is invoked by the dispatcher
- **THEN** it accepts the payload as an argument and reads stdin only when that
  argument is absent, so the first gate cannot drain the payload from the others

## REMOVED Requirements

### Requirement: The project-level settings.json hook registration SHALL be retired

The per-workspace registration of hooks into `<workspace>/.claude/settings.json` SHALL
be removed. The runtime does not read that file, and the project-level registration
path is superseded by the plugin dispatcher.

#### Scenario: no workspace settings file is written during initialization

- **WHEN** `kunglao-init` initializes a workspace
- **THEN** no `.claude/settings.json` is created in the workspace and no hook
  registration entry points at it

#### Scenario: the retired carrier is not scanned for stale references

- **WHEN** the install-reference scanner runs over a workspace
- **THEN** it scans only the MiniMax-side carriers, and the retired settings carrier
  is absent from the carrier list
