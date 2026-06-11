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

SYSTEM_PROMPT = """You are an expert marketing creative director and brief writer. Given an audience
profile and a positioning strategy, you produce a concise, actionable campaign brief in JSON format.

Always respond with valid JSON matching this exact structure:
{
  "campaign_objective": "one clear sentence describing what the campaign aims to achieve",
  "target_audience_summary": "2-3 sentence summary of who the campaign is speaking to",
  "key_messages": ["message 1", "message 2", "message 3"],
  "tone_of_voice": "description of the tone and style guidelines for all creative work",
  "deliverables": ["deliverable 1", "deliverable 2", "deliverable 3", "deliverable 4"],
  "success_metrics": ["metric 1", "metric 2", "metric 3"]
}"""


class BriefWriterState(TypedDict):
    audience_profile: dict
    positioning_strategy: dict
    rag_context: dict
    campaign_brief: dict


def write_brief(state: BriefWriterState) -> BriefWriterState:
    context = f"""AUDIENCE PROFILE:
{json.dumps(state["audience_profile"], indent=2)}

POSITIONING STRATEGY:
{json.dumps(state["positioning_strategy"], indent=2)}"""

    context_block = ""
    if state.get("rag_context"):
        ctx = state["rag_context"]
        guidelines = "\n\n".join(ctx.get("brand_guidelines", []))
        campaigns = "\n\n".join(
            f"- {c['title']}: {c['content']}" for c in ctx.get("similar_campaigns", [])
        )
        context_block = f"\n\nBRAND GUIDELINES (the brief must align with these):\n{guidelines}\n\nSIMILAR PAST CAMPAIGNS:\n{campaigns}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Write a campaign brief based on the following audience profile and positioning strategy:\n\n{context}{context_block}",
            }
        ],
    )

    brief = parse_json(response.content[0].text)
    return {"campaign_brief": brief}


def build_brief_writer_graph() -> StateGraph:
    graph = StateGraph(BriefWriterState)
    graph.add_node("write_brief", write_brief)
    graph.set_entry_point("write_brief")
    graph.add_edge("write_brief", END)
    return graph.compile()


def run_brief_writer(audience_profile: dict, positioning_strategy: dict, rag_context: dict = None) -> dict:
    agent = build_brief_writer_graph()
    result = agent.invoke({
        "audience_profile": audience_profile,
        "positioning_strategy": positioning_strategy,
        "rag_context": rag_context or {},
        "campaign_brief": {}
    })
    return result["campaign_brief"]


if __name__ == "__main__":
    # Sample output from Agent 1
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

    # Sample output from Agent 2
    sample_positioning_strategy = {
        "campaign_tone": "Warm, intelligent, and quietly confident — the voice of a well-traveled friend who genuinely knows their stuff. Never preachy or performative about sustainability. Speaks with earned authority and poetic specificity.",
        "key_messages": [
            "Every bag tells the full story — from the soil it was grown in to the hands that harvested it.",
            "This isn't a subscription. It's a standing invitation to explore the world one extraordinary cup at a time.",
            "We don't use the word 'sustainable' lightly. Our sourcing partners practice regenerative agriculture that actively restores ecosystems.",
            "Your morning ritual deserves more than a generic blend.",
            "Share something worth talking about."
        ],
        "campaign_angle": "The Provenance Ritual — position the product as the antidote to anonymous consumption: a curated journey that transforms a daily habit into an act of conscious connection.",
        "unique_selling_point": "Fully traceable, regenerative-certified single-origin coffees delivered as a curated discovery experience with radical supply chain transparency."
    }

    print("Running Brief Writer agent...\n")
    brief = run_brief_writer(sample_audience_profile, sample_positioning_strategy)
    print(json.dumps(brief, indent=2))
