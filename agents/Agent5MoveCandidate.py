"""
Action 5 : Déplacement de candidature - CONFORME CDC
"""

from typing import TypedDict, Literal, Optional, Dict, Any
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


class MoveState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool
    candidature_id: Optional[str]
    etape_cible_id: Optional[str]
    raison: Optional[str]
    candidature_data: Optional[dict]
    etape_actuelle: Optional[dict]
    etape_cible: Optional[dict]
    transition_valide: bool
    transition_error: Optional[str]
    actions_auto: Optional[list]
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



def analyze_intent(state: MoveState) -> MoveState:
    """Analyse l'intention et extrait les paramètres"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidature_id ("cand_789" pour Chaima/Backend)
    - etape_cible_id (ID de l'étape cible, format "step_XXX")
    - raison (raison du déplacement, optionnel)
    
    Étapes disponibles :
    - step_001 : Candidature reçue
    - step_002 : En évaluation
    - step_003 : Entretien RH
    - step_004 : Entretien technique
    - step_005 : Entretien final
    - step_006 : Offre envoyée
    - step_007 : Acceptée
    - step_008 : Rejetée
    
    Si l'utilisateur mentionne un nom d'étape (ex: "Entretien RH"), 
    traduis-le en step_id correspondant.
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Candidature : {data.get('candidature_id', 'cand_789')}")
        print(f"    Étape cible : {data.get('etape_cible_id', 'step_003')}")
        
        return {
            **state,
            "candidature_id": data.get("candidature_id", "cand_789"),
            "etape_cible_id": data.get("etape_cible_id", "step_003"),
            "raison": data.get("raison", "Déplacement manuel"),
        }
    
    except Exception as e:
        print(f"     Erreur parsing JSON : {e}")
        return {
            **state,
            "candidature_id": "cand_789",
            "etape_cible_id": "step_003",
            "raison": "Déplacement manuel",
        }

async def fetch_candidature_async(state: MoveState) -> MoveState:
    """Récupère la candidature via MCP Resource"""
    print("\n[NŒUD 2] Récupération candidature via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidature_id = state.get("candidature_id", "cand_789")
        candidature = await mcp_client.get_resource(f"candidature/{candidature_id}")
        
        print(f"    Candidat : {candidature.get('candidat_nom', 'N/A')}")
        print(f"    Poste : {candidature.get('offre_titre', 'N/A')}")
        print(f"    Étape actuelle : {candidature.get('etape_actuelle_nom', 'N/A')} ({candidature.get('etape_actuelle_id', 'N/A')})")
        
        etape_actuelle = {
            "id": candidature.get("etape_actuelle_id"),
            "nom": candidature.get("etape_actuelle_nom")
        }
        
        return {
            **state,
            "candidature_data": candidature,
            "etape_actuelle": etape_actuelle
        }
    
    finally:
        await mcp_client.close()

def fetch_candidature(state: MoveState) -> MoveState:
    return asyncio.run(fetch_candidature_async(state))

async def fetch_etape_cible_async(state: MoveState) -> MoveState:
    """Récupère l'étape cible via MCP Resource"""
    print("\n[NŒUD 3] Récupération étape cible via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        etape_cible_id = state.get("etape_cible_id", "step_003")
        etape_cible = await mcp_client.get_resource(f"etape/{etape_cible_id}")
        
        print(f"    ✓ Étape cible : {etape_cible.get('nom', 'N/A')} (ordre: {etape_cible.get('ordre', 'N/A')})")
        print(f"    Description : {etape_cible.get('description', 'N/A')}")
        
        actions_auto = etape_cible.get('actions_auto', [])
        if actions_auto:
            print(f"    Actions auto : {', '.join(actions_auto)}")
        
        return {
            **state,
            "etape_cible": etape_cible,
            "actions_auto": actions_auto
        }
    
    finally:
        await mcp_client.close()

def fetch_etape_cible(state: MoveState) -> MoveState:
    return asyncio.run(fetch_etape_cible_async(state))

def validate_transition(state: MoveState) -> MoveState:
    """Valide que la transition est autorisée"""
    print("\n[NŒUD 4] Validation de la transition...")
    
    etape_actuelle = state.get("etape_actuelle", {})
    etape_cible = state.get("etape_cible", {})
    
    etape_actuelle_id = etape_actuelle.get("id")
    etape_cible_id = etape_cible.get("id")
    
    
    if not etape_cible_id:
        return {
            **state,
            "transition_valide": False,
            "transition_error": "Étape cible non trouvée"
        }
    
    if etape_actuelle.get("nom") in ["Acceptée", "Rejetée"]:
        return {
            **state,
            "transition_valide": False,
            "transition_error": f"Impossible de modifier une candidature {etape_actuelle['nom']}"
        }
    
    if etape_actuelle_id == etape_cible_id:
        return {
            **state,
            "transition_valide": False,
            "transition_error": "La candidature est déjà à cette étape"
        }
    
    print(f"     Transition validée : {etape_actuelle.get('nom')} → {etape_cible.get('nom')}")
    
    return {
        **state,
        "transition_valide": True,
        "transition_error": None
    }

def human_approval(state: MoveState) -> MoveState:
    """Validation humaine (OBLIGATOIRE selon CDC)"""
    
    if not state.get("transition_valide"):
        print(f"\n✗ Transition invalide : {state.get('transition_error')}")
        return {**state, "human_approved": False}
    
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] Déplacement approuvé automatiquement")
        return {**state, "human_approved": True}
    
    print("\n" + "="*70)
    print("PREVIEW DÉPLACEMENT CANDIDATURE")
    print("="*70)
    
    if state.get('candidature_data'):
        cand = state['candidature_data']
        print(f"Candidature : {cand.get('candidat_nom', 'N/A')}")
        print(f"Poste       : {cand.get('offre_titre', 'N/A')}")
        print(f"Date        : {cand.get('date_candidature', 'N/A')}")
    
    print("\n┌────────────────────────────────────────┐")
    print("│ DÉPLACEMENT                            │")
    print("├────────────────────────────────────────┤")
    
    etape_actuelle = state.get('etape_actuelle', {})
    etape_cible = state.get('etape_cible', {})
    
    print(f"│ De   :  {etape_actuelle.get('nom', 'N/A'):<30} │")
    print(f"│ Vers :  {etape_cible.get('nom', 'N/A'):<30} │")
    print("│                                        │")
    
    raison = state.get('raison') or 'Déplacement manuel'
    print(f"│ Raison : {raison:<29} │")
    print("└────────────────────────────────────────┘")

    actions_auto = state.get('actions_auto', [])
    if actions_auto:
        print("\n  ACTIONS AUTOMATIQUES :")
        print("┌────────────────────────────────────────┐")
        for action in actions_auto:
            if action == "notifier_candidat":
                print("│   Notifier candidat par email       │")
            elif action == "creer_tache_planification":
                print("│  Créer tâche planification          │")
            elif action == "creer_tache_onboarding":
                print("│  Créer tâche onboarding              │")
        print("└────────────────────────────────────────┘")
    
    print("\n  Cette action va :")
    print("  • Changer le statut de la candidature")
    print("  • Enregistrer dans l'historique")
    if actions_auto:
        print(f"  • Déclencher {len(actions_auto)} action(s) automatique(s)")
    print("  • Créer une trace ATS")
    
    print("="*70)
    
    choice = input("\n[e] Exécuter  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    
    elif choice == 'm':
        print("\n--- Modification ---")
        new_raison = input(f"Nouvelle raison [{state['raison']}] : ").strip()
        if new_raison:
            state["raison"] = new_raison
        
        print(" Modifié et approuvé")
        return {**state, "human_approved": True}
    
    else:
        print(" Annulé")
        return {**state, "human_approved": False}

async def execute_move_async(state: MoveState) -> MoveState:
    """Exécute le déplacement via MCP Tool"""
    if not state.get("human_approved"):
        return {
            **state,
            "result": {"status": "cancelled"},
            "final_message": "Déplacement annulé"
        }
    
    print("\n[NŒUD 6] Exécution du déplacement via MCP Tool...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="deplacer_candidature",
            parameters={
                "candidature_id": state['candidature_id'],
                "etape_cible_id": state['etape_cible_id']
            }
        )
        
        if result.get('status') != 'success':
            error_msg = result.get('error', 'Erreur inconnue')
            print(f"\n✗ Erreur : {error_msg}")
            return {
                **state,
                "result": {"status": "error", "error": error_msg},
                "final_message": f"Erreur : {error_msg}"
            }
            
        print(f"\n✓ Candidature déplacée avec succès")
        print(f"  De : {result['etape_precedente']['nom']}")
        print(f"  Vers : {result['etape_actuelle']['nom']}")
        
        actions_declenchees = result.get('actions_declenchees', [])
        if actions_declenchees:
            print(f"\n  Actions automatiques déclenchées : {len(actions_declenchees)}")
            for action in actions_declenchees:
                action_type = action.get('type', 'unknown')
                action_status = action.get('status', 'unknown')
                if action_type == "email_notification":
                    print(f"     Email notification : {action_status}")
                elif action_type == "task_creation":
                    print(f"     Tâche créée : {action.get('task_id', 'N/A')}")
        
        return {
            **state,
            "result": result,
            "final_message": f"Candidature déplacée : {result['etape_precedente']['nom']} → {result['etape_actuelle']['nom']}"
        }
    
    except Exception as e:
        print(f"\n✗ Erreur MCP : {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "result": {"status": "error", "error": str(e)},
            "final_message": f"Erreur : {e}"
        }
    
    finally:
        await mcp_client.close()

def execute_move(state: MoveState) -> MoveState:
    return asyncio.run(execute_move_async(state))

def should_execute(state: MoveState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"


def build_move_graph():
    g = StateGraph(MoveState)
    
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch_candidature", fetch_candidature)
    g.add_node("fetch_etape", fetch_etape_cible)
    g.add_node("validate", validate_transition)
    g.add_node("approve", human_approval)
    g.add_node("execute", execute_move)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch_candidature")
    g.add_edge("fetch_candidature", "fetch_etape")
    g.add_edge("fetch_etape", "validate")
    g.add_edge("validate", "approve")
    g.add_conditional_edges(
        "approve",
        should_execute,
        {"execute": "execute", "end": END}
    )
    g.add_edge("execute", END)
    
    return g.compile()

def run_move_agent(user_question: str, use_real: bool = True, auto_approve: bool = False):
    """
    Point d'entrée de l'agent de déplacement de candidature
    
    Args:
        user_question: Question/demande de l'utilisateur
        use_real: Utiliser les vraies APIs (legacy, pas utilisé ici)
        auto_approve: Auto-approuver (True pour API, False pour CLI)
    
    Returns:
        État final avec résultat
    """
    print("\n" + "="*70)
    print("ACTION 5 - DÉPLACEMENT CANDIDATURE (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_move_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,
        "candidature_id": None,
        "etape_cible_id": None,
        "raison": None,
        "candidature_data": None,
        "etape_actuelle": None,
        "etape_cible": None,
        "transition_valide": False,
        "transition_error": None,
        "actions_auto": None,
        "human_approved": False,
        "result": None,
        "final_message": None,
    })
    
    print(f"\n{'='*70}\nRÉSUMÉ\n{'='*70}")
    result = final.get('result')
    if result:
        print(f"Statut : {result.get('status')}")
    else:
        print(f"Statut : Aucun résultat (transition invalide ou annulée)")
    print(f"Message : {final.get('final_message')}")
    print(f"Temps  : {time.time() - start:.2f}s\n{'='*70}\n")
    
    return final  

if __name__ == "__main__":
    run_move_agent(
        "Déplacer la candidature de Chaima à l'étape Entretien RH",
        use_real=True,
        auto_approve=False
    )