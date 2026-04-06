"""
Action 3 : Création et affectation de tâche 
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



class TaskState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool  
    candidature_id: Optional[str]  
    task_type: Optional[str]  
    task_description: Optional[str]
    assignee_id: Optional[str]  
    echeance: Optional[str]  
    priorite: Optional[str]
    candidature_data: Optional[dict]  
    human_approved: bool
    result: Optional[dict]
    final_message: Optional[str]



llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=0.2,
)



def analyze_intent(state: TaskState) -> TaskState:
    """Analyse l'intention et extrait les paramètres"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidature_id ("cand_789" pour Chaima/Backend)
    - task_type (OBLIGATOIRE : "relance" | "verification_references" | "preparation_onboarding")
    - task_description (description détaillée)
    - assignee_id ("user_001" pour Sarah, "user_002" pour Thomas, "user_003" pour Agent IA)
    - echeance (date au format YYYY-MM-DD si mentionnée, sinon null)
    - priorite ("haute" | "moyenne" | "basse")
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Type : {data.get('task_type')}")
        print(f"    Assigné à : {data.get('assignee_id')}")
        
        return {
            **state,
            "candidature_id": data.get("candidature_id", "cand_789"),
            "task_type": data.get("task_type", "relance"),
            "task_description": data.get("task_description"),
            "assignee_id": data.get("assignee_id", "user_001"),
            "echeance": data.get("echeance"),
            "priorite": data.get("priorite", "moyenne"),
        }
    
    except Exception as e:
        print(f"     Erreur : {e}")
        return {
            **state,
            "candidature_id": "cand_789",
            "task_type": "relance",
            "task_description": state['user_question'],
            "assignee_id": "user_001",
            "priorite": "moyenne",
        }

async def fetch_candidature_async(state: TaskState) -> TaskState:
    """Récupère la candidature via MCP"""
    print("\n[NŒUD 2] Récupération de la candidature via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidature_id = state.get("candidature_id", "cand_789")
        candidature = await mcp_client.get_resource(f"candidature/{candidature_id}")
        
        print(f"    ✓ Candidature : {candidature['candidat_nom']}")
        print(f"    Offre : {candidature['offre_titre']}")
        
        return {**state, "candidature_data": candidature}
    finally:
        await mcp_client.close()

def fetch_candidature(state: TaskState) -> TaskState:
    return asyncio.run(fetch_candidature_async(state))

def human_approval(state: TaskState) -> TaskState:
    """Validation humaine"""
    
    #  AUTO-APPROVE
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] Tâche approuvée automatiquement")
        return {**state, "human_approved": True}
    
    # SINON : Validation manuelle
    print("\n" + "="*70)
    print("PREVIEW TÂCHE")
    print("="*70)
    
    if state.get('candidature_data'):
        cand = state['candidature_data']
        print(f"Candidature : {cand['candidat_nom']} → {cand['offre_titre']}")
    
    # Traduction type
    types_fr = {
        "relance": "Relance candidat",
        "verification_references": "Vérification références",
        "preparation_onboarding": "Préparation onboarding"
    }
    
    print(f"Type        : {types_fr.get(state['task_type'], state['task_type'])}")
    print(f"Description : {state['task_description']}")
    print(f"Assignée à  : {state['assignee_id']}")
    print(f"Échéance    : {state['echeance'] or 'Non spécifiée'}")
    print(f"Priorité    : {state['priorite']}")
    print("="*70)
    
    choice = input("\n[e] Créer  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    elif choice == 'm':
        new_desc = input("Nouvelle description (Entrée pour garder) : ").strip()
        if new_desc:
            state["task_description"] = new_desc
        print(" Modifié et approuvé")
        return {**state, "human_approved": True}
    else:
        print(" Annulé")
        return {**state, "human_approved": False}

async def execute_action_async(state: TaskState) -> TaskState:
    """Crée la tâche via MCP"""
    if not state.get("human_approved"):
        return {**state, "result": {"status": "cancelled"}, "final_message": "Tâche annulée"}
    
    print("\n[NŒUD 4] Création de la tâche via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="creer_tache",
            parameters={
                "candidature_id": state['candidature_id'],
                "type": state['task_type'],
                "description": state['task_description'],
                "assignee_id": state['assignee_id'],
                "echeance": state['echeance'],
                "priorite": state['priorite']
            }
        )
        
        print(f"\n✓ Tâche créée : {result.get('task_id')}")
        
        return {**state, "result": result, "final_message": "Tâche créée"}
    
    finally:
        await mcp_client.close()

def execute_action(state: TaskState) -> TaskState:
    return asyncio.run(execute_action_async(state))

def should_execute(state: TaskState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"

# ============================================================================
# GRAPH
# ============================================================================

def build_task_graph():
    g = StateGraph(TaskState)
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

def run_task_agent(user_question: str, use_real: bool = True, auto_approve: bool = False):  
    print("\n" + "="*70)
    print("ACTION 3 - CRÉATION TÂCHE (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_task_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,  
        "candidature_id": None,
        "task_type": None,
        "task_description": None,
        "assignee_id": None,
        "echeance": None,
        "priorite": None,
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
    run_task_agent("Créer une tâche de relance pour la candidature de Chaima au poste Backend")