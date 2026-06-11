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

SYSTEM_PROMPT = """You are an expert audience and market analyst. Given a product description,
you analyze the target market and return a structured audience profile in JSON format.

Always respond with valid JSON matching this exact structure:
{
  "target_demographic": {
    "age": "age range or description",
    "gender": "gender breakdown or 'all genders'",
    "location": "geographic focus"
  },
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "motivations": ["motivation 1", "motivation 2", "motivation 3"],
  "lifestyle": "description of lifestyle and daily habits",
  "online_presence": ["platform 1", "platform 2", "platform 3"]
}"""


class AnalystState(TypedDict):
    product_description: str
    audience_profile: dict


def analyze_audience(state: AnalystState) -> AnalystState:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Analyze the target audience for this product:\n\n{state['product_description']}",
            }
        ],
    )

    profile = parse_json(response.content[0].text)
    return {"audience_profile": profile}


def build_analyst_graph() -> StateGraph:
    graph = StateGraph(AnalystState)
    graph.add_node("analyze_audience", analyze_audience)
    graph.set_entry_point("analyze_audience")
    graph.add_edge("analyze_audience", END)
    return graph.compile()


def run_analyst(product_description: str) -> dict:
    agent = build_analyst_graph()
    result = agent.invoke({"product_description": product_description, "audience_profile": {}})
    return result["audience_profile"]


if __name__ == "__main__":
    sample_product = """
    EcoBrews — a subscription coffee brand that sources beans exclusively from regenerative
    farms. Each bag includes a QR code linking to the farm's story and impact metrics.
    Subscribers get a monthly "farm box" with seasonal single-origin beans, tasting notes,
    and a small gift from the region (e.g. local spice, recipe card). Priced at $34/month.
    """

    print("Running Audience & Market Analyst agent...\n")
    profile = run_analyst(sample_product)
    print(json.dumps(profile, indent=2))
