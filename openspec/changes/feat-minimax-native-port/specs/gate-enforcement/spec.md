## ADDED Requirements

### Requirement: Every blocking gate SHALL emit the MiniMax-native deny decision

Each gate that must stop a tool call SHALL write, to stdout, a single JSON object
carrying `hookSpecificOutput.hookEventName` equal to the active event,
`hookSpecificOutput.permissionDecision` equal to `"deny"`, and
`hookSpecificOutput.permissionDecisionReason` carrying the operator-facing reason. The
gate SHALL additionally exit with code 2 so that a compatible-format load path blocks
identically.

The seven gates covered are `write_guard`, `dispatch_gate`, `evidence_pin_guard`,
`orchestrator_tool_guard`, `rt_read_barrier`, `worker_budget`, and
`env_check_gate`. A gate whose blocking path does not exit 2 in the reviewed baseline
is not in this set. In particular the two Stop gates `completion_gate` and
`workguard_gate` use the top-level `{"decision": "block"}` shape and never exit 2 from
the hook path, so they are out of scope here.

Each gate's **blocking path** today signals the block in one of two ways, and the port
SHALL make every blocking path signal it in **both** ways:

- `write_guard` signals only through stderr plus exit code 2 — it has no stdout channel
  at all. The port ADDS the native deny JSON to stdout and keeps stderr and exit 2.
- `dispatch_gate`, `evidence_pin_guard`, `orchestrator_tool_guard`, `rt_read_barrier`,
  `worker_budget`, and `env_check_gate` signal through a stdout `hookSpecificOutput`
  object plus exit code 2. The port ADDS `permissionDecision` `"deny"` and a
  `permissionDecisionReason` to that same object and keeps `additionalContext` and
  exit 2.

Each gate's **non-blocking path** SHALL NOT carry a deny verdict, and whatever that path
emits today SHALL be preserved as-is. The concrete emission differs per gate — some
print nothing, some print `additionalContext`, one prints a `permissionDecision`
`"allow"` with a reason — and the port SHALL NOT normalize them. The `"allow"` verdict
is permission-bearing: it can resolve an ordinary permission confirmation on the
product's behalf. Keeping it preserves the gate's current observable behavior exactly;
replacing it with `additionalContext` would restore a purely advisory posture but would
let ordinary permission prompts reappear for the guarded tool. This port keeps the
current behavior and records the alternative as a separate follow-up rather than
silently changing it.

#### Scenario: a native-format load denies the tool call

- **WHEN** the gate decides to block and the hook is loaded in the MiniMax-native
  plugin format
- **THEN** the hook's stdout parses to a structured decision whose permission decision
  is `deny`, and the tool call does not execute

#### Scenario: a compatible-format load denies the tool call

- **WHEN** the gate decides to block and the hook is loaded in a compatible vendor
  format
- **THEN** the hook's process exit code is 2, and the tool call does not execute

#### Scenario: both channels are present in the same blocking response

- **WHEN** the gate decides to block
- **THEN** the emitted JSON carries `permissionDecision` `deny` AND the process exit
  code is 2 — a response carrying only one of the two channels is a defect

#### Scenario: a non-blocking path carries no deny verdict

- **WHEN** a gate decides to allow the operation
- **THEN** its response carries no deny verdict, the tool call proceeds, and whatever
  that gate emits on that path is unchanged from the reviewed baseline

#### Scenario: a gate with no stdout channel gains exactly one

- **WHEN** a gate whose blocking path today writes only to stderr is ported
- **THEN** its blocking path writes exactly one JSON object to stdout, carrying the
  deny verdict, and keeps its stderr output and exit code 2

### Requirement: The port SHALL not change any gate's existing error posture

Each gate today has its own deliberate posture on an unresolvable input — some fail
open, some fail closed, and the choice is gate-specific and reviewed. The port SHALL
preserve each gate's posture exactly: it SHALL NOT turn a fail-open gate into a
fail-closed one, nor the reverse. Changing an error posture is a policy decision
outside the scope of moving the host runtime.

The one invariant the port itself introduces is narrow: constructing the native deny
channel SHALL be exception-safe. If building the deny JSON raises, the gate SHALL
still exit with its blocking exit code, so that the block is never lost because of a
serialization failure.

#### Scenario: a fail-open gate stays fail-open

- **WHEN** a gate that today returns an allow on an unparseable payload receives an
  unparseable payload after the port
- **THEN** it still allows the operation, exactly as it does today

#### Scenario: a deny-channel serialization failure does not lose the block

- **WHEN** a gate decides to block but the deny JSON cannot be constructed
- **THEN** the gate still exits with its blocking exit code and its stderr reason, and
  the tool call does not execute

### Requirement: The Stop-event completion gate SHALL keep its existing decision shape

`completion_gate` SHALL continue to emit the top-level `{"decision": "block", "reason":
...}` shape on the `Stop` event. That shape is natively supported and its adjudication
logic SHALL NOT be rewritten.

#### Scenario: an unsanctioned stop is blocked

- **WHEN** the completion gate finds no sanctioned PASS on record
- **THEN** the hook emits a top-level `decision` `block` with the reason, and the
  session is not allowed to end

## MODIFIED Requirements

### Requirement: The write gate SHALL block on the MiniMax-native deny channel

`hooks/write_guard.py` SHALL replace its exit-code-only blocking contract with a dual
emission: the MiniMax-native `permissionDecision: "deny"` channel AND exit code 2. Its
carrier detection, checker logic, and `kunglao_log` write on every block SHALL be
unchanged.

#### Scenario: a carrier write without a provenance chain is blocked on both channels

- **WHEN** `write_guard` rejects a write to a contract carrier because the fact body
  lacks a provenance chain
- **THEN** the hook emits a `permissionDecision` `deny` with the reason, exits 2, and
  the block is recorded in `kunglao_log`

#### Scenario: a non-carrier write is still allowed

- **WHEN** `write_guard` finds the target is not a contract carrier
- **THEN** the hook exits 0, emits no deny decision, and the write proceeds
