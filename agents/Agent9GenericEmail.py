"""
Action 9 : Envoi Email Générique - CONFORME CDC
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

class EmailState(TypedDict):
    user_question: str
    use_real: bool
    candidat_id: Optional[str]
    email_objet: Optional[str]
    email_contenu: Optional[str]
    type_mail: Optional[str]  
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

def analyze_intent(state: EmailState) -> EmailState:
    """Analyse l'intention"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse : "{state['user_question']}"
    
    Extrais en JSON :
    - candidat_id ("123" pour Chaima)
    - type_mail (OBLIGATOIRE : "suivi" | "relance" | "rejet" | "information")
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Type : {data.get('type_mail', 'information')}")
        
        return {
            **state,
            "candidat_id": data.get("candidat_id", "123"),
            "type_mail": data.get("type_mail", "information"),
        }
    
    except:
        return {
            **state,
            "candidat_id": "123",
            "type_mail": "information",
        }

async def fetch_candidate_async(state: EmailState) -> EmailState:
    """Récupère candidat via MCP"""
    print("\n[NŒUD 2] Récupération candidat via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidate = await mcp_client.get_resource(f"candidat/{state['candidat_id']}")
        print(f"     {candidate['prenom']} {candidate['nom']}")
        print(f"    Email : {candidate['email']}")
        return {**state, "candidate_data": candidate}
    finally:
        await mcp_client.close()

def fetch_candidate(state: EmailState) -> EmailState:
    return asyncio.run(fetch_candidate_async(state))

def generate_email(state: EmailState) -> EmailState:
    """Génère l'email avec adaptation du ton"""
    print("\n[NŒUD 3] Génération de l'email...")
    
    candidate = state['candidate_data']
    
    # ADAPTATION SELON CONTEXTE
    ton_mapping = {
        "suivi": "professionnel et encourageant",
        "relance": "courtois mais ferme",
        "rejet": "respectueux et empathique",
        "information": "neutre et informatif"
    }
    
    ton = ton_mapping.get(state['type_mail'], "professionnel")
    
    prompt = f"""
Tu es un assistant RH chez NextGen Technologies.

Génère un email de type "{state['type_mail']}" pour :
- Candidat : {candidate['prenom']} {candidate['nom']}
- Email : {candidate['email']}
- Contexte : {state['user_question']}

TON : {ton}

RÈGLES STRICTES :
1. Réponds en 2 parties séparées par "---"
2. Partie 1 : Le sujet (une ligne, sans "SUJET:")
3. Partie 2 : Le corps HTML complet

FORMAT :
[Sujet incluant NextGen Technologies si pertinent]
---
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; color: #333;">
<div style="max-width: 600px; margin: 0 auto; padding: 20px;">
<h2 style="color: #2c3e50;">Bonjour {candidate['prenom']},</h2>
<p>[Contenu adapté au type {state['type_mail']}]</p>
<p>Cordialement,</p>
<p><strong>L'équipe NextGen Technologies</strong></p>
</div>
</body>
</html>

INTERDICTIONS :
- NE METS PAS ```html
- NE METS PAS "**Corps HTML**"
- NE METS PAS de commentaires
"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    
    # Nettoyer
    content = content.replace("```html", "").replace("```", "")
    content = content.replace("**Corps HTML**", "").replace("**SUJET**", "")
    
    # Séparer
    parts = content.split("---", 1)
    
    if len(parts) >= 2:
        objet = parts[0].strip().replace("SUJET:", "").strip()
        contenu = parts[1].strip()
    else:
        objet = "Message de NextGen Technologies"
        contenu = content
    
    print(f"    Sujet : {objet[:50]}...")
    
    return {**state, "email_objet": objet, "email_contenu": contenu}

def human_approval(state: EmailState) -> EmailState:
    """Validation humaine"""
    print("\n" + "="*70)
    print("PREVIEW EMAIL")
    print("="*70)
    if state.get('candidate_data'):
        c = state['candidate_data']
        print(f"À     : {c['prenom']} {c['nom']}")
        print(f"Email : {c['email']}")
    print(f"Type  : {state['type_mail']}")
    print(f"Sujet : {state['email_objet']}")
    print("-"*70)
    content_preview = state['email_contenu'][:200] + "..." if len(state['email_contenu']) > 200 else state['email_contenu']
    print(content_preview)
    print("="*70)
    
    choice = input("\n[e] Envoyer  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    
    elif choice == 'm':
        new_objet = input(f"Nouveau sujet [{state['email_objet']}] : ") or state['email_objet']
        new_contenu = input("Nouveau contenu (Entrée pour garder) : ") or state['email_contenu']
        
        print(" Modifié et approuvé")
        return {
            **state,
            "email_objet": new_objet,
            "email_contenu": new_contenu,
            "human_approved": True
        }
    
    else:
        print(" Annulé")
        return {**state, "human_approved": False}

async def send_email_async(state: EmailState) -> EmailState:
    """Envoie l'email via MCP"""
    if not state.get("human_approved"):
        return {**state, "result": {"status": "cancelled"}, "final_message": "Email annulé"}
    
    print("\n[NŒUD 5] Envoi email via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="envoyer_mail",
            parameters={
                "candidat_id": state['candidat_id'],
                "objet": state['email_objet'],
                "contenu": state['email_contenu'],
                "type_mail": state['type_mail']  
            }
        )
        
        status_text = "envoyé" if result['status'] == 'sent' else "simulé"
        print(f"\n Email {status_text} à {result.get('email', state['candidate_data']['email'])}")
        
        return {**state, "result": result, "final_message": f"Email {status_text}"}
    
    except Exception as e:
        print(f"\n Erreur : {e}")
        return {**state, "result": {"status": "error", "error": str(e)}, "final_message": f"Erreur : {e}"}
    
    finally:
        await mcp_client.close()

def send_email(state: EmailState) -> EmailState:
    return asyncio.run(send_email_async(state))

def should_execute(state: EmailState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"

# ============================================================================
# GRAPH
# ============================================================================

def build_email_graph():
    g = StateGraph(EmailState)
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch", fetch_candidate)
    g.add_node("generate", generate_email)
    g.add_node("approve", human_approval)
    g.add_node("send", send_email)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch")
    g.add_edge("fetch", "generate")
    g.add_edge("generate", "approve")
    g.add_conditional_edges("approve", should_execute, {"execute": "send", "end": END})
    g.add_edge("send", END)
    
    return g.compile()

def run_email_agent(user_question: str, use_real: bool = True):
    print("\n" + "="*70)
    print("ACTION 9 - ENVOI EMAIL (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_email_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "candidat_id": None,
        "email_objet": None,
        "email_contenu": None,
        "type_mail": None,
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
    run_email_agent(user_question="Rejette Chaima",  
        use_real=True
        )