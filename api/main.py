import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

from agents.agent1_analyst import run_analyst
from agents.agent2_strategist import run_strategist
from agents.agent3_brief_writer import run_brief_writer
from agents.agent4_tagline import run_tagline
from agents.agent5_instagram import run_instagram
from agents.agent6_email import run_email
from agents.agent7_quality_check import run_quality_checker
from agents.agent_researcher import run_researcher

app = FastAPI(title="Marketing Campaign System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CampaignRequest(BaseModel):
    product_description: str


@app.get("/")
def root():
    return {"message": "hello world"}


@app.post("/campaign")
async def run_campaign(request: CampaignRequest):
    if not request.product_description.strip():
        raise HTTPException(status_code=400, detail="product_description cannot be empty")

    # Step 1 — Audience & Market Analyst (no RAG — pure market research)
    audience_profile = await asyncio.to_thread(run_analyst, request.product_description)

    # Step RAG — run researcher right after analyst using product description as query
    # Context is shared across all downstream agents
    rag_context = await asyncio.to_thread(run_researcher, request.product_description)

    # Step 2 — Positioning Strategist (uses brand guidelines + past campaign strategies)
    positioning_strategy = await asyncio.to_thread(run_strategist, audience_profile, rag_context)

    # Step 3 — Brief Writer (brief must align with brand guidelines)
    campaign_brief = await asyncio.to_thread(run_brief_writer, audience_profile, positioning_strategy, rag_context)

    # Steps 4, 5, 6 — run in parallel (all use RAG context)
    taglines, instagram_post, email_copy = await asyncio.gather(
        asyncio.to_thread(run_tagline,   campaign_brief, rag_context),
        asyncio.to_thread(run_instagram, campaign_brief, rag_context),
        asyncio.to_thread(run_email,     campaign_brief, rag_context),
    )

    # Step 7 — Quality Check (uses brand guidelines as review standard)
    review_report = await asyncio.to_thread(
        run_quality_checker, campaign_brief, taglines, instagram_post, email_copy, rag_context
    )

    return {
        "audience_profile": audience_profile,
        "positioning_strategy": positioning_strategy,
        "campaign_brief": campaign_brief,
        "taglines": taglines,
        "instagram_post": instagram_post,
        "email_copy": email_copy,
        "review_report": review_report,
    }
