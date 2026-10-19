## ADDED Requirements

### Requirement: Every agent SHALL use the MiniMax custom-agent frontmatter contract

Each file under `agents/` SHALL carry frontmatter with `name` equal to the file name
stem, a non-empty `description`, an optional `tools` array of native tool names, an
optional `disallowedTools` array, an optional `mcpServers` array of server names, and
optional `x-mavis.displayName`. The retired `allowedTools`, `triggers`, and `isolation`
fields SHALL NOT appear in any agent file. The fields `hooks`, `permissionMode`,
`x-mavis.avatar`, and `x-mavis.defaultWorkspaceDir` SHALL NOT be written.

#### Scenario: the tool allowlist is honoured and uses native names

- **WHEN** a worker agent declares a restricted tool set
- **THEN** the declared `tools` array contains only native names such as `read`,
  `write`, `edit`, `bash`, `grep`, and `glob`, and the worker session is limited to
  exactly those tools

#### Scenario: the isolation field is retired

- **WHEN** any agent file is inspected
- **THEN** no `isolation` field is present, because a plugin subagent is always an
  isolated child session

#### Scenario: the subagent cannot delegate further

- **WHEN** any agent file declares its `tools` array
- **THEN** the array does not contain `task`, so a worker cannot spawn a further
  subagent and the maker-checker separation holds at the delegation layer

### Requirement: MCP access SHALL be declared by server name

An agent that needs an MCP server SHALL declare it in `mcpServers` by server name, not
by a tool-name pattern. Tool-name patterns such as `mcp__ghidra__*` SHALL NOT appear in
an agent's `tools` array, because the runtime may alias a server whose name collides
with another owner.

#### Scenario: a worker declares the Ghidra server

- **WHEN** the Ghidra-capable worker declares its MCP access
- **THEN** it lists `ghidra` in `mcpServers`, and no `mcp__` prefixed pattern appears in
  its `tools` array

#### Scenario: a colliding server name still resolves to the plugin alias

- **WHEN** a configured MCP server shares its name with a plugin-declared server
- **THEN** the agent's allowlist binds to the plugin alias rather than the same-named
  configured server

### Requirement: Dispatch instructions SHALL use the scoped delegation name

Every place that instructs the orchestrator to dispatch a worker SHALL name the worker
by its scoped plugin delegation name. The bare agent name SHALL NOT be the only form
used in dispatch instructions.

#### Scenario: a dispatch instruction identifies one specific worker

- **WHEN** the orchestrator is instructed to dispatch the generic claim worker
- **THEN** the instruction names the scoped worker identity, and the delegating call
  uses that scoped name

#### Scenario: subagent lifecycle matchers can target one worker

- **WHEN** a lifecycle matcher is registered for a single worker type
- **THEN** it matches the scoped worker identity that the runtime reports as the
  subagent type

### Requirement: The MCP prefix gate SHALL keep its actual deny-list semantics under the native naming rules

The workspace MCP prefix gate SHALL continue to reject the two forbidden namespaces it
rejects today and SHALL allow every other namespace, including the environment-supplied
server namespaces this change declares in `mcpServers`. The gate SHALL remain correct
under the runtime's tool-name construction, including the length cap that truncates a
composed tool name.

The gate's current source comment and its rejection message both state that only one
namespace is sanctioned, while the implementation is a deny-list that permits the
others. This mismatch is pre-existing and SHALL NOT be changed by this port: the port
changes the host runtime, not the gate's policy. The comment and message SHALL be left
as they are so that the enforcement policy stays byte-identical to the reviewed
baseline, and the mismatch SHALL be recorded as a separate follow-up.

#### Scenario: a declared server namespace passes the prefix gate

- **WHEN** a tool whose name begins with a namespace this change declares in
  `mcpServers` reaches the gate
- **THEN** the gate allows it

#### Scenario: a truncated long tool name keeps its prefix verdict

- **WHEN** a server name and tool name compose to a name longer than the runtime's
  length cap
- **THEN** the truncated name still yields the same prefix verdict as the untruncated
  name, because truncation removes only the tail

#### Scenario: a forbidden namespace is still rejected

- **WHEN** a tool name begins with one of the two forbidden namespaces
- **THEN** the gate rejects it with a reason naming the offending namespace
