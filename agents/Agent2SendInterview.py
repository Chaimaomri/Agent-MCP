"""
Action 2 : Convocation entretien 
"""

from typing import TypedDict, Literal, Optional, List, Dict
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
import json
import time
import asyncio
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from mcp_client import MCPClient

# ============================================================================
# STATE
# ============================================================================

class InterviewState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool
    candidature_id: Optional[str]
    candidat_id: Optional[str]
    candidat_nom: Optional[str]  # Nom complet du Resource
    candidat_prenom: Optional[str]  # Extrait du nom complet
    candidat_email: Optional[str]
    poste: Optional[str]
    type_entretien: Optional[str]
    creneaux: Optional[List[Dict[str, str]]]
    lien_visio: Optional[str]
    email_objet: Optional[str]
    email_corps: Optional[str]
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

def analyze_intent(state: InterviewState) -> InterviewState:
    """Analyse l'intention et extrait les paramètres"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidature_id ("cand_789" pour Chaima/Backend)
    - type_entretien (OBLIGATOIRE : "technique" | "rh" | "final" | "culture")
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        print(f"    Type entretien : {data.get('type_entretien', 'technique')}")
        
        return {
            **state,
            "candidature_id": data.get("candidature_id", "cand_789"),
            "type_entretien": data.get("type_entretien", "technique"),
        }
    
    except Exception as e:
        print(f"     Erreur parsing JSON : {e}")
        return {
            **state,
            "candidature_id": "cand_789",
            "type_entretien": "technique",
        }

async def fetch_candidature_async(state: InterviewState) -> InterviewState:
    """Récupère la candidature via MCP Resource"""
    print("\n[NŒUD 2] Récupération candidature via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidature_id = state.get("candidature_id", "cand_789")
        candidature = await mcp_client.get_resource(f"candidature/{candidature_id}")
        
        nom_complet = candidature.get('candidat_nom', 'Candidat')
        
        parts = nom_complet.split(' ', 1)
        prenom = parts[0] if len(parts) > 0 else 'Candidat'
        nom = parts[1] if len(parts) > 1 else ''
        
        candidat_id = candidature.get('candidat_id', candidature.get('id', '123'))
        
        print(f"    ✓ Candidat : {nom_complet}")
        print(f"    Email : {candidature['candidat_email']}")
        print(f"    Poste : {candidature['offre_titre']}")
        
        return {
            **state,
            "candidature_data": candidature,
            "candidat_id": candidat_id,
            "candidat_nom": nom,  # Nom seul
            "candidat_prenom": prenom,  # Prénom extrait
            "candidat_email": candidature['candidat_email'],
            "poste": candidature['offre_titre']
        }
    finally:
        await mcp_client.close()

def fetch_candidature(state: InterviewState) -> InterviewState:
    return asyncio.run(fetch_candidature_async(state))

def generate_creneaux(state: InterviewState) -> InterviewState:
    """Génère des créneaux pour l'entretien"""
    print("\n[NŒUD 3] Génération des créneaux...")
    
    # Générer 2 créneaux dans les prochains jours (CDC : minimum 2 créneaux)
    creneaux = []
    base_date = datetime.now() + timedelta(days=2)
    
    # Créneau 1 : Dans 2 jours à 14h
    creneaux.append({
        "date": base_date.strftime("%Y-%m-%d"),
        "heure": "14:00",
        "duree": "1h"
    })
    
    # Créneau 2 : Dans 3 jours à 15h
    creneaux.append({
        "date": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "heure": "15:00",
        "duree": "1h"
    })
    
    # Lien visio 
    lien_visio = "https://meet.google.com/nextgen-entretien-tech"
    
    print(f"    ✓ {len(creneaux)} créneaux générés")
    for i, c in enumerate(creneaux, 1):
        print(f"      {i}. {c['date']} à {c['heure']} ({c['duree']})")
    print(f"    Lien visio : {lien_visio}")
    
    return {**state, "creneaux": creneaux, "lien_visio": lien_visio}

def generate_email(state: InterviewState) -> InterviewState:
    """Génère l'objet et le corps HTML de l'email"""
    print("\n[NŒUD 4] Génération de l'email...")
    
    candidat = state['candidature_data']
    type_entretien = state['type_entretien']
    creneaux = state['creneaux']
    prenom = state['candidat_prenom']
    
    types_fr = {
        "technique": "Entretien technique",
        "rh": "Entretien RH",
        "final": "Entretien final",
        "culture": "Entretien culture d'entreprise"
    }
    
    type_label = types_fr.get(type_entretien, "Entretien")
    
    objet = f"Convocation - {type_label} - {state['poste']}"
    
    creneaux_html = ""
    for i, creneau in enumerate(creneaux, 1):
        # Formater la date en français
        date_obj = datetime.strptime(creneau['date'], "%Y-%m-%d")
        date_fr = date_obj.strftime("%A %d %B %Y")
        
        creneaux_html += f"""
        <li style="padding: 15px; background: white; margin: 10px 0; border-left: 4px solid #3498db; border-radius: 4px;">
            <strong>Créneau {i}</strong><br>
             {date_fr}<br>
             {creneau['heure']}<br>
             Durée : {creneau['duree']}
        </li>
        """
    
    # Corps HTML complet
    corps_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 20px;
            background-color: #f9f9f9;
        }}
        .content h2 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .info-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        .creneaux {{
            list-style: none;
            padding: 0;
            margin: 20px 0;
        }}
        .visio-link {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 5px;
            margin: 15px 0;
            font-weight: 600;
        }}
        .visio-link:hover {{
            background: #2980b9;
        }}
        .footer {{
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- En-tête -->
        <div class="header">
            <h1> NextGen Technologies</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Département Recrutement</p>
        </div>
        
        <!-- Contenu -->
        <div class="content">
            <h2>Bonjour {prenom},</h2>
            
            <p>Nous avons le plaisir de vous convier à un <strong>{type_label}</strong> pour le poste de <strong>{state['poste']}</strong>.</p>
            
            <div class="info-box">
                <h3 style="margin-top: 0; color: #667eea;">📋 Détails de l'entretien</h3>
                <p><strong>Type :</strong> {type_label}</p>
                <p><strong>Poste :</strong> {state['poste']}</p>
                <p><strong>Format :</strong> Visioconférence</p>
            </div>
            
            <h3>🗓️ Créneaux disponibles</h3>
            <p>Merci de choisir <strong>l'un des créneaux suivants</strong> et de nous confirmer votre disponibilité :</p>
            
            <ul class="creneaux">
                {creneaux_html}
            </ul>
            
            <h3> Lien de visioconférence</h3>
            <p>L'entretien se déroulera en visioconférence. Voici le lien de connexion :</p>
            <a href="{state['lien_visio']}" class="visio-link">🔗 Rejoindre la visioconférence</a>
            <p style="font-size: 12px; color: #666;">Lien : {state['lien_visio']}</p>
            
            <div class="info-box" style="border-left-color: #f39c12;">
                <h3 style="margin-top: 0; color: #f39c12;">⚠️ Important</h3>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    <li>Merci de confirmer votre disponibilité en répondant à cet email</li>
                    <li>Prévoyez une connexion internet stable</li>
                    <li>Testez votre caméra et micro avant l'entretien</li>
                    <li>Rejoignez la réunion 5 minutes en avance</li>
                </ul>
            </div>
            
            <p>Nous nous réjouissons de vous rencontrer et d'échanger avec vous sur votre parcours et vos motivations.</p>
            
            <p style="margin-top: 30px;">
                Cordialement,<br>
                <strong>L'équipe Recrutement NextGen Technologies</strong>
            </p>
        </div>
        
        <!-- Pied de page -->
        <div class="footer">
            <p>NextGen Technologies | Recrutement</p>
            <p style="font-size: 11px; color: #999;">
                Cet email a été envoyé automatiquement par notre système de gestion des candidatures.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    print(f"     Email généré")
    print(f"    Objet : {objet}")
    print(f"    Corps : {len(corps_html)} caractères")
    
    return {**state, "email_objet": objet, "email_corps": corps_html}

def human_approval(state: InterviewState) -> InterviewState:
    """Validation humaine (CDC : prévisualisation + modification + confirmation)"""
    
    #  AUTO-APPROVE pour API
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] Convocation approuvée automatiquement")
        return {**state, "human_approved": True}
    
    print("\n" + "="*70)
    print("PREVIEW CONVOCATION ENTRETIEN")
    print("="*70)
    
    if state.get('candidature_data'):
        cand = state['candidature_data']
        print(f"Candidat  : {cand.get('candidat_nom', 'N/A')}")
        print(f"Email     : {cand['candidat_email']}")
        print(f"Poste     : {cand['offre_titre']}")
    
    types_fr = {
        "technique": "🔧 Technique",
        "rh": " RH",
        "final": " Final",
        "culture": " Culture"
    }
    
    print(f"Type      : {types_fr.get(state['type_entretien'], state['type_entretien'])}")
    print(f"\nCréneaux proposés :")
    for i, creneau in enumerate(state['creneaux'], 1):
        print(f"  {i}. {creneau['date']} à {creneau['heure']} ({creneau['duree']})")
    print(f"\nLien visio : {state['lien_visio']}")
    print(f"Objet email : {state['email_objet']}")
    print("="*70)
    
    choice = input("\n[e] Envoyer  [m] Modifier  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print("✓ Approuvé")
        return {**state, "human_approved": True}
    
    elif choice == 'm':
        print("\n--- Modification ---")
        new_objet = input(f"Nouveau sujet [{state['email_objet']}] : ").strip()
        if new_objet:
            state["email_objet"] = new_objet
        
        new_lien = input(f"Nouveau lien visio [{state['lien_visio']}] : ").strip()
        if new_lien:
            state["lien_visio"] = new_lien
            state["email_corps"] = state["email_corps"].replace(
                state.get("lien_visio", ""),
                new_lien
            )
        
        print(" Modifié et approuvé")
        return {**state, "human_approved": True}
    
    else:
        print(" Annulé")
        return {**state, "human_approved": False}

async def send_convocation_async(state: InterviewState) -> InterviewState:
    """Envoie la convocation via MCP Tool (CDC : trace ATS)"""
    if not state.get("human_approved"):
        return {
            **state,
            "result": {"status": "cancelled"},
            "final_message": "Convocation annulée"
        }
    
    print("\n[NŒUD 6] Envoi convocation via MCP Tool...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="envoyer_mail_entretien",
            parameters={
                "candidat_id": state['candidat_id'],
                "candidat_email": state['candidat_email'],
                "objet": state['email_objet'],
                "corps_html": state['email_corps'],
                "type_entretien": state['type_entretien'],
                "creneaux": state['creneaux'],
                "lien_visio": state['lien_visio']
            }
        )
        
        if not result.get('success'):
            error_msg = result.get('error', 'Erreur inconnue')
            print(f"\n Erreur : {error_msg}")
            return {
                **state,
                "result": {"status": "error", "error": error_msg},
                "final_message": f"Erreur : {error_msg}"
            }
        
        print(f"\n Email de convocation envoyé")
        print(f"  Message ID : {result.get('mail_id')}")
        print(f"  Créneaux : {result.get('creneaux_count')}")
        print(f"  Trace ATS : Enregistrée")
        
        nom_complet = f"{state['candidat_prenom']} {state['candidat_nom']}".strip()
        
        return {
            **state,
            "result": {
                "status": "sent",
                "email_id": result.get('mail_id'),
                "candidat_nom": nom_complet,
                "candidat_email": state['candidat_email'],
                "poste": state['poste'],
                "type_entretien": state['type_entretien'],
                "creneaux_count": len(state['creneaux']),
                "lien_visio": state['lien_visio'],
                "trace_enregistree": True
            },
            "final_message": "Convocation envoyée avec succès"
        }
    
    except Exception as e:
        print(f"\n Erreur MCP : {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "result": {"status": "error", "error": str(e)},
            "final_message": f"Erreur : {e}"
        }
    
    finally:
        await mcp_client.close()

def send_convocation(state: InterviewState) -> InterviewState:
    return asyncio.run(send_convocation_async(state))

def should_execute(state: InterviewState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"

# ============================================================================
# GRAPH (CDC : orchestration LangGraph)
# ============================================================================

def build_interview_graph():
    g = StateGraph(InterviewState)
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch", fetch_candidature)
    g.add_node("gen_creneaux", generate_creneaux)
    g.add_node("gen_email", generate_email)
    g.add_node("approve", human_approval)
    g.add_node("send", send_convocation)
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch")
    g.add_edge("fetch", "gen_creneaux")
    g.add_edge("gen_creneaux", "gen_email")
    g.add_edge("gen_email", "approve")
    g.add_conditional_edges(
        "approve",
        should_execute,
        {"execute": "send", "end": END}
    )
    g.add_edge("send", END)
    
    return g.compile()

def run_interview_agent(user_question: str, use_real: bool = True, auto_approve: bool = False):
    """
    Point d'entrée de l'agent de convocation entretien
    
    Args:
        user_question: Question/demande de l'utilisateur
        use_real: Utiliser les vraies APIs (Resend)
        auto_approve: Auto-approuver (True pour API, False pour CLI)
    
    Returns:
        État final avec résultat
    """
    print("\n" + "="*70)
    print("ACTION 2 - CONVOCATION ENTRETIEN (ADAPTÉ AU RESOURCE)")
    print("="*70)
    
    start = time.time()
    graph = build_interview_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,
        "candidature_id": None,
        "candidat_id": None,
        "candidat_nom": None,
        "candidat_prenom": None,
        "candidat_email": None,
        "poste": None,
        "type_entretien": None,
        "creneaux": None,
        "lien_visio": None,
        "email_objet": None,
        "email_corps": None,
        "candidature_data": None,
        "human_approved": False,
        "result": None,
        "final_message": None,
    })
    
    print(f"\n{'='*70}\nRÉSUMÉ\n{'='*70}")
    print(f"Statut : {final.get('result', {}).get('status')}")
    print(f"Message : {final.get('final_message')}")
    print(f"Temps  : {time.time() - start:.2f}s\n{'='*70}\n")
    
    return final

run_interview_workflow = run_interview_agent
if __name__ == "__main__":
    run_interview_agent(
        "Convoquer Chaima pour un entretien technique mardi prochain",
        use_real=True,
        auto_approve=False
    )