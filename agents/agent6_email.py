from typing import TypedDict
from langgraph.graph import StateGraph, END
from anthropic import Anthropic
from dotenv import load_dotenv, find_dotenv
import json
import os
try:
    from agents.utils import parse_json
except ModuleNotFoundError:
    from utils import parse_json

load_dotenv(find_dotenv(), override=True)

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are an expert email copywriter. Given a campaign brief, you write a
compelling marketing email with a subject line and body copy.

Always respond with valid JSON matching this exact structure:
{
  "subject_line": "the email subject line",
  "body": "the full email body (max 200 words)"
}

Rules:
- Subject line should be punchy, curiosity-driven, and under 60 characters
- Body must be 200 words or fewer
- Match the tone of voice from the brief exactly
- End with a clear call to action"""


class EmailState(TypedDict):
    campaign_brief: dict
    rag_context: dict
    email_copy: dict


def generate_email(state: EmailState) -> EmailState:
    context_block = ""
    if state.get("rag_context"):
        ctx = state["rag_context"]
        guidelines = "\n\n".join(ctx.get("brand_guidelines", []))
        campaigns = "\n\n".join(
            f"- {c['title']}: {c['content']}" for c in ctx.get("similar_campaigns", [])
        )
        context_block = f"\n\nBRAND GUIDELINES (from knowledge base):\n{guidelines}\n\nSIMILAR PAST CAMPAIGNS:\n{campaigns}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Write a marketing email for this campaign:\n\n{json.dumps(state['campaign_brief'], indent=2)}{context_block}",
            }
        ],
    )

    return {"email_copy": parse_json(response.content[0].text)}


def build_email_graph():
    graph = StateGraph(EmailState)
    graph.add_node("generate_email", generate_email)
    graph.set_entry_point("generate_email")
    graph.add_edge("generate_email", END)
    return graph.compile()


def run_email(campaign_brief: dict, rag_context: dict = None) -> dict:
    agent = build_email_graph()
    result = agent.invoke({"campaign_brief": campaign_brief, "rag_context": rag_context or {}, "email_copy": {}})
    return result["email_copy"]


if __name__ == "__main__":
    from sample_brief import SAMPLE_BRIEF

    print("Running Email agent...\n")
    output = run_email(SAMPLE_BRIEF)
    print(json.dumps(output, indent=2))
