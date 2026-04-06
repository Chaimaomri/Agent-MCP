"""
Action 7 : Détection d'incohérences 
"""

from typing import TypedDict, Literal, Optional, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
import json
import time
import asyncio
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from mcp_client import MCPClient


class AnalyzeState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool
    candidat_id: Optional[str]
    candidat_data: Optional[dict]
    inconsistencies: Optional[list]
    coherence_score: Optional[int]
    recommendations: Optional[list]
    human_approved: bool
    result: Optional[dict]
    final_message: Optional[str]


llm = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=0.3,
)


def analyze_intent(state: AnalyzeState) -> AnalyzeState:
    """Analyse l'intention et extrait le candidat_id"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidat_id ("123" pour Chaima)
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        candidat_id = data.get('candidat_id', '123')
        print(f"    Candidat ID : {candidat_id}")
        
        return {
            **state,
            "candidat_id": candidat_id,
        }
    
    except Exception as e:
        print(f"     Erreur parsing JSON : {e}")
        return {
            **state,
            "candidat_id": "123",
        }


async def fetch_candidate_async(state: AnalyzeState) -> AnalyzeState:
    """Récupère le profil candidat via MCP Resource"""
    print("\n[NŒUD 2] Récupération profil candidat via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidat_id = state.get("candidat_id", "123")
        candidat = await mcp_client.get_resource(f"candidat/{candidat_id}")
        
        print(f"    Candidat : {candidat.get('prenom', '')} {candidat.get('nom', '')}")
        print(f"    Email : {candidat.get('email', 'N/A')}")
        print(f"    Compétences : {len(candidat.get('competences', []))} compétences")
        print(f"    Expériences : {len(candidat.get('experiences', []))} expériences")
        
        return {
            **state,
            "candidat_data": candidat
        }
    
    finally:
        await mcp_client.close()


def fetch_candidate(state: AnalyzeState) -> AnalyzeState:
    return asyncio.run(fetch_candidate_async(state))


def detect_inconsistencies(state: AnalyzeState) -> AnalyzeState:
    """Détecte les incohérences via LLM + règles métier"""
    print("\n[NŒUD 3] Détection des incohérences...")
    
    candidat = state.get('candidat_data', {})
    
    prompt = f"""
    Analyse ce profil candidat et détecte TOUTES les incohérences possibles.
    
    CANDIDAT :
    - Nom : {candidat.get('prenom', '')} {candidat.get('nom', '')}
    - Email : {candidat.get('email', '')}
    - Téléphone : {candidat.get('telephone', '')}
    
    COMPÉTENCES :
    {json.dumps(candidat.get('competences', []), indent=2)}
    
    EXPÉRIENCES :
    {json.dumps(candidat.get('experiences', []), indent=2)}
    
    TYPES D'INCOHÉRENCES À VÉRIFIER :
    
    1. CHEVAUCHEMENTS DE DATES
       - Deux expériences avec des périodes qui se chevauchent
       - Exemple : Job A (2020-06 à 2023-12) + Job B (2022-01 à 2024-01)
    
    2. ÉCARTS INEXPLIQUÉS
       - Trous > 6 mois entre deux expériences
       - Exemple : Job A se termine en 2020-05, Job B commence en 2021-01
    
    3. COMPÉTENCES VS EXPÉRIENCE
       - Compétences listées mais jamais utilisées dans les expériences
       - Exemple : Compétence "React" mais aucune exp frontend
    
    4. COHÉRENCE TECHNOLOGIQUE
       - Technologies incompatibles ou contradictoires
       - Exemple : "Expert Python" mais que des jobs Java
    
    5. DESCRIPTION VAGUE
       - Descriptions d'expérience trop courtes ou génériques
       - Exemple : "Développement d'APIs" (< 30 caractères)
    
    Réponds en JSON avec cette structure EXACTE :
    {{
        "inconsistencies": [
            {{
                "type": "experience_gap|overlap|skill_mismatch|vague_description",
                "severity": "low|medium|high",
                "description": "Description claire du problème",
                "affected_items": ["item1", "item2"]
            }}
        ],
        "coherence_score": 75,
        "recommendations": [
            "Recommandation 1",
            "Recommandation 2"
        ]
    }}
    
    Si AUCUNE incohérence : inconsistencies = [], coherence_score = 100
    
    Réponds UNIQUEMENT avec le JSON, rien d'autre.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        inconsistencies = data.get('inconsistencies', [])
        coherence_score = data.get('coherence_score', 100)
        recommendations = data.get('recommendations', [])
        
        print(f"     Score de cohérence : {coherence_score}/100")
        print(f"     Incohérences détectées : {len(inconsistencies)}")
        
        if inconsistencies:
            for i, inc in enumerate(inconsistencies, 1):
                severity_icon = "🔴" if inc['severity'] == 'high' else "🟡" if inc['severity'] == 'medium' else "🟢"
                print(f"      {severity_icon} [{inc['type']}] {inc['description']}")
        
        return {
            **state,
            "inconsistencies": inconsistencies,
            "coherence_score": coherence_score,
            "recommendations": recommendations
        }
    
    except Exception as e:
        print(f"     Erreur parsing JSON : {e}")
        print(f"    Response brute : {response.content[:500]}")
        
        return {
            **state,
            "inconsistencies": [],
            "coherence_score": 0,
            "recommendations": ["Erreur lors de l'analyse"]
        }


def human_approval(state: AnalyzeState) -> AnalyzeState:
    """Validation humaine """
    
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] Rapport approuvé automatiquement")
        return {**state, "human_approved": True}
    
    print("\n" + "="*70)
    print("PREVIEW RAPPORT D'ANALYSE")
    print("="*70)
    
    candidat = state.get('candidat_data', {})
    print(f"Candidat : {candidat.get('prenom', '')} {candidat.get('nom', '')}")
    print(f"Email    : {candidat.get('email', '')}")
    
    coherence_score = state.get('coherence_score', 0)
    print(f"\n SCORE DE COHÉRENCE : {coherence_score}/100")
    
    if coherence_score >= 80:
        print("    Profil cohérent")
    elif coherence_score >= 60:
        print("     Quelques incohérences mineures")
    else:
        print("    Incohérences significatives détectées")
    
    inconsistencies = state.get('inconsistencies', [])
    
    if inconsistencies:
        print(f"\n🔍 INCOHÉRENCES DÉTECTÉES : {len(inconsistencies)}")
        print("┌────────────────────────────────────────┐")
        
        for i, inc in enumerate(inconsistencies, 1):
            severity_icon = "🔴" if inc['severity'] == 'high' else "🟡" if inc['severity'] == 'medium' else "🟢"
            print(f"│ {i}. {severity_icon} {inc['type']:<25} │")
            print(f"│    {inc['description']:<35} │")
        
        print("└────────────────────────────────────────┘")
    else:
        print("\n Aucune incohérence détectée")
    
    recommendations = state.get('recommendations', [])
    if recommendations:
        print(f"\n RECOMMANDATIONS : {len(recommendations)}")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print("="*70)
    
    choice = input("\n[e] Exécuter  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    else:
        print(" Annulé")
        return {**state, "human_approved": False}


async def generate_report_async(state: AnalyzeState) -> AnalyzeState:
    """Génère le rapport final via MCP Tool"""
    if not state.get("human_approved"):
        return {
            **state,
            "result": {"status": "cancelled"},
            "final_message": "Analyse annulée"
        }
    
    print("\n[NŒUD 5] Génération du rapport via MCP Tool...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="analyser_coherence",
            parameters={
                "candidat_id": state['candidat_id'],
                "inconsistencies": state.get('inconsistencies', []),
                "coherence_score": state.get('coherence_score', 0),
                "recommendations": state.get('recommendations', [])
            }
        )
        
        if result.get('status') != 'success':
            error_msg = result.get('error', 'Erreur inconnue')
            print(f"\n Erreur : {error_msg}")
            return {
                **state,
                "result": {"status": "error", "error": error_msg},
                "final_message": f"Erreur : {error_msg}"
            }
        
        print(f"\n Rapport généré avec succès")
        print(f"  Score de cohérence : {result.get('coherence_score')}/100")
        print(f"  Incohérences : {len(result.get('inconsistencies', []))}")
        
        return {
            **state,
            "result": result,
            "final_message": f"Analyse terminée - Score: {result.get('coherence_score')}/100"
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


def generate_report(state: AnalyzeState) -> AnalyzeState:
    return asyncio.run(generate_report_async(state))


def should_execute(state: AnalyzeState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"


def build_analyze_graph():
    g = StateGraph(AnalyzeState)
    
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch", fetch_candidate)
    g.add_node("detect", detect_inconsistencies)
    g.add_node("approve", human_approval)
    g.add_node("execute", generate_report)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch")
    g.add_edge("fetch", "detect")
    g.add_edge("detect", "approve")
    g.add_conditional_edges(
        "approve",
        should_execute,
        {"execute": "execute", "end": END}
    )
    g.add_edge("execute", END)
    
    return g.compile()


def run_analyze_agent(user_question: str, use_real: bool = True, auto_approve: bool = False):
    """
    Point d'entrée de l'agent de détection d'incohérences
    
    Args:
        user_question: Question/demande de l'utilisateur
        use_real: Utiliser les vraies APIs (legacy, pas utilisé ici)
        auto_approve: Auto-approuver (True pour API, False pour CLI)
    
    Returns:
        État final avec résultat
    """
    print("\n" + "="*70)
    print("ACTION 7 - DÉTECTION D'INCOHÉRENCES (VIA MCP - CONFORME CDC)")
    print("="*70)
    
    start = time.time()
    graph = build_analyze_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,
        "candidat_id": None,
        "candidat_data": None,
        "inconsistencies": None,
        "coherence_score": None,
        "recommendations": None,
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
    run_analyze_agent(
        "Analyser le profil de Chaima pour détecter des incohérences",
        use_real=True,
        auto_approve=False
    )
