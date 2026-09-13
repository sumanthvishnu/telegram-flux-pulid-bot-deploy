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
    timeout_s: float = 900.0,
) -> bytes:
    """Submit one Flux+PuLID job; return output image bytes."""
    payload: dict[str, Any] = {
        "input": {
            "image_b64": base64.b64encode(image_bytes).decode("ascii"),
            "prompt": prompt,
            "id_weight": id_weight,
        }
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
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
            s.raise_for_status()
            body = s.json()
            status = body.get("status")
            if status == "COMPLETED":
                out = (body.get("output") or {})
                b64 = out.get("image_b64")
                if not b64:
                    raise RunPodError(f"Completed but no image_b64: {body}")
                return base64.b64decode(b64)
            if status in {"FAILED", "CANCELLED", "TIMED_OUT"}:
                raise RunPodError(f"Job {status}: {body}")
            await asyncio.sleep(2.0)
        raise RunPodError(f"Timed out waiting for job {job_id}")
