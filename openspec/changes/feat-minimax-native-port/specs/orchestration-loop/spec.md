## ADDED Requirements

### Requirement: The monitor loop SHALL be driven by background-task completion notification

The orchestrator's monitor loop SHALL treat the runtime's automatic notification that a
background subagent completed as the primary wake-up source. A scheduled sweep SHALL
remain available as a fallback for a worker that never reports completion, but the
sweep SHALL NOT be the mechanism by which a normally-finishing worker is observed.

#### Scenario: a finished worker wakes the orchestrator

- **WHEN** a dispatched background worker completes
- **THEN** the orchestrator is resumed by the runtime's completion notification and
  immediately re-evaluates the claim register, without waiting for a sweep tick

#### Scenario: a silent worker is still detected

- **WHEN** a dispatched worker produces no completion notification and its status file
  exceeds the staleness threshold
- **THEN** the fallback sweep pings it and applies the strike policy as before

#### Scenario: artifacts are still read from the file contract

- **WHEN** the orchestrator handles a completion notification
- **THEN** the worker's status and declared artifacts are read from the worker status
  file and the fact tree, not from the notification payload

### Requirement: Completion notification SHALL NOT be the only channel for a worker's evidence

The completion notification SHALL be treated as a wake-up signal only. The worker
status file, the fact files, and the claim register remain the authoritative carriers
of a worker's result. A notification that carries no artifact information SHALL still
result in the orchestrator reading the artifacts from disk.

#### Scenario: a notification carries no artifact list

- **WHEN** the completion notification for a worker carries no artifact paths
- **THEN** the orchestrator reads the worker's declared artifacts from the workspace
  and classifies the worker from the status file

#### Scenario: a notification and a status file disagree

- **WHEN** the notification reports success but the worker status file's last status
  line reports a blocked state
- **THEN** the status file wins, because the file contract is the authoritative carrier

### Requirement: The monitor loop SHALL stay within the runtime turn budget

The loop SHALL NOT block a turn waiting for a worker to finish. Every dispatch SHALL
launch in the background and return to the loop immediately.

#### Scenario: dispatch does not block the turn

- **WHEN** the orchestrator dispatches a worker
- **THEN** the dispatch call returns immediately with a task handle, and the loop
  continues to the next step

## MODIFIED Requirements

### Requirement: Worker delivery SHALL use the native task terminator

The delivery rule — concluding a worker whose artifacts are verified — SHALL name the
native task terminator and SHALL keep the rule that no further dispatch or verification
action happens before a delivered worker is concluded.

#### Scenario: a verified worker is concluded before the next dispatch

- **WHEN** a worker reports a terminal status and its declared artifacts are verified
- **THEN** the orchestrator concludes that worker through the native terminator before
  issuing any further dispatch or verification action

#### Scenario: a worker that is not yet terminal is left running

- **WHEN** a worker reports a non-terminal status
- **THEN** the orchestrator does not conclude it, and continues monitoring
