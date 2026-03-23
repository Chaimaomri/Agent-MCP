"""
Action 6 : Ajout évaluation - CONFORME CDC
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

class EvaluationState(TypedDict):
    user_question: str
    use_real: bool
    candidature_id: Optional[str]
    scores: Optional[dict] 
    commentaire: Optional[str]
    recommandation: Optional[str]  
    candidature_data: Optional[dict]
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

def analyze_intent(state: EvaluationState) -> EvaluationState:
    """Analyse l'intention"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidature_id ("cand_789" pour Chaima/Backend)
    - scores (objet flexible avec compétences et notes sur 5, ex: {{"technique": 4.5, "communication": 4.0, "leadership": 3.5}})
    - commentaire (appréciation qualitative)
    - recommandation (OBLIGATOIRE : "poursuivre" | "attente" | "rejet")
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Recommandation : {data.get('recommandation')}")
        print(f"    Scores : {list(data.get('scores', {}).keys())}")
        
        return {
            **state,
            "candidature_id": data.get("candidature_id", "cand_789"),
            "scores": data.get("scores", {}),
            "commentaire": data.get("commentaire"),
            "recommandation": data.get("recommandation", "attente"),
        }
    
    except Exception as e:
        print(f"     Erreur : {e}")
        return {
            **state,
            "candidature_id": "cand_789",
            "scores": {"global": 3.0},
            "commentaire": state['user_question'],
            "recommandation": "attente",
        }

async def fetch_candidature_async(state: EvaluationState) -> EvaluationState:
    """Récupère la candidature via MCP"""
    print("\n[NŒUD 2] Récupération de la candidature via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidature = await mcp_client.get_resource(f"candidature/{state['candidature_id']}")
        print(f"     {candidature['candidat_nom']} → {candidature['offre_titre']}")
        return {**state, "candidature_data": candidature}
    finally:
        await mcp_client.close()

def fetch_candidature(state: EvaluationState) -> EvaluationState:
    return asyncio.run(fetch_candidature_async(state))

def human_approval(state: EvaluationState) -> EvaluationState:
    """Validation humaine"""
    print("\n" + "="*70)
    print("PREVIEW ÉVALUATION")
    print("="*70)
    
    if state.get('candidature_data'):
        c = state['candidature_data']
        print(f"Candidature : {c['candidat_nom']} → {c['offre_titre']}")
    
    print(f"\nScores :")
    for competence, score in state['scores'].items():
        print(f"  • {competence.capitalize()}: {score}/5")
    
    print(f"\nCommentaire : {state['commentaire']}")
    
    # Traduction recommandation
    reco_fr = {
        "poursuivre": " Poursuivre",
        "attente": " Attente",
        "rejet": " Rejet"
    }
    print(f"Recommandation : {reco_fr.get(state['recommandation'], state['recommandation'])}")
    print("="*70)
    
    choice = input("\n[e] Enregistrer  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    
    elif choice == 'm':
        new_comment = input("Nouveau commentaire (Entrée pour garder) : ").strip()
        if new_comment:
            state["commentaire"] = new_comment
        
        new_reco = input("Nouvelle recommandation (poursuivre/attente/rejet, Entrée pour garder) : ").strip()
        if new_reco in ["poursuivre", "attente", "rejet"]:
            state["recommandation"] = new_reco
        
        print(" Modifié et approuvé")
        return {**state, "human_approved": True}
    
    else:
        print(" Annulé")
        return {**state, "human_approved": False}

async def execute_action_async(state: EvaluationState) -> EvaluationState:
    """Enregistre l'évaluation via MCP"""
    if not state.get("human_approved"):
        return {**state, "result": {"status": "cancelled"}, "final_message": "Évaluation annulée"}
    
    print("\n[NŒUD 4] Enregistrement de l'évaluation via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="ajouter_evaluation",
            parameters={
                "candidature_id": state['candidature_id'],
                "scores": state['scores'],  
                "commentaire": state['commentaire'],
                "recommandation": state['recommandation']
            }
        )
        
        print(f"\n Évaluation enregistrée : {result.get('evaluation_id')}")
        
        return {**state, "result": result, "final_message": "Évaluation enregistrée"}
    
    finally:
        await mcp_client.close()

def execute_action(state: EvaluationState) -> EvaluationState:
    return asyncio.run(execute_action_async(state))

def should_execute(state: EvaluationState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"

# ============================================================================
# GRAPH
# ============================================================================

def build_evaluation_graph():
    g = StateGraph(EvaluationState)
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch", fetch_candidature)
    g.add_node("approve", human_approval)
    g.add_node("execute", execute_action)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch")
    g.add_edge("fetch", "approve")
    g.add_conditional_edges("approve", should_execute, {"execute": "execute", "end": END})
    g.add_edge("execute", END)
    
    return g.compile()

def run_evaluation_agent(user_question: str, use_real: bool = True):
    print("\n" + "="*70)
    print("ACTION 6 - AJOUT ÉVALUATION (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_evaluation_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "candidature_id": None,
        "scores": None,
        "commentaire": None,
        "recommandation": None,
        "candidature_data": None,
        "human_approved": False,
        "result": None,
        "final_message": None,
    })
    
    print(f"\n{'='*70}\nRÉSUMÉ\n{'='*70}")
    print(f"Statut : {final.get('result', {}).get('status')}")
    print(f"Temps  : {time.time() - start:.2f}s\n{'='*70}\n")
    
    return final

if __name__ == "__main__":
    run_evaluation_agent(
        "Ajouter une évaluation pour Chaima : technique 4.5/5, communication 4/5, "
        "recommandation poursuivre"
    )