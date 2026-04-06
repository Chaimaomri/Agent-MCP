"""
Action 8 : Envoi SMS - CONFORME CDC
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

class SMSState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool  
    candidat_id: Optional[str]
    sms_message: Optional[str]
    type_communication: Optional[str]  
    candidate_data: Optional[dict]
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

def analyze_intent(state: SMSState) -> SMSState:
    """Analyse l'intention"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse : "{state['user_question']}"
    
    Extrais en JSON :
    - candidat_id ("123" pour Chaima)
    - type_communication (OBLIGATOIRE : "rappel" | "confirmation" | "notification")
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Type : {data.get('type_communication', 'rappel')}")
        
        return {
            **state,
            "candidat_id": data.get("candidat_id", "123"),
            "type_communication": data.get("type_communication", "rappel"),
        }
    
    except:
        return {
            **state,
            "candidat_id": "123",
            "type_communication": "rappel",
        }

async def fetch_candidate_async(state: SMSState) -> SMSState:
    """Récupère candidat via MCP"""
    print("\n[NŒUD 2] Récupération candidat via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidate = await mcp_client.get_resource(f"candidat/{state['candidat_id']}")
        print(f"    ✓ {candidate['prenom']} {candidate['nom']}")
        print(f"    Téléphone : {candidate['telephone']}")
        return {**state, "candidate_data": candidate}
    finally:
        await mcp_client.close()

def fetch_candidate(state: SMSState) -> SMSState:
    return asyncio.run(fetch_candidate_async(state))

def generate_sms(state: SMSState) -> SMSState:
    """Génère le SMS"""
    print("\n[NŒUD 3] Génération du SMS...")
    
    candidate = state['candidate_data']
    
    prompt = f"""
    Génère un SMS professionnel court (MAX 160 caractères) :
    
    Candidat : {candidate['prenom']} {candidate['nom']}
    Type : {state['type_communication']}
    Demande : {state['user_question']}
    
    Règles :
    - MAX 160 caractères
    - Professionnel mais courtois
    - Signature : "NextGen" ou "NextGen RH"
    
    Réponds UNIQUEMENT avec le texte du SMS (sans guillemets).
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip().strip('"').strip("'")
    
    if len(content) > 160:
        content = content[:157] + "..."
    
    print(f"    SMS généré ({len(content)} caractères)")
    
    return {**state, "sms_message": content}

def human_approval(state: SMSState) -> SMSState:
    """Validation humaine"""
    
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] SMS approuvé automatiquement")
        return {**state, "human_approved": True}
    
    print("\n" + "="*70)
    print("PREVIEW SMS")
    print("="*70)
    if state.get('candidate_data'):
        c = state['candidate_data']
        print(f"À         : {c['prenom']} {c['nom']}")
        print(f"Téléphone : {c['telephone']}")
    print(f"Type      : {state['type_communication']}")
    print("-"*70)
    print(state['sms_message'])
    print(f"({len(state['sms_message'])} caractères)")
    print("="*70)
    
    choice = input("\n[e] Envoyer  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    elif choice == 'm':
        new_sms = input("Nouveau SMS (max 160 car) : ").strip()
        if new_sms:
            if len(new_sms) > 160:
                new_sms = new_sms[:157] + "..."
            state["sms_message"] = new_sms
        print(" Modifié et approuvé")
        return {**state, "human_approved": True}
    else:
        print(" Annulé")
        return {**state, "human_approved": False}

async def send_sms_async(state: SMSState) -> SMSState:
    """Envoie le SMS via MCP"""
    if not state.get("human_approved"):
        return {**state, "result": {"status": "cancelled"}, "final_message": "SMS annulé"}
    
    print("\n[NŒUD 5] Envoi SMS via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="envoyer_sms",
            parameters={
                "candidat_id": state['candidat_id'],
                "message": state['sms_message'],
                "type_communication": state['type_communication']
            }
        )
        
        if result.get('status') == 'error':
            print(f"\n Erreur : {result.get('error')}")
            return {**state, "result": result, "final_message": f"Erreur : {result.get('error')}"}
        
        status_text = "envoyé" if result['status'] == 'sent' else "simulé"
        telephone = result.get('telephone', state['candidate_data']['telephone'])
        
        print(f"\n SMS {status_text} à {telephone}")
        
        return {**state, "result": result, "final_message": f"SMS {status_text}"}
    
    except Exception as e:
        print(f"\n Erreur MCP : {e}")
        return {**state, "result": {"status": "error", "error": str(e)}, "final_message": f"Erreur : {e}"}
    
    finally:
        await mcp_client.close()

def send_sms(state: SMSState) -> SMSState:
    return asyncio.run(send_sms_async(state))

def should_execute(state: SMSState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"

# ============================================================================
# GRAPH
# ============================================================================

def build_sms_graph():
    g = StateGraph(SMSState)
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch", fetch_candidate)
    g.add_node("generate", generate_sms)
    g.add_node("approve", human_approval)
    g.add_node("send", send_sms)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch")
    g.add_edge("fetch", "generate")
    g.add_edge("generate", "approve")
    g.add_conditional_edges("approve", should_execute, {"execute": "send", "end": END})
    g.add_edge("send", END)
    
    return g.compile()

def run_sms_agent(user_question: str, use_real: bool = True, auto_approve: bool = False):  
    print("\n" + "="*70)
    print("ACTION 8 - ENVOI SMS (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_sms_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,  
        "candidat_id": None,
        "sms_message": None,
        "type_communication": None,
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
    run_sms_agent("Envoyer un SMS de rappel RDV demain 14h à Chaima", use_real=True)