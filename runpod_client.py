from __future__ import annotations

import asyncio
import base64
import os
from typing import Any

import httpx

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")

BASE = "https://api.runpod.ai/v2"


class RunPodError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not RUNPOD_API_KEY or not RUNPOD_ENDPOINT_ID:
        raise RunPodError("RUNPOD_API_KEY / RUNPOD_ENDPOINT_ID not set")
    return {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}


async def generate_one(
    *,
    image_bytes: bytes,
    prompt: str,
    id_weight: float = 1.0,
    timeout_s: float = 1200.0,
) -> bytes:
    """Submit one Flux Kontext job; return output image bytes."""
    payload: dict[str, Any] = {
        "input": {
            "image_b64": base64.b64encode(image_bytes).decode("ascii"),
            "prompt": prompt,
            "id_weight": id_weight,
        }
    }
    # Long client timeout: first cold start installs torch + downloads weights.
    timeout = httpx.Timeout(120.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            f"{BASE}/{RUNPOD_ENDPOINT_ID}/run",
            headers=_headers(),
            json=payload,
        )
        r.raise_for_status()
        job = r.json()
        job_id = job.get("id")
        if not job_id:
            raise RunPodError(f"No job id: {job}")

        deadline = asyncio.get_event_loop().time() + timeout_s
        while asyncio.get_event_loop().time() < deadline:
            s = await client.get(
                f"{BASE}/{RUNPOD_ENDPOINT_ID}/status/{job_id}",
                headers=_headers(),
            )
            if s.status_code == 404:
                raise RunPodError(
                    "RunPod job vanished (404). Usually a queue purge or endpoint "
                    "redeploy mid-run — try again."
                )
            s.raise_for_status()
            body = s.json()
            status = body.get("status")
            if status == "COMPLETED":
                out = body.get("output") or {}
                if isinstance(out, list) and out:
                    out = out[0] if isinstance(out[0], dict) else {"image_b64": out}
                b64 = out.get("image_b64") if isinstance(out, dict) else None
                if not b64 and isinstance(out, dict) and out.get("error"):
                    raise RunPodError(f"Worker error: {out.get('error')}")
                if not b64:
                    raise RunPodError(f"Completed but no image_b64: {body}")
                return base64.b64decode(b64)
            if status in {"FAILED", "CANCELLED", "TIMED_OUT"}:
                raise RunPodError(f"Job {status}: {body}")
            await asyncio.sleep(2.0)
        raise RunPodError(f"Timed out waiting for job {job_id}")
