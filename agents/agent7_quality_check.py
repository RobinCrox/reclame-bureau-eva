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

SYSTEM_PROMPT = """You are a senior creative director conducting a quality review of marketing
campaign assets. Your job is to flag issues — not rewrite anything.

Review the assets against the campaign brief and check for:
1. Consistency with the campaign objective and key messages
2. Tone of voice alignment (does each asset sound like the same brand?)
3. Anything generic, clichéd, or off-brand

Always respond with valid JSON matching this exact structure:
{
  "overall_assessment": "A short paragraph summarising the overall quality of the campaign assets",
  "issues": [
    {
      "asset": "name of the asset with the issue (e.g. Tagline 2, Instagram Caption, Email Subject Line)",
      "issue": "clear description of the problem",
      "suggested_fix": "specific guidance on what to change and why — do not rewrite the copy"
    }
  ]
}

If no issues are found, return an empty array for issues:
{ "overall_assessment": "...", "issues": [] }"""


class QualityCheckState(TypedDict):
    campaign_brief: dict
    rag_context: dict
    tagline_options: dict
    instagram_post: dict
    email_copy: dict
    review_report: dict


def run_quality_check(state: QualityCheckState) -> QualityCheckState:
    rag_block = ""
    if state.get("rag_context"):
        ctx = state["rag_context"]
        guidelines = "\n\n".join(ctx.get("brand_guidelines", []))
        rag_block = f"\n\nBRAND GUIDELINES (use these as the standard for your review):\n{guidelines}"

    context = f"""CAMPAIGN BRIEF:
{json.dumps(state["campaign_brief"], indent=2)}

TAGLINES (Agent 4):
{json.dumps(state["tagline_options"], indent=2)}

INSTAGRAM POST (Agent 5):
{json.dumps(state["instagram_post"], indent=2)}

EMAIL COPY (Agent 6):
{json.dumps(state["email_copy"], indent=2)}{rag_block}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Review these campaign assets against the brief and flag any issues:\n\n{context}",
            }
        ],
    )

    return {"review_report": parse_json(response.content[0].text)}


def build_quality_check_graph():
    graph = StateGraph(QualityCheckState)
    graph.add_node("run_quality_check", run_quality_check)
    graph.set_entry_point("run_quality_check")
    graph.add_edge("run_quality_check", END)
    return graph.compile()


def run_quality_checker(
    campaign_brief: dict,
    tagline_options: dict,
    instagram_post: dict,
    email_copy: dict,
    rag_context: dict = None,
) -> dict:
    agent = build_quality_check_graph()
    result = agent.invoke({
        "campaign_brief": campaign_brief,
        "rag_context": rag_context or {},
        "tagline_options": tagline_options,
        "instagram_post": instagram_post,
        "email_copy": email_copy,
        "review_report": {},
    })
    return result["review_report"]


if __name__ == "__main__":
    from sample_brief import SAMPLE_BRIEF

    sample_taglines = {
        "taglines": [
            {
                "tagline": "Know Every Hand That Touched It.",
                "explanation": "Speaks directly to greenwashing fatigue and makes transparency feel human."
            },
            {
                "tagline": "From Living Soil to Your Morning Ritual.",
                "explanation": "Anchors the Provenance Ritual campaign while telescoping the farm-to-cup journey."
            },
            {
                "tagline": "Extraordinary Coffee Has Nothing to Hide.",
                "explanation": "Weaponizes the audience's skepticism and turns transparency into a mark of quality."
            }
        ]
    }

    sample_instagram = {
        "caption": "Somewhere on a hillside in Huila, Colombia, Ana Lucia is sorting this morning's harvest by hand.\n\nBy Friday, those same cherries will be in your cup — and you'll know exactly who picked them, what the soil was fed, and why it matters.\n\nThis is The Provenance Ritual. Not a subscription. A standing invitation to explore one extraordinary, regenerative-certified origin at a time.\n\nNo vague claims. No borrowed virtue. Just full transparency from soil to first sip — because you deserve to know the whole story.\n\nReady to meet your next cup? Link in bio.",
        "hashtags": [
            "#TheProvenanceRitual",
            "#RadicalTransparency",
            "#RegenerativeCoffee",
            "#SpecialtyCoffee",
            "#KnowYourFarmer",
            "#SlowLiving",
            "#CoffeeOrigins",
            "#MindfulConsumption"
        ]
    }

    sample_email = {
        "subject_line": "You deserve to know where your coffee's been",
        "body": "Most coffee bags tell you almost nothing. A flag. A vague region. A word like 'sustainable' doing a lot of heavy lifting.\n\nWe do things differently.\n\nEvery bag we ship carries the full story — the specific farm, the soil composition, the regenerative practices quietly restoring the land beneath each harvest. The name of the family who picked it. The elevation. The rain.\n\nNot because we're performing transparency. Because once you taste coffee with a real provenance, everything else feels hollow.\n\nOur sourcing partners don't just avoid harm — they actively rebuild ecosystems. Healthier soil. Better yields. A cup that means something beyond the morning ritual.\n\nThis isn't a subscription you'll forget about. It's a standing invitation — a new origin, a new story, delivered to your door each month.\n\nWe launched The Provenance Ritual for people who are tired of guessing what they're actually buying.\n\nYou seem like one of those people.\n\n→ Explore your first origin and join the ritual today.\n\nFirst bag ships within 48 hours. Cancel anytime — though we've found most people don't want to."
    }

    print("Running Quality Check agent...\n")
    report = run_quality_checker(SAMPLE_BRIEF, sample_taglines, sample_instagram, sample_email)
    print(json.dumps(report, indent=2))
