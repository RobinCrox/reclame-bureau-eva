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

SYSTEM_PROMPT = """You are an expert brand strategist and positioning consultant. Given an audience
profile, you craft a focused marketing positioning strategy in JSON format.

Always respond with valid JSON matching this exact structure:
{
  "campaign_tone": "description of the tone and voice to use",
  "key_messages": [
    "message 1",
    "message 2",
    "message 3",
    "message 4",
    "message 5"
  ],
  "campaign_angle": "the overarching creative angle or narrative hook for the campaign",
  "unique_selling_point": "the single clearest differentiator that sets this product apart"
}"""


class StrategistState(TypedDict):
    audience_profile: dict
    positioning_strategy: dict


def build_strategy(state: StrategistState) -> StrategistState:
    profile_text = json.dumps(state["audience_profile"], indent=2)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Create a positioning strategy for a product targeting this audience:\n\n{profile_text}",
            }
        ],
    )

    strategy = parse_json(response.content[0].text)
    return {"positioning_strategy": strategy}


def build_strategist_graph() -> StateGraph:
    graph = StateGraph(StrategistState)
    graph.add_node("build_strategy", build_strategy)
    graph.set_entry_point("build_strategy")
    graph.add_edge("build_strategy", END)
    return graph.compile()


def run_strategist(audience_profile: dict) -> dict:
    agent = build_strategist_graph()
    result = agent.invoke({"audience_profile": audience_profile, "positioning_strategy": {}})
    return result["positioning_strategy"]


if __name__ == "__main__":
    # Sample output from Agent 1 (agent1_analyst.py)
    sample_audience_profile = {
        "target_demographic": {
            "age": "28-45",
            "gender": "all genders, slight skew toward women",
            "location": "Urban and suburban US, Canada, and Western Europe"
        },
        "pain_points": [
            "Distrust of greenwashing — frustrated by vague sustainability claims",
            "Feeling disconnected from where their food and beverages come from",
            "Difficulty finding premium coffee that aligns with their ethical values",
            "Subscription fatigue from generic boxes that lack meaning",
            "Guilt around consumption habits"
        ],
        "motivations": [
            "Desire to support regenerative agriculture and climate-positive supply chains",
            "Passion for discovery — exploring global cultures through everyday rituals",
            "Willingness to pay a premium for transparency and verified ethical sourcing",
            "Love of curated, gift-like experiences that make daily routines feel special",
            "Desire to share values-aligned discoveries with like-minded people"
        ],
        "lifestyle": "Educated, values-driven professionals with disposable income who treat food and drink as an extension of their identity. They shop at farmers markets, practice mindful consumption, and enjoy slow-living rituals like pour-over coffee.",
        "online_presence": [
            "Instagram — aesthetic coffee content and lifestyle sharing",
            "Reddit — r/Coffee, r/ZeroWaste, r/sustainability",
            "YouTube — long-form content on coffee origins and eco-living",
            "Pinterest — recipe inspiration and sustainable home aesthetics",
            "Substack — food, sustainability, and slow-living newsletters"
        ]
    }

    print("Running Positioning & Strategist agent...\n")
    strategy = run_strategist(sample_audience_profile)
    print(json.dumps(strategy, indent=2))
