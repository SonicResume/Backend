import uuid
import httpx

COMFY_URL = "http://127.0.0.1:8188"


# =========================
# WORKFLOW BUILDER
# =========================
def apply_prompt(workflow: dict, prompt: str, node_text="2", node_seed="5"):
    """
    Safely inject prompt + seed into ComfyUI workflow
    (based on your Backend 2 structure)
    """

    if node_text not in workflow:
        raise ValueError(f"Missing text node: {node_text}")

    if node_seed not in workflow:
        raise ValueError(f"Missing seed node: {node_seed}")

    workflow[node_text]["inputs"]["text"] = prompt
    workflow[node_seed]["inputs"]["seed"] = uuid.uuid4().int % 1_000_000_000

    return workflow


# =========================
# COMFY CLIENT
# =========================
async def send_to_comfy(workflow: dict):
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"{COMFY_URL}/prompt",
            json={"prompt": workflow}
        )

    res.raise_for_status()
    return res.json()


# =========================
# MAIN GENERATOR
# =========================
async def generate_image(workflow_loader, prompt: str, workflow_name: str = "workflow_flux"):
    """
    This is your single entry point:
    - loads workflow
    - injects prompt
    - sends to ComfyUI
    """

    workflow = workflow_loader(workflow_name)

    workflow = apply_prompt(workflow, prompt)

    result = await send_to_comfy(workflow)

    return {
        "status": "submitted",
        "prompt_id": result.get("prompt_id")
    }
