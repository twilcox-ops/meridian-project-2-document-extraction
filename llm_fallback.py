import time

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5"
INPUT_PRICE_PER_MTOK = 1.00
OUTPUT_PRICE_PER_MTOK = 5.00

TOOL = {
    "name": "report_capacity",
    "description": (
        "Report the elevator's rated load capacity in pounds as stated in the "
        "inspection certificate text, or null if the text does not state a "
        "numeric capacity anywhere."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"capacity_lbs": {"type": ["integer", "null"]}},
        "required": ["capacity_lbs"],
        "additionalProperties": False,
    },
    "strict": True,
}


def llm_capacity_fallback(page_text, client=None):
    """Structured-output LLM fallback for a single missing capacity_lbs field.

    Returns (capacity_lbs_or_None, cost_usd, latency_seconds). Never fabricates:
    the model is instructed to return null when the text doesn't state a value.
    """
    client = client or anthropic.Anthropic()
    start = time.monotonic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "report_capacity"},
        messages=[{
            "role": "user",
            "content": (
                "This is the text of an elevator inspection certificate. "
                "Report the rated load capacity in pounds. If the text does not "
                "state a numeric capacity anywhere, report null.\n\n" + page_text
            ),
        }],
    )
    latency = time.monotonic() - start

    tool_use = next(b for b in response.content if b.type == "tool_use")
    capacity = tool_use.input["capacity_lbs"]
    cost = (
        response.usage.input_tokens * INPUT_PRICE_PER_MTOK / 1_000_000
        + response.usage.output_tokens * OUTPUT_PRICE_PER_MTOK / 1_000_000
    )
    return capacity, cost, latency
