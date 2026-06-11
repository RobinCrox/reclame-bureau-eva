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

SYSTEM_PROMPT = """You are an expert social media copywriter specialising in Instagram. Given a
campaign brief, you write one Instagram caption and a set of relevant hashtags.

Always respond with valid JSON matching this exact structure:
{
  "caption": "the instagram caption text (max 150 words, no hashtags inline)",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"]
}

Rules:
- Caption must be 150 words or fewer
- Include 5 to 8 hashtags
- Hashtags go in the array only, not in the caption body
- Write for the brand tone described in the brief"""


class InstagramState(TypedDict):
    campaign_brief: dict
    instagram_post: dict


def generate_instagram(state: InstagramState) -> InstagramState:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Write an Instagram post for this campaign:\n\n{json.dumps(state['campaign_brief'], indent=2)}",
            }
        ],
    )

    return {"instagram_post": parse_json(response.content[0].text)}


def build_instagram_graph():
    graph = StateGraph(InstagramState)
    graph.add_node("generate_instagram", generate_instagram)
    graph.set_entry_point("generate_instagram")
    graph.add_edge("generate_instagram", END)
    return graph.compile()


def run_instagram(campaign_brief: dict) -> dict:
    agent = build_instagram_graph()
    result = agent.invoke({"campaign_brief": campaign_brief, "instagram_post": {}})
    return result["instagram_post"]


if __name__ == "__main__":
    from sample_brief import SAMPLE_BRIEF

    print("Running Instagram agent...\n")
    output = run_instagram(SAMPLE_BRIEF)
    print(json.dumps(output, indent=2))
