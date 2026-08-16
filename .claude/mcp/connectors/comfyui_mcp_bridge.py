#!/usr/bin/env python3
"""comfyui_mcp_bridge.py — minimal, auditable stdio MCP server for a *local* ComfyUI.

WHAT THIS IS
------------
A tiny bridge that lets Claude Code (via the /book-generate-images skill) drive a
self-hosted ComfyUI instance running on localhost. It exposes exactly two MCP tools:

  - health_check()  -> confirms ComfyUI is reachable (call this FIRST).
  - generate_image(positive_prompt, negative_prompt, width, height, seed?)
                    -> runs one SDXL 1.0 base text-to-image job and returns the
                       ABSOLUTE path of the saved PNG.

That is the whole contract the skill needs (SKILL.md lines 82-91: a lightweight
health call, then per-brief a call with the exact positive/negative prompt +
dimensions, producing a saved file whose path we hand to `image-gen ingest`).

WHY A CUSTOM ~120-LINE SERVER (not a third-party bridge)
--------------------------------------------------------
This process runs on your machine with access to your local network. Keeping it to
stdlib `urllib`/`json` + Anthropic's own `mcp` SDK means the entire trust surface is
code you can read in one sitting — no unverified third-party maintainer, no telemetry,
no scope creep. It matches the framework's deterministic, gated posture.

GOVERNANCE
----------
- LIVE GATE: refuses to submit any job unless IMAGE_GEN_LIVE_ENABLED == "1".
  This is the framework's convention (EXTENSION_GUIDE.md §6), enforced *in code*
  here rather than bolted on with a wrapper script.
- LOCAL ONLY: talks to COMFYUI_URL (default http://127.0.0.1:8188). No egress, no
  credential, no per-image cost once the SDXL weights are on disk — the same
  category as ffmpeg/epubcheck.
- The bridge never touches the book repo, workflow state, approvals, or rights
  records. Provenance + rights records are written by `image-gen ingest` in the
  book repo AFTER a file exists — never here.

DEPENDENCY
----------
  pip install mcp        # Anthropic's official MCP SDK
Everything else is Python standard library.

ENVIRONMENT VARIABLES
---------------------
  COMFYUI_URL             base URL of the running ComfyUI  (default http://127.0.0.1:8188)
  IMAGE_GEN_LIVE_ENABLED  must be "1" or generate_image refuses (health_check still works)
  COMFY_GEN_TIMEOUT_S     max seconds to wait for one image  (default 300)
"""
from __future__ import annotations

import json
import os
import time
import uuid
import urllib.request
import urllib.error

from mcp.server.fastmcp import FastMCP

COMFY_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
LIVE = os.environ.get("IMAGE_GEN_LIVE_ENABLED") == "1"
TIMEOUT_S = int(os.environ.get("COMFY_GEN_TIMEOUT_S", "300"))
CHECKPOINT = "sd_xl_base_1.0.safetensors"            # SDXL (existing default provider)
# FLUX.1-schnell component files (installed under ComfyUI/models/{diffusion_models,text_encoders,vae})
FLUX_UNET = "flux1-schnell.safetensors"
FLUX_CLIP_L = "clip_l.safetensors"
FLUX_T5 = "t5xxl_fp16.safetensors"
FLUX_VAE = "ae.safetensors"
# fp8 runtime quantization: halves memory on Apple silicon, tiny quality cost.
# Override with FLUX_WEIGHT_DTYPE=default for full fp16 if you have the RAM.
FLUX_WEIGHT_DTYPE = os.environ.get("FLUX_WEIGHT_DTYPE", "fp8_e4m3fn")

mcp = FastMCP("comfyui-bridge")


# ---------------------------------------------------------------------------
# ComfyUI HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------
def _get_json(path: str, timeout: float = 10.0) -> dict:
    with urllib.request.urlopen(f"{COMFY_URL}{path}", timeout=timeout) as r:
        return json.load(r)


def _post_json(path: str, payload: dict, timeout: float = 30.0) -> dict:
    req = urllib.request.Request(
        f"{COMFY_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _sdxl_txt2img_workflow(pos: str, neg: str, width: int, height: int, seed: int) -> dict:
    """A minimal SDXL 1.0 base text-to-image graph in ComfyUI's prompt-API format.

    Node "9" is a SaveImage node; its output filename+subfolder is what we resolve
    back to an absolute path after the job completes.
    """
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed, "steps": 30, "cfg": 7.0,
                "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0,
                "model": ["4", 0], "positive": ["6", 0],
                "negative": ["7", 0], "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "book-sdxl", "images": ["8", 0]}},
    }


def _flux_schnell_txt2img_workflow(pos: str, neg: str, width: int, height: int, seed: int) -> dict:
    """FLUX.1-schnell text-to-image graph in ComfyUI's prompt-API format.

    schnell is timestep-distilled: CFG-disabled (cfg=1.0), ~4 steps, euler/simple.
    There is no true negative prompt under distillation, so `neg` is encoded but has
    no effect at cfg=1.0 — kept only so KSampler's required `negative` input is
    well-formed. Node "9" is the SaveImage node resolved to an absolute path, exactly
    like the SDXL graph, so the polling logic downstream is unchanged.
    """
    return {
        "10": {"class_type": "UNETLoader",
               "inputs": {"unet_name": FLUX_UNET, "weight_dtype": FLUX_WEIGHT_DTYPE}},
        "11": {"class_type": "DualCLIPLoader",
               "inputs": {"clip_name1": FLUX_CLIP_L, "clip_name2": FLUX_T5, "type": "flux"}},
        "12": {"class_type": "VAELoader", "inputs": {"vae_name": FLUX_VAE}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["11", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["11", 0]}},
        "13": {"class_type": "FluxGuidance",
               "inputs": {"conditioning": ["6", 0], "guidance": 3.5}},
        "5": {"class_type": "EmptySD3LatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "3": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 4, "cfg": 1.0,
                         "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                         "model": ["10", 0], "positive": ["13", 0],
                         "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "book-flux", "images": ["8", 0]}},
    }


def _comfy_output_root() -> str:
    """Absolute path of ComfyUI's own output directory.

    We ask ComfyUI where it thinks its output dir is (/system_stats exposes it on
    recent builds); fall back to <ComfyUI>/output relative to this file's install
    location. This is the fix for the naive `os.path.join(OUTPUT_DIR, fname)` bug —
    ComfyUI decides the real directory, and saved images may sit in a `subfolder`.
    """
    try:
        stats = _get_json("/system_stats", timeout=5.0)
        # Newer ComfyUI exposes paths under system_stats; be defensive about shape.
        for key in ("output_directory", "output_dir"):
            val = stats.get("system", {}).get(key) or stats.get(key)
            if val:
                return os.path.abspath(os.path.expanduser(val))
    except Exception:
        pass
    # Fallback: this file lives at <ComfyUI>/comfyui_mcp_bridge.py after install,
    # so ComfyUI's output/ is a sibling.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------
@mcp.tool()
def health_check() -> dict:
    """Confirm the local ComfyUI is reachable. Call this before generating.

    Returns {"ok": true, "comfyui_url": ..., "live_enabled": bool, "checkpoint": ...}
    or {"ok": false, "error": ...}. Never submits a job, so it works even when
    IMAGE_GEN_LIVE_ENABLED is unset — use it to distinguish "server down" from
    "live flag off".
    """
    try:
        stats = _get_json("/system_stats", timeout=5.0)
    except Exception as exc:  # noqa: BLE001 - report any failure to the caller
        return {"ok": False, "comfyui_url": COMFY_URL, "live_enabled": LIVE,
                "error": f"ComfyUI not reachable: {exc}"}
    version = None
    try:
        version = stats.get("system", {}).get("comfyui_version")
    except Exception:
        pass
    flux_available = False
    try:
        info = _get_json("/object_info/UNETLoader", timeout=5.0)
        choices = info["UNETLoader"]["input"]["required"]["unet_name"][0]
        flux_available = FLUX_UNET in choices
    except Exception:
        pass
    return {"ok": True, "comfyui_url": COMFY_URL, "live_enabled": LIVE,
            "checkpoint": CHECKPOINT, "flux_available": flux_available,
            "flux_weight_dtype": FLUX_WEIGHT_DTYPE, "comfyui_version": version}


@mcp.tool()
def generate_image(positive_prompt: str, negative_prompt: str = "",
                   width: int = 1024, height: int = 1024,
                   seed: int | None = None, provider: str = "local-sdxl") -> dict:
    """Generate ONE image (SDXL default, or FLUX.1-schnell via provider=local-flux-schnell)
    and return the saved PNG's absolute path.

    Args:
      positive_prompt: required; the brief's generation_prompt.positive.
      negative_prompt: optional; the brief's generation_prompt.negative.
      width, height:   pixel dimensions. NOTE: SDXL is trained near ~1024px on a
                       side; for very large book targets, generate at an
                       SDXL-native size in the right aspect ratio and upscale
                       downstream (the skill/guide handles this).
      seed:            optional; omit for a deterministic seed derived from the
                       prompt so repeat calls are reproducible.
      provider:        "local-sdxl" (default) or "local-flux-schnell". Selects the
                       ComfyUI workflow; flux runs CFG-disabled at ~4 steps and its
                       negative_prompt is inert.

    Returns {"path": "<abs png>", "prompt_id": ..., "seed": ..., "width":..., "height":...}
    or {"error": ...}. Refuses unless IMAGE_GEN_LIVE_ENABLED == "1".
    """
    if not LIVE:
        return {"error": "IMAGE_GEN_LIVE_ENABLED != 1 — refusing to submit a live job. "
                         "Set it in the bridge's MCP env (and your shell) to enable."}
    if not positive_prompt or not positive_prompt.strip():
        return {"error": "positive_prompt is required and must be non-empty."}

    # Deterministic default seed (no clock/random): derived from the prompt text so
    # the same brief reproduces the same image. Caller may override.
    if seed is None:
        seed = abs(hash((positive_prompt, negative_prompt, width, height))) % (2 ** 31)

    if provider == "local-flux-schnell":
        wf = _flux_schnell_txt2img_workflow(positive_prompt, negative_prompt, width, height, seed)
        active_model = FLUX_UNET
    else:
        wf = _sdxl_txt2img_workflow(positive_prompt, negative_prompt, width, height, seed)
        active_model = CHECKPOINT
    client_id = str(uuid.uuid4())
    try:
        resp = _post_json("/prompt", {"prompt": wf, "client_id": client_id})
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            pass
        return {"error": f"ComfyUI rejected the workflow (HTTP {exc.code}). "
                         f"Is {active_model} installed for provider '{provider}'? Detail: {body[:400]}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to submit workflow: {exc}"}

    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        return {"error": f"ComfyUI did not return a prompt_id: {resp}"}

    # Poll /history/<id> until node 9's images appear (or timeout).
    deadline = TIMEOUT_S
    waited = 0
    while waited < deadline:
        time.sleep(1)
        waited += 1
        try:
            hist = _get_json(f"/history/{prompt_id}", timeout=10.0)
        except Exception:
            continue
        entry = hist.get(prompt_id)
        if not entry:
            continue
        outputs = entry.get("outputs", {})
        node9 = outputs.get("9", {})
        images = node9.get("images") or []
        if not images:
            # Some builds surface images under a different SaveImage node id; scan all.
            for node in outputs.values():
                if node.get("images"):
                    images = node["images"]
                    break
        if images:
            img = images[0]
            fname = img.get("filename")
            subfolder = img.get("subfolder", "")
            out_root = _comfy_output_root()
            abs_path = os.path.abspath(os.path.join(out_root, subfolder, fname))
            return {"path": abs_path, "prompt_id": prompt_id, "seed": seed,
                    "width": width, "height": height, "subfolder": subfolder}
    return {"error": f"Timed out after {TIMEOUT_S}s waiting for prompt {prompt_id}. "
                     "The job may still be running in ComfyUI; check its console."}


if __name__ == "__main__":
    mcp.run(transport="stdio")
