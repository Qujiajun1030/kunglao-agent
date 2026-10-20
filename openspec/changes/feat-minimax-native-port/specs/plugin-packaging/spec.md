## ADDED Requirements

### Requirement: The repository SHALL ship a MiniMax Code plugin manifest

The repository SHALL carry `.minimax-plugin/plugin.json` declaring `schemaVersion: 1`, a
plugin `name` matching `^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$`, a SemVer `version`, a
non-empty `description`, an `author`, an `icon` path pointing at an existing package
image, a `category` from the MiniMax category pool, a non-empty `exampleQueries` array,
`"apps": []`, a present `mcpServers` array, and the `skills` / `agents` / `hooks` asset
arrays. The `hooks` array SHALL point at `hooks/hooks.json`; the `agents` array SHALL
point at `agents/<name>.md` entries; the `skills` array SHALL point at
`skills/<name>/SKILL.md` entries. The `mcpServers` array SHALL be present and empty,
because the MCP servers this project uses are environment-supplied rather than bundled
as package files; omitting the field is a manifest error that rejects the whole
package.

#### Scenario: the manifest declares every runtime asset

- **WHEN** `.minimax-plugin/plugin.json` is parsed
- **THEN** `skills` lists every shipped skill directory, `agents` lists all ten worker
  and checker agents, `hooks` lists `hooks/hooks.json`, and `mcpServers` is present and
  empty

#### Scenario: the manifest stays inside the plugin V1 asset limits

- **WHEN** the package rooted at the repository root is measured
- **THEN** the count of regular files is at most 1024 and the count of total filesystem
  entries is at most 2048

### Requirement: The shipped plugin package SHALL contain only the runtime asset set

The plugin package SHALL contain `skills/`, `agents/`, `hooks/`, `tools/`, `scripts/`,
`templates/`, `schemas/`, `rules/`, `references/`, `.minimax-plugin/`, and the plugin
icon. It SHALL NOT contain a root-level `SKILL.md`: the root command-router skill is
relocated under `skills/` so that every shipped skill lives at
`skills/<skill-name>/SKILL.md`. It SHALL NOT contain `tests/`, `openspec/`, `evals/`,
`eval/`, `docs/`, `gc-harness/`, `kunglao-bench/`, `devkit/`, or `.github/`.

#### Scenario: the package has no root-level skill file

- **WHEN** the package root is enumerated
- **THEN** there is no `SKILL.md` at the root, and every skill file resolves under
  `skills/<skill-name>/SKILL.md`

#### Scenario: the relocated router is addressed by its new name

- **WHEN** the relocated command-router skill is read
- **THEN** its frontmatter name equals its new directory name, and it differs from every
  other shipped skill's name

#### Scenario: the source tree exceeds the limit but the shipped set does not

- **WHEN** the tracked file count of the full source tree is compared with the tracked
  file count of the runtime asset set
- **THEN** the full tree exceeds 1024 tracked files while the runtime asset set stays at
  or below 1024, and the difference is attributable to the non-shipped trees such as
  `tests/` and `openspec/`

#### Scenario: the asset counts are reproducible

- **WHEN** the asset set is counted with `git ls-files` and measured with the
  workspace's actual byte sizes
- **THEN** the same command yields the same counts, and the counts stay within the
  package limits above

The point-in-time measured baseline lives in the change proposal's evidence table
rather than here, so that this requirement does not become stale as the tree grows.

#### Scenario: no path segment violates the portable-segment rule

- **WHEN** every path in the package is split on `/`
- **THEN** each segment matches `^[A-Za-z0-9._-]+$` and no segment ends with `.`

### Requirement: Agent file paths SHALL satisfy the subagent path rule

Every agent file referenced by the manifest SHALL sit directly under `agents/` and its
package-relative path SHALL match `^agents/[a-z][a-z0-9_-]*\.md$`. Nested directories
under `agents/` SHALL NOT be used, because they are not read.

#### Scenario: every declared agent path is a flat file under agents/

- **WHEN** each entry of the manifest `agents` array is checked
- **THEN** the path matches `^agents/[a-z][a-z0-9_-]*\.md$` and the file exists

### Requirement: The plugin manifest SHALL coexist with a retired Claude manifest without shadowing it

The repository MAY retain `.claude-plugin/plugin.json` for provenance. When both
manifests are present, the MiniMax manifest SHALL be the active one: the runtime selects
the Agent Plugins V1 root manifest first, then MiniMax, then the compatible vendor
format, then Codex — a single selection, never a merge.

#### Scenario: the MiniMax manifest wins the selection

- **WHEN** both `.minimax-plugin/plugin.json` and `.claude-plugin/plugin.json` exist in a
  package root
- **THEN** the MiniMax manifest is the active manifest and the Claude manifest is inert
  provenance

## MODIFIED Requirements

### Requirement: The release manifest SHALL declare the MiniMax plugin asset set

`release-manifest.yaml` SHALL declare the shipped assets under the MiniMax plugin
layout: the `.minimax-plugin/plugin.json` manifest, the `skills/` tree, the `agents/`
tree, the `hooks/` tree (including `hooks/hooks.json`), the `tools/` tree, the
`scripts/` tree, the `templates/` tree, the `schemas/` tree, the `rules/` tree, and
the `references/` tree. It SHALL NOT declare the retired `.claude-plugin/` manifest
as a shipped asset.

#### Scenario: every shipped directory is declared

- **WHEN** the declared asset list is compared with the shipped directory list
- **THEN** every shipped directory — including `scripts/`, which carries the majority
  of the shipped files — appears in the declaration, and no declared path is missing
  from the tree

#### Scenario: the release receipt validates against the new asset set

- **WHEN** `python scripts/release_receipt.py --check` runs on the release tree
- **THEN** every declared path exists and its digest is recorded, and no declared path
  is missing from the tree
