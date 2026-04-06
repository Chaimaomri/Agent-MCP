"""
Action 1 : Génération Kit d'Entretien PDF 
"""

from typing import TypedDict, Literal, Optional, Dict, Any, List
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


class PDFState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool
    candidature_id: Optional[str]
    poste_id: Optional[str]
    candidature_data: Optional[dict]
    candidat_data: Optional[dict]
    poste_data: Optional[dict]
    interview_kit: Optional[dict]
    human_approved: bool
    result: Optional[dict]
    final_message: Optional[str]


llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=0.4,
)


def analyze_intent(state: PDFState) -> PDFState:
    """Analyse l'intention et extrait candidature_id + poste_id"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidature_id ("cand_789" pour Chaima/Backend)
    - poste_id ("456" pour Backend Senior)
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        candidature_id = data.get('candidature_id', 'cand_789')
        poste_id = data.get('poste_id', '456')
        
        print(f"    Candidature ID : {candidature_id}")
        print(f"    Poste ID : {poste_id}")
        
        return {
            **state,
            "candidature_id": candidature_id,
            "poste_id": poste_id,
        }
    
    except Exception as e:
        print(f"     Erreur parsing JSON : {e}")
        return {
            **state,
            "candidature_id": "cand_789",
            "poste_id": "456",
        }


async def fetch_candidature_data_async(state: PDFState) -> PDFState:
    """Récupère la candidature via MCP Resource"""
    print("\n[NŒUD 2] Récupération candidature via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidature_id = state.get("candidature_id", "cand_789")
        candidature = await mcp_client.get_resource(f"candidature/{candidature_id}")
        
        print(f"     Candidature : {candidature.get('candidat_nom', 'N/A')}")
        print(f"    Poste : {candidature.get('offre_titre', 'N/A')}")
        
        # Récupère aussi le candidat complet
        candidat_id = candidature.get('candidat_id', '123')
        candidat = await mcp_client.get_resource(f"candidat/{candidat_id}")
        
        print(f"     Candidat : {candidat.get('prenom', '')} {candidat.get('nom', '')}")
        print(f"    Compétences : {len(candidat.get('competences', []))} compétences")
        print(f"    Expériences : {len(candidat.get('experiences', []))} expériences")
        
        return {
            **state,
            "candidature_data": candidature,
            "candidat_data": candidat
        }
    
    finally:
        await mcp_client.close()


def fetch_candidature_data(state: PDFState) -> PDFState:
    return asyncio.run(fetch_candidature_data_async(state))


async def fetch_poste_data_async(state: PDFState) -> PDFState:
    """Récupère l'offre/poste via MCP Resource"""
    print("\n[NŒUD 3] Récupération offre/poste via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        poste_id = state.get("poste_id", "456")
        poste = await mcp_client.get_resource(f"offre/{poste_id}")
        
        print(f"     Poste : {poste.get('titre', 'N/A')}")
        print(f"    Compétences requises : {len(poste.get('competences_requises', []))}")
        
        return {
            **state,
            "poste_data": poste
        }
    
    finally:
        await mcp_client.close()


def fetch_poste_data(state: PDFState) -> PDFState:
    return asyncio.run(fetch_poste_data_async(state))


def generate_interview_kit(state: PDFState) -> PDFState:
    """Génère le kit d'entretien via LLM"""
    print("\n[NŒUD 4] Génération kit d'entretien...")
    
    candidat = state.get('candidat_data', {})
    poste = state.get('poste_data', {})
    
    # Construction du prompt pour le LLM
    prompt = f"""
    Tu es un expert en recrutement. Génère un kit d'entretien complet et structuré.
    
    CANDIDAT :
    - Nom : {candidat.get('prenom', '')} {candidat.get('nom', '')}
    - Compétences : {json.dumps(candidat.get('competences', []))}
    - Expériences : {json.dumps(candidat.get('experiences', []), indent=2)}
    
    POSTE :
    - Titre : {poste.get('titre', '')}
    - Compétences requises : {json.dumps(poste.get('competences_requises', []))}
    - Localisation : {poste.get('localisation', '')}
    
    GÉNÈRE UN KIT AVEC CES 5 SECTIONS :
    
    1. GRILLE D'ÉVALUATION PONDÉRÉE
       - Liste les compétences requises
       - Attribue un poids (%) à chaque compétence (total = 100%)
       - Format : {{"competence": "Python", "poids": 30}}
    
    2. QUESTIONS TECHNIQUES (5-8 questions)
       - Questions spécifiques aux compétences requises
       - Variées : théoriques, pratiques, cas d'usage
       - Format : {{"competence": "Python", "question": "..."}}
    
    3. QUESTIONS COMPORTEMENTALES (4-6 questions)
       - Méthode STAR (Situation, Tâche, Action, Résultat)
       - Travail d'équipe, résolution problèmes, leadership
       - Format : {{"categorie": "Travail d'équipe", "question": "..."}}
    
    4. CRITÈRES DE NOTATION
       - Description des niveaux 1/5 à 5/5
       - Spécifique au contexte du poste
    
    5. POINTS D'ATTENTION SPÉCIFIQUES
       - Analyse du profil du candidat
       - Points forts à valoriser
       - Zones d'ombre à clarifier
       - Questions prioritaires
    
    Réponds UNIQUEMENT avec un JSON structuré selon ce format :
    {{
        "grille_evaluation": [
            {{"competence": "Python", "poids": 30}},
            {{"competence": "Django", "poids": 25}}
        ],
        "questions_techniques": [
            {{"competence": "Python", "question": "Expliquez les décorateurs"}},
            {{"competence": "Django", "question": "Différence entre select_related et prefetch_related ?"}}
        ],
        "questions_comportementales": [
            {{"categorie": "Résolution problèmes", "question": "Racontez une situation où..."}}
        ],
        "criteres_notation": {{
            "5": "Expert - Maîtrise parfaite...",
            "4": "Avancé - Autonome...",
            "3": "Intermédiaire - Besoin accompagnement...",
            "2": "Débutant - Formation nécessaire...",
            "1": "Novice - Aucune expérience..."
        }},
        "points_attention": [
            "Expérience solide : 5 ans Backend",
            "Docker mentionné mais peu détaillé → À creuser"
        ]
    }}
    
    Réponds UNIQUEMENT avec le JSON, aucun texte avant ou après.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        interview_kit = json.loads(content)
        
        print(f"    ✓ Kit généré")
        print(f"      Grille évaluation : {len(interview_kit.get('grille_evaluation', []))} compétences")
        print(f"      Questions techniques : {len(interview_kit.get('questions_techniques', []))}")
        print(f"      Questions comportementales : {len(interview_kit.get('questions_comportementales', []))}")
        
        return {
            **state,
            "interview_kit": interview_kit
        }
    
    except Exception as e:
        print(f"    ⚠ Erreur parsing JSON : {e}")
        print(f"    Response brute : {response.content[:500]}")
        
        # Kit par défaut si erreur
        return {
            **state,
            "interview_kit": {
                "grille_evaluation": [],
                "questions_techniques": [],
                "questions_comportementales": [],
                "criteres_notation": {},
                "points_attention": []
            }
        }


def human_approval(state: PDFState) -> PDFState:
    """Validation humaine (OBLIGATOIRE selon CDC)"""
    
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] Kit approuvé automatiquement")
        return {**state, "human_approved": True}
    
    print("\n" + "="*70)
    print("PREVIEW KIT D'ENTRETIEN")
    print("="*70)
    
    candidat = state.get('candidat_data', {})
    poste = state.get('poste_data', {})
    interview_kit = state.get('interview_kit', {})
    
    print(f"\nCandidat : {candidat.get('prenom', '')} {candidat.get('nom', '')}")
    print(f"Poste    : {poste.get('titre', '')}")
    
    # Grille évaluation
    grille = interview_kit.get('grille_evaluation', [])
    if grille:
        print(f"\n GRILLE D'ÉVALUATION ({len(grille)} compétences)")
        print("┌────────────────────────────────┬──────────┐")
        for item in grille[:5]:  # Affiche les 5 premières
            comp = item.get('competence', 'N/A')
            poids = item.get('poids', 0)
            print(f"│ {comp:<30} │ {poids:>3}%     │")
        if len(grille) > 5:
            print(f"│ ... et {len(grille) - 5} autres{' ' * 15}│          │")
        print("└────────────────────────────────┴──────────┘")
    
    # Questions techniques
    questions_tech = interview_kit.get('questions_techniques', [])
    print(f"\n QUESTIONS TECHNIQUES : {len(questions_tech)}")
    for i, q in enumerate(questions_tech[:3], 1):
        print(f"   {i}. [{q.get('competence', 'N/A')}] {q.get('question', '')[:60]}...")
    if len(questions_tech) > 3:
        print(f"   ... et {len(questions_tech) - 3} autres")
    
    # Questions comportementales
    questions_comp = interview_kit.get('questions_comportementales', [])
    print(f"\n QUESTIONS COMPORTEMENTALES : {len(questions_comp)}")
    for i, q in enumerate(questions_comp[:2], 1):
        print(f"   {i}. {q.get('question', '')[:60]}...")
    
    # Points d'attention
    points = interview_kit.get('points_attention', [])
    if points:
        print(f"\n POINTS D'ATTENTION : {len(points)}")
        for point in points[:3]:
            print(f"   • {point}")
    
    print("="*70)
    
    choice = input("\n[e] Exécuter (Générer PDF)  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    else:
        print(" Annulé")
        return {**state, "human_approved": False}


async def create_pdf_kit_async(state: PDFState) -> PDFState:
    """Génère le PDF via MCP Tool"""
    if not state.get("human_approved"):
        return {
            **state,
            "result": {"status": "cancelled"},
            "final_message": "Génération PDF annulée"
        }
    
    print("\n[NŒUD 6] Génération PDF via MCP Tool...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="creer_kit_entretien",
            parameters={
                "candidature_id": state.get('candidature_id'),
                "poste_id": state.get('poste_id'),
                "interview_kit": state.get('interview_kit'),
                "candidat_data": state.get('candidat_data'),
                "poste_data": state.get('poste_data')
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
        
        pdf_path = result.get('pdf_path', '')
        print(f"\n✓ PDF généré avec succès")
        print(f"  Fichier : {pdf_path}")
        
        return {
            **state,
            "result": result,
            "final_message": f"Kit d'entretien généré : {pdf_path}"
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


def create_pdf_kit(state: PDFState) -> PDFState:
    return asyncio.run(create_pdf_kit_async(state))


def should_execute(state: PDFState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"


def build_pdf_graph():
    g = StateGraph(PDFState)
    
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch_candidature", fetch_candidature_data)
    g.add_node("fetch_poste", fetch_poste_data)
    g.add_node("generate", generate_interview_kit)
    g.add_node("approve", human_approval)
    g.add_node("execute", create_pdf_kit)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch_candidature")
    g.add_edge("fetch_candidature", "fetch_poste")
    g.add_edge("fetch_poste", "generate")
    g.add_edge("generate", "approve")
    g.add_conditional_edges(
        "approve",
        should_execute,
        {"execute": "execute", "end": END}
    )
    g.add_edge("execute", END)
    
    return g.compile()


def run_pdf_agent(user_question: str, use_real: bool = True, auto_approve: bool = False):
    """
    Point d'entrée de l'agent de génération kit PDF
    
    Args:
        user_question: Question/demande de l'utilisateur
        use_real: Utiliser les vraies APIs (legacy, pas utilisé ici)
        auto_approve: Auto-approuver (True pour API, False pour CLI)
    
    Returns:
        État final avec résultat
    """
    print("\n" + "="*70)
    print("ACTION 1 - GÉNÉRATION KIT D'ENTRETIEN PDF (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_pdf_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,
        "candidature_id": None,
        "poste_id": None,
        "candidature_data": None,
        "candidat_data": None,
        "poste_data": None,
        "interview_kit": None,
        "human_approved": False,
        "result": None,
        "final_message": None,
    })
    
    print(f"\n{'='*70}\nRÉSUMÉ\n{'='*70}")
    result = final.get('result')
    if result:
        print(f"Statut : {result.get('status')}")
    else:
        print(f"Statut : Aucun résultat (annulé)")
    print(f"Message : {final.get('final_message')}")
    print(f"Temps  : {time.time() - start:.2f}s\n{'='*70}\n")
    
    return final


if __name__ == "__main__":
    run_pdf_agent(
        "Générer un kit d'entretien pour la candidature de Chaima au poste de Développeur Backend Senior",
        use_real=True,
        auto_approve=False
    )
