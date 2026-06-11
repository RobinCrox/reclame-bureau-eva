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

SYSTEM_PROMPT = """You are an expert copywriter specialising in brand taglines. Given a campaign
brief, you generate three distinct tagline options, each with a short explanation.

Always respond with valid JSON matching this exact structure:
{
  "taglines": [
    {"tagline": "tagline text", "explanation": "why this works for the brand and audience"},
    {"tagline": "tagline text", "explanation": "why this works for the brand and audience"},
    {"tagline": "tagline text", "explanation": "why this works for the brand and audience"}
  ]
}"""


class TaglineState(TypedDict):
    campaign_brief: dict
    rag_context: dict
    tagline_options: dict


def generate_taglines(state: TaglineState) -> TaglineState:
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
                "content": f"Generate three tagline options for this campaign:\n\n{json.dumps(state['campaign_brief'], indent=2)}{context_block}",
            }
        ],
    )

    return {"tagline_options": parse_json(response.content[0].text)}


def build_tagline_graph():
    graph = StateGraph(TaglineState)
    graph.add_node("generate_taglines", generate_taglines)
    graph.set_entry_point("generate_taglines")
    graph.add_edge("generate_taglines", END)
    return graph.compile()


def run_tagline(campaign_brief: dict, rag_context: dict = None) -> dict:
    agent = build_tagline_graph()
    result = agent.invoke({"campaign_brief": campaign_brief, "rag_context": rag_context or {}, "tagline_options": {}})
    return result["tagline_options"]


if __name__ == "__main__":
    from sample_brief import SAMPLE_BRIEF

    print("Running Tagline agent...\n")
    output = run_tagline(SAMPLE_BRIEF)
    print(json.dumps(output, indent=2))
