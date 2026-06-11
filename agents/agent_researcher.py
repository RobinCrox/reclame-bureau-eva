from typing import TypedDict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv, find_dotenv
import json
import os

from rag.indexer import index_all
from rag.chroma_store import query

load_dotenv(find_dotenv(), override=True)

GUIDELINES_COLLECTION = "brand_guidelines"
CAMPAIGNS_COLLECTION = "example_campaigns"


class ResearcherState(TypedDict):
    campaign_brief: dict
    rag_context: dict


def _build_search_query(brief: dict) -> str:
    """Derive a focused search query from the campaign brief."""
    parts = []
    if brief.get("campaign_objective"):
        parts.append(brief["campaign_objective"])
    if brief.get("target_audience_summary"):
        parts.append(brief["target_audience_summary"])
    if brief.get("tone_of_voice"):
        parts.append(brief["tone_of_voice"])
    return " ".join(parts)[:500]


def retrieve_context(state: ResearcherState) -> ResearcherState:
    index_all()

    query_text = _build_search_query(state["campaign_brief"])

    guideline_hits = query(GUIDELINES_COLLECTION, query_text, n_results=3)
    campaign_hits = query(CAMPAIGNS_COLLECTION, query_text, n_results=2)

    rag_context = {
        "brand_guidelines": [h["document"] for h in guideline_hits],
        "similar_campaigns": [
            {
                "title": h["metadata"].get("title", ""),
                "content": h["document"],
                "relevance_score": round(h["score"], 3),
            }
            for h in campaign_hits
        ],
    }

    return {"rag_context": rag_context}


def build_researcher_graph() -> StateGraph:
    graph = StateGraph(ResearcherState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", END)
    return graph.compile()


def run_researcher(campaign_brief: dict) -> dict:
    agent = build_researcher_graph()
    result = agent.invoke({"campaign_brief": campaign_brief, "rag_context": {}})
    return result["rag_context"]


if __name__ == "__main__":
    try:
        from agents.sample_brief import SAMPLE_BRIEF
    except ModuleNotFoundError:
        from sample_brief import SAMPLE_BRIEF

    print("Running Researcher agent...\n")
    context = run_researcher(SAMPLE_BRIEF)
    print("--- Brand Guidelines (top 3 chunks) ---")
    for i, chunk in enumerate(context["brand_guidelines"], 1):
        print(f"\n[{i}] {chunk[:300]}...")
    print("\n--- Similar Campaigns (top 2) ---")
    for camp in context["similar_campaigns"]:
        print(f"\n[{camp['title']}] score={camp['relevance_score']}\n{camp['content'][:300]}...")
