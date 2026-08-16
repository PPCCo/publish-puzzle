# MCP connectors

This directory holds the **reviewed source of truth** for out-of-core MCP
connectors that pub-clr's offline core may drive but never bundles. The offline
core (`image_gen.py`, `dependencies.py`, `compositor.py`) is network-free
(rule 18); a connector is the *only* sanctioned network egress, and it runs as a
separate stdio MCP server — never imported by core modules.

## `comfyui_mcp_bridge.py` — local ComfyUI text-to-image bridge

A minimal, auditable (~300-line, stdlib + `mcp` SDK only) stdio MCP server that
lets Claude Code drive a **local** ComfyUI instance on `127.0.0.1:8188`. It
exposes exactly two tools:

- `health_check()` — confirms ComfyUI is reachable (call this FIRST; works even
  when the live flag is off, so it distinguishes "server down" from "live off").
- `generate_image(positive_prompt, negative_prompt, width, height, seed?, provider?)`
  — runs one text-to-image job (SDXL default, or FLUX.1-schnell via
  `provider="local-flux-schnell"`) and returns the saved PNG's absolute path.

Governance built into the bridge itself:

- **Live gate:** `generate_image` refuses to submit any job unless
  `IMAGE_GEN_LIVE_ENABLED == "1"`.
- **Local only:** talks to `COMFYUI_URL` (default `http://127.0.0.1:8188`). No
  egress off the machine, no credential, no per-image cost once weights are on
  disk — same category as ffmpeg/epubcheck.
- The bridge **never** touches the repo, workflow state, approvals, or rights
  records. Provenance + rights records are written by `image-gen ingest` in the
  repo *after* a PNG exists — never here.

This file is the byte-for-byte copy of the deployed bridge
(`sha256 aecec08…14bfc`). `doctor` compares this connector against the deployed
copy and reports drift (`bridge:connector` check). If you update the bridge,
update **both** copies so they stay in sync.

## Home, registration, and repoint — HUMAN steps

The following are **documented human steps**, not performed by framework code.
`.mcp.json` edits in particular are reserved to the human (security rule 17):
the assistant does not edit `.mcp.json`.

### 1. Neutral install home (recommended)

The bridge currently lives next to a specific ComfyUI checkout at
`../image-tools/ComfyUI/comfyui_mcp_bridge.py`. To decouple it from any one
repo, a human may move it to a neutral shared home, e.g.
`../image-tools/mcp/comfyui_mcp_bridge.py`, and point every consuming repo's
`.mcp.json` at that path. If you do, either keep the deployed copy next to
ComfyUI (the bridge's output-dir fallback assumes it sits at `<ComfyUI>/…`) or
set `COMFYUI_URL` so `/system_stats` resolves the output directory. The
`doctor` drift check reads the deployed path from `$COMFYUI_BRIDGE_PATH`
(default `../image-tools/ComfyUI/comfyui_mcp_bridge.py`); set that env var if
you move it.

### 2. Register `comfyui-mcp` in `.mcp.json` (human edit)

pub-clr's `.mcp.json` ships with only `publishing-house`. To enable live
generation, a human adds a `comfyui-mcp` server. Proven working shape (from the
sibling publish-bk repo, running ComfyUI v0.32.0 on Apple silicon):

```json
"comfyui-mcp": {
  "type": "stdio",
  "command": "/absolute/path/to/image-tools/ComfyUI/.venv-comfy/bin/python3",
  "args": ["/absolute/path/to/comfyui_mcp_bridge.py"],
  "env": {
    "COMFYUI_URL": "http://127.0.0.1:8188",
    "IMAGE_GEN_LIVE_ENABLED": "1",
    "FLUX_WEIGHT_DTYPE": "default"
  }
}
```

Notes:

- `command` must be the ComfyUI venv's Python (it has `mcp` + ComfyUI deps).
- `FLUX_WEIGHT_DTYPE: "default"` requests full fp16 for FLUX; the bridge
  defaults to `fp8_e4m3fn` (halves memory on Apple silicon, tiny quality cost)
  if unset. Set `"default"` only if you have the RAM.
- `IMAGE_GEN_LIVE_ENABLED: "1"` is what flips the bridge from
  health-check-only to able-to-generate. Leaving it unset keeps the bridge
  present but inert — the framework still ships `mode: manual-only` regardless.
- After editing `.mcp.json`, restart Claude Code, then run the `comfyui-mcp`
  `health_check` tool to confirm reachability before any `generate_image` call.

### 3. Repoint publish-bk (optional)

If you move the bridge to a neutral home (step 1), update publish-bk's
`.mcp.json` `comfyui-mcp` entry to the new path as well, so both repos share one
reviewed bridge. Again: a human edit.
