"""
Action 4 : Ajout commentaire candidat - CONFORME CDC
"""

from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
import json
import time
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from mcp_client import MCPClient

# ============================================================================
# STATE
# ============================================================================

class CommentState(TypedDict):
    user_question: str
    use_real: bool
    candidat_id: Optional[str]
    comment_content: Optional[str]
    comment_category: Optional[str] 
    candidate_data: Optional[dict]
    human_approved: bool
    result: Optional[dict]
    final_message: Optional[str]

# ============================================================================
# LLM
# ============================================================================

llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=0.2,
)

# ============================================================================
# NŒUDS
# ============================================================================

def analyze_intent(state: CommentState) -> CommentState:
    """Analyse l'intention"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidat_id ("123" pour Chaima)
    - comment_content (le contenu du commentaire à ajouter)
    - comment_category (optionnel : "entretien" | "relance" | "decision" | "observation" | null)
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Catégorie : {data.get('comment_category', 'non spécifiée')}")
        
        return {
            **state,
            "candidat_id": data.get("candidat_id", "123"),
            "comment_content": data.get("comment_content"),
            "comment_category": data.get("comment_category"),  # Peut être None
        }
    
    except Exception as e:
        print(f"     Erreur : {e}")
        return {
            **state,
            "candidat_id": "123",
            "comment_content": state['user_question'],
            "comment_category": None,
        }

async def fetch_candidate_async(state: CommentState) -> CommentState:
    """Récupère le candidat via MCP"""
    print("\n[NŒUD 2] Récupération du candidat via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidate = await mcp_client.get_resource(f"candidat/{state['candidat_id']}")
        print(f"     {candidate['prenom']} {candidate['nom']}")
        return {**state, "candidate_data": candidate}
    finally:
        await mcp_client.close()

def fetch_candidate(state: CommentState) -> CommentState:
    return asyncio.run(fetch_candidate_async(state))

def human_approval(state: CommentState) -> CommentState:
    """Validation humaine"""
    print("\n" + "="*70)
    print("PREVIEW COMMENTAIRE")
    print("="*70)
    
    if state.get('candidate_data'):
        c = state['candidate_data']
        print(f"Candidat  : {c['prenom']} {c['nom']}")
    
    print(f"Catégorie : {state['comment_category'] or 'Non spécifiée'}")
    print(f"Contenu   :\n{state['comment_content']}")
    print("="*70)
    
    choice = input("\n[e] Ajouter  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print("Approuvé")
        return {**state, "human_approved": True}
    
    elif choice == 'm':
        new_content = input("Nouveau contenu (Entrée pour garder) : ").strip()
        if new_content:
            state["comment_content"] = new_content
        print("Modifié et approuvé")
        return {**state, "human_approved": True}
    
    else:
        print("Annulé")
        return {**state, "human_approved": False}

async def execute_action_async(state: CommentState) -> CommentState:
    """Ajoute le commentaire via MCP"""
    if not state.get("human_approved"):
        return {**state, "result": {"status": "cancelled"}, "final_message": "Commentaire annulé"}
    
    print("\n[NŒUD 4] Ajout du commentaire via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="ajouter_commentaire",
            parameters={
                "candidat_id": state['candidat_id'],
                "contenu": state['comment_content'],
                "categorie": state['comment_category']  # Peut être None
            }
        )
        
        print(f"\n Commentaire ajouté : {result.get('comment_id')}")
        
        return {**state, "result": result, "final_message": "Commentaire ajouté"}
    
    finally:
        await mcp_client.close()

def execute_action(state: CommentState) -> CommentState:
    return asyncio.run(execute_action_async(state))

def should_execute(state: CommentState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"

# ============================================================================
# GRAPH
# ============================================================================

def build_comment_graph():
    g = StateGraph(CommentState)
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch", fetch_candidate)
    g.add_node("approve", human_approval)
    g.add_node("execute", execute_action)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch")
    g.add_edge("fetch", "approve")
    g.add_conditional_edges("approve", should_execute, {"execute": "execute", "end": END})
    g.add_edge("execute", END)
    
    return g.compile()

def run_comment_agent(user_question: str, use_real: bool = True):
    print("\n" + "="*70)
    print("ACTION 4 - AJOUT COMMENTAIRE (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_comment_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "candidat_id": None,
        "comment_content": None,
        "comment_category": None,
        "candidate_data": None,
        "human_approved": False,
        "result": None,
        "final_message": None,
    })
    
    print(f"\n{'='*70}\nRÉSUMÉ\n{'='*70}")
    print(f"Statut : {final.get('result', {}).get('status')}")
    print(f"Temps  : {time.time() - start:.2f}s\n{'='*70}\n")
    
    return final

if __name__ == "__main__":
    run_comment_agent("Ajouter un commentaire : Chaima a confirmé sa disponibilité pour l'entretien")