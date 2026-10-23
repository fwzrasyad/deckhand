# Writing actions

Purpose: Explain `actions.yaml`: its format, action and param fields, run types,
templating, validation rules, reload behaviour, and status probes (SRD
Section 8.3).

Status: outline, to be written in Phase 6.

## File and safety model
Edited only on the PC, loaded with `yaml.safe_load`, validated by pydantic; this file is the security boundary (Section 8.3).
## Top-level format
`version` and the `actions` list (Section 8.3).
## Action fields
`id`, `label`, `icon`, `category`, `description`, `run`, `params`, `confirm`, `parallel`, `interactive`, `mode`, `timeout_sec`, and `status` (Section 8.3).
## Run types
`exec`, `script`, `shell` (gated by `security.allow_shell`), and `macro` (Section 8.3).
## Params
Field types, validation attributes, and runtime checks including the leading-dash rule (Section 8.3).
## Templating
Where `{{name}}` placeholders are allowed, how substitution works, and the rules for defaults, `~`, and `$VAR` (Section 8.3).
## Load-time validation
Unique ids, resolved references, and forbidden placeholder positions (Section 8.3).
## Reload
CLI, tray, or mtime polling; failed reloads keep the previous registry; layout pruning and `CONFIG_CHANGED` (Section 8.3).
## Status probes
`process`, `tcp_port`, `http`, `docker_container`, and `run_state` (Section 8.3).
