"""
Action 10 : Recherche profil web + Incohérences - 
"""

from typing import TypedDict, Literal, Optional, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
import json
import time
import asyncio
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from mcp_client import MCPClient


class SearchState(TypedDict):
    user_question: str
    use_real: bool
    auto_approve: bool
    candidat_id: Optional[str]
    search_types: Optional[list]
    candidat_data: Optional[dict]
    web_results: Optional[dict]
    cross_check_report: Optional[dict]
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


def analyze_intent(state: SearchState) -> SearchState:
    """Analyse l'intention et extrait candidat_id + search_types"""
    print("\n[NŒUD 1] Analyse de l'intention...")
    
    prompt = f"""
    Analyse cette demande : "{state['user_question']}"
    
    Extrais en JSON :
    - candidat_id ("123" pour Chaima)
    - search_types : liste parmi ["linkedin", "github", "portfolio", "articles"]
    
    Si la demande ne précise pas, utilise : ["linkedin", "github", "portfolio"]
    
    Réponds UNIQUEMENT avec JSON.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(content)
        
        candidat_id = data.get('candidat_id', '123')
        search_types = data.get('search_types', ['linkedin', 'github', 'portfolio'])
        
        print(f"    Candidat ID : {candidat_id}")
        print(f"    Types recherche : {', '.join(search_types)}")
        
        return {
            **state,
            "candidat_id": candidat_id,
            "search_types": search_types,
        }
    
    except Exception as e:
        print(f"     Erreur parsing JSON : {e}")
        return {
            **state,
            "candidat_id": "123",
            "search_types": ['linkedin', 'github', 'portfolio'],
        }


async def fetch_candidate_async(state: SearchState) -> SearchState:
    """Récupère le profil candidat complet via MCP Resource"""
    print("\n[NŒUD 2] Récupération profil candidat (CV ATS) via MCP...")
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        candidat_id = state.get("candidat_id", "123")
        candidat = await mcp_client.get_resource(f"candidat/{candidat_id}")
        
        print(f"    Candidat : {candidat.get('prenom', '')} {candidat.get('nom', '')}")
        print(f"    Email : {candidat.get('email', 'N/A')}")
        print(f"    Expériences : {len(candidat.get('experiences', []))}")
        print(f"    Compétences : {len(candidat.get('competences', []))}")
        
        return {
            **state,
            "candidat_data": candidat
        }
    
    finally:
        await mcp_client.close()


def fetch_candidate(state: SearchState) -> SearchState:
    return asyncio.run(fetch_candidate_async(state))


async def web_search_async(state: SearchState) -> SearchState:
    """Recherche web via MCP Tool (Tavily ou Mock)"""
    print("\n[NŒUD 3] Recherche profil web via MCP Tool...")
    
    candidat = state.get('candidat_data', {})
    candidat_nom = f"{candidat.get('prenom', '')} {candidat.get('nom', '')}"
    candidat_email = candidat.get('email', '')
    search_types = state.get('search_types', [])
    use_real = state.get('use_real', False)
    
    mcp_client = MCPClient("http://127.0.0.1:8002")
    try:
        result = await mcp_client.call_tool(
            tool_name="rechercher_profil_web",
            parameters={
                "candidat_id": state.get('candidat_id'),
                "candidat_nom": candidat_nom,
                "candidat_email": candidat_email,
                "search_types": search_types,
                "use_real": use_real
            }
        )
        
        if result.get('status') != 'success':
            error_msg = result.get('error', 'Erreur inconnue')
            print(f"\n Erreur : {error_msg}")
            return {
                **state,
                "web_results": {"status": "error", "error": error_msg}
            }
        
        sources_found = result.get('sources_found', 0)
        print(f"\n Recherche terminée : {sources_found}/{len(search_types)} sources trouvées")
        
        return {
            **state,
            "web_results": result
        }
    
    except Exception as e:
        print(f"\n Erreur MCP : {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "web_results": {"status": "error", "error": str(e)}
        }
    
    finally:
        await mcp_client.close()


def web_search(state: SearchState) -> SearchState:
    return asyncio.run(web_search_async(state))


def cross_check_analysis(state: SearchState) -> SearchState:
    """Analyse croisée CV (ATS) vs Données Web via LLM"""
    print("\n[NŒUD 4] Analyse croisée CV/Web via LLM...")
    
    candidat = state.get('candidat_data', {})
    web_results = state.get('web_results', {})
    enriched_data = web_results.get('enriched_data', {})
    
    # Prépare les données pour le LLM
    cv_data = {
        "nom": f"{candidat.get('prenom', '')} {candidat.get('nom', '')}",
        "email": candidat.get('email', ''),
        "competences": candidat.get('competences', []),
        "experiences": candidat.get('experiences', []),
        "formations": candidat.get('formations', [])
    }
    
    prompt = f"""
    Tu es un expert en recrutement. Analyse et compare les données du CV (ATS) avec les informations trouvées sur le web.
    
    DONNÉES CV (ATS) :
    {json.dumps(cv_data, indent=2, ensure_ascii=False)}
    
    DONNÉES WEB TROUVÉES :
    {json.dumps(enriched_data, indent=2, ensure_ascii=False)}
    
    TÂCHE : Détecte les incohérences et divergences entre le CV et le web.
    
    Analyse ces points :
    1. **Postes actuels** : Le poste mentionné sur LinkedIn correspond-il au CV ?
    2. **Entreprises** : Les entreprises mentionnées sont-elles cohérentes ?
    3. **Dates** : Les périodes d'expérience matchent-elles ?
    4. **Compétences** : Les compétences GitHub/LinkedIn correspondent-elles au CV ?
    5. **Formations** : Les diplômes sont-ils cohérents ?
    
    Pour chaque incohérence, indique :
    - Type (poste, entreprise, dates, competences, formation)
    - Sévérité (high, medium, low)
    - Source CV vs Source Web
    - Description détaillée
    
    Calcule aussi un **score de cohérence global** de 0 à 100 :
    - 90-100 : Excellent (aucune incohérence majeure)
    - 70-89  : Bon (quelques divergences mineures)
    - 50-69  : Moyen (incohérences à clarifier)
    - 0-49   : Faible (incohérences importantes)
    
    Réponds UNIQUEMENT avec un JSON structuré :
    {{
        "coherence_score": 85,
        "incohérences": [
            {{
                "type": "competences",
                "severity": "medium",
                "cv_value": "Docker mentionné",
                "web_value": "Docker pas dans top compétences GitHub",
                "description": "Le CV mentionne Docker mais GitHub ne montre pas d'activité Docker récente"
            }}
        ],
        "points_positifs": [
            "Poste actuel cohérent entre CV et LinkedIn",
            "Compétences Python validées par GitHub"
        ],
        "recommandations": [
            "Clarifier expérience Docker lors de l'entretien",
            "Valider les certifications mentionnées"
        ]
    }}
    
    Réponds UNIQUEMENT avec le JSON, aucun texte avant ou après.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content.strip().replace("```json", "").replace("```", "")
        report = json.loads(content)
        
        print(f"      Analyse terminée")
        print(f"      Score cohérence : {report.get('coherence_score', 0)}/100")
        print(f"      Incohérences    : {len(report.get('incohérences', []))}")
        print(f"      Points positifs : {len(report.get('points_positifs', []))}")
        
        return {
            **state,
            "cross_check_report": report
        }
    
    except Exception as e:
        print(f"    Erreur parsing JSON : {e}")
        print(f"    Response brute : {response.content[:500]}")
        
        # Rapport par défaut si erreur
        return {
            **state,
            "cross_check_report": {
                "coherence_score": 0,
                "incohérences": [],
                "points_positifs": [],
                "recommandations": ["Erreur analyse LLM"]
            }
        }


def human_approval(state: SearchState) -> SearchState:
    """Validation humaine (OBLIGATOIRE selon CDC)"""
    
    if state.get('auto_approve', False):
        print("\n[AUTO-APPROVE] Rapport approuvé automatiquement")
        return {**state, "human_approved": True}
    
    print("\n" + "="*70)
    print("PREVIEW RAPPORT CROISEMENT CV/WEB")
    print("="*70)
    
    candidat = state.get('candidat_data', {})
    web_results = state.get('web_results', {})
    report = state.get('cross_check_report', {})
    
    print(f"\nCandidat : {candidat.get('prenom', '')} {candidat.get('nom', '')}")
    print(f"Email    : {candidat.get('email', '')}")
    
    # Sources trouvées
    sources_found = web_results.get('sources_found', 0)
    search_types = state.get('search_types', [])
    
    print(f"\n SOURCES WEB")
    print(f"Sources trouvées : {sources_found}/{len(search_types)}")
    
    enriched_data = web_results.get('enriched_data', {})
    
    if 'linkedin' in enriched_data:
        print(f"    LinkedIn : ✓")
    if 'github' in enriched_data:
        print(f"    GitHub   : ✓")
    if 'portfolio' in enriched_data:
        print(f"    Portfolio: ✓")
    
    # Score de cohérence
    score = report.get('coherence_score', 0)
    print(f"\n SCORE DE COHÉRENCE : {score}/100")
    
    if score >= 90:
        print(f"   🟢 Excellent - Profil très cohérent")
    elif score >= 70:
        print(f"   🟡 Bon - Quelques divergences mineures")
    elif score >= 50:
        print(f"   🟠 Moyen - Incohérences à clarifier")
    else:
        print(f"   🔴 Faible - Incohérences importantes")
    
    # Incohérences
    incohérences = report.get('incohérences', [])
    if incohérences:
        print(f"\n INCOHÉRENCES DÉTECTÉES : {len(incohérences)}")
        print("─" * 70)
        
        for i, inc in enumerate(incohérences[:5], 1):
            severity = inc.get('severity', 'low')
            severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
            
            print(f"\n{i}. {severity_icon} [{inc.get('type', 'N/A').upper()}] - Sévérité: {severity}")
            print(f"   CV  : {inc.get('cv_value', 'N/A')}")
            print(f"   Web : {inc.get('web_value', 'N/A')}")
            print(f"   → {inc.get('description', 'N/A')}")
        
        if len(incohérences) > 5:
            print(f"\n   ... et {len(incohérences) - 5} autres incohérences")
    else:
        print(f"\n Aucune incohérence majeure détectée")
    
    # Points positifs
    points_positifs = report.get('points_positifs', [])
    if points_positifs:
        print(f"\n POINTS POSITIFS : {len(points_positifs)}")
        for point in points_positifs[:3]:
            print(f"   • {point}")
    
    # Recommandations
    recommandations = report.get('recommandations', [])
    if recommandations:
        print(f"\n RECOMMANDATIONS : {len(recommandations)}")
        for reco in recommandations[:3]:
            print(f"   → {reco}")
    
    print("="*70)
    
    choice = input("\n[e] Exécuter (Générer rapport)  [a] Annuler\nChoix : ").lower()
    
    if choice == 'e':
        print(" Approuvé")
        return {**state, "human_approved": True}
    else:
        print(" Annulé")
        return {**state, "human_approved": False}


def generate_report(state: SearchState) -> SearchState:
    """Génère le rapport final en JSON + PDF"""
    if not state.get("human_approved"):
        return {
            **state,
            "result": {"status": "cancelled"},
            "final_message": "Génération rapport annulée"
        }
    
    print("\n[NŒUD 6] Génération rapport final...")
    
    candidat = state.get('candidat_data', {})
    web_results = state.get('web_results', {})
    report = state.get('cross_check_report', {})
    
    final_report = {
        "candidat": {
            "id": state.get('candidat_id'),
            "nom": f"{candidat.get('prenom', '')} {candidat.get('nom', '')}",
            "email": candidat.get('email', '')
        },
        "sources_web": {
            "total_found": web_results.get('sources_found', 0),
            "sources": list(web_results.get('enriched_data', {}).keys())
        },
        "analyse": {
            "coherence_score": report.get('coherence_score', 0),
            "incohérences_count": len(report.get('incohérences', [])),
            "incohérences": report.get('incohérences', []),
            "points_positifs": report.get('points_positifs', []),
            "recommandations": report.get('recommandations', [])
        },
        "timestamp": web_results.get('timestamp', '')
    }
    

    score = report.get('coherence_score', 0)
    incoh_count = len(report.get('incohérences', []))
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output_pdfs")
    os.makedirs(output_dir, exist_ok=True)
    
    candidat_nom = f"{candidat.get('prenom', '')}_{candidat.get('nom', '')}".replace(" ", "_")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"RAPPORT_WEB_{candidat_nom}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Crée le document PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    style_bullet = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=4
    )
    
    # Construction du contenu
    story = []
    
    # === EN-TÊTE ===
    story.append(Paragraph("RAPPORT D'ANALYSE PROFIL WEB", style_title))
    story.append(Spacer(1, 0.5*cm))
    
    # Infos candidat
    info_data = [
        ['Candidat', f"{candidat.get('prenom', '')} {candidat.get('nom', '')}"],
        ['Email', candidat.get('email', 'N/A')],
        ['Date analyse', datetime.now().strftime('%d/%m/%Y à %H:%M')],
        ['Sources trouvées', f"{web_results.get('sources_found', 0)} / {len(state.get('search_types', []))}"]
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 1*cm))
    
    # === SOURCES WEB ===
    story.append(Paragraph("SOURCES WEB ANALYSÉES", style_heading))
    story.append(Spacer(1, 0.3*cm))
    
    sources_data = [['Source', 'Statut']]
    enriched_data = web_results.get('enriched_data', {})
    
    for source in ['linkedin', 'github', 'portfolio', 'articles']:
        if source in enriched_data:
            sources_data.append([source.capitalize(), '✓ Trouvé'])
        else:
            sources_data.append([source.capitalize(), '✗ Non trouvé'])
    
    sources_table = Table(sources_data, colWidths=[8*cm, 8*cm])
    sources_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(sources_table)
    story.append(Spacer(1, 1*cm))
    
    # === SCORE DE COHÉRENCE ===
    story.append(Paragraph("SCORE DE COHÉRENCE GLOBAL", style_heading))
    story.append(Spacer(1, 0.3*cm))
    
    # Couleur selon score
    if score >= 90:
        score_color = colors.HexColor('#27AE60')
        score_label = "Excellent - Profil très cohérent"
    elif score >= 70:
        score_color = colors.HexColor('#F39C12')
        score_label = "Bon - Quelques divergences mineures"
    elif score >= 50:
        score_color = colors.HexColor('#E67E22')
        score_label = "Moyen - Incohérences à clarifier"
    else:
        score_color = colors.HexColor('#E74C3C')
        score_label = "Faible - Incohérences importantes"
    
    score_data = [
        ['Score', f"{score} / 100"],
        ['Évaluation', score_label],
        ['Incohérences détectées', str(incoh_count)]
    ]
    
    score_table = Table(score_data, colWidths=[6*cm, 10*cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
        ('BACKGROUND', (1, 0), (1, 0), score_color),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(score_table)
    story.append(Spacer(1, 1*cm))
    
    # === INCOHÉRENCES ===
    incohérences = report.get('incohérences', [])
    
    if incohérences:
        story.append(Paragraph(f"INCOHÉRENCES DÉTECTÉES ({len(incohérences)})", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        for i, inc in enumerate(incohérences, 1):
            severity = inc.get('severity', 'low')
            
            # Couleur selon sévérité
            if severity == 'high':
                severity_color = colors.HexColor('#E74C3C')
                severity_label = '🔴 HAUTE'
            elif severity == 'medium':
                severity_color = colors.HexColor('#F39C12')
                severity_label = '🟡 MOYENNE'
            else:
                severity_color = colors.HexColor('#27AE60')
                severity_label = '🟢 BASSE'
            
            inc_data = [
                ['Type', inc.get('type', 'N/A').upper()],
                ['Sévérité', severity_label],
                ['CV (ATS)', inc.get('cv_value', 'N/A')],
                ['Web', inc.get('web_value', 'N/A')],
                ['Description', inc.get('description', 'N/A')]
            ]
            
            inc_table = Table(inc_data, colWidths=[3.5*cm, 12.5*cm])
            inc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
                ('BACKGROUND', (1, 1), (1, 1), severity_color),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.whitesmoke),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(Paragraph(f"<b>Incohérence #{i}</b>", style_normal))
            story.append(Spacer(1, 0.2*cm))
            story.append(inc_table)
            story.append(Spacer(1, 0.5*cm))
    else:
        story.append(Paragraph("AUCUNE INCOHÉRENCE DÉTECTÉE", style_heading))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(" Le profil web est parfaitement cohérent avec le CV.", style_normal))
        story.append(Spacer(1, 0.5*cm))
    
    story.append(PageBreak())
    
    # === POINTS POSITIFS ===
    points_positifs = report.get('points_positifs', [])
    
    if points_positifs:
        story.append(Paragraph("POINTS POSITIFS", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        for point in points_positifs:
            story.append(Paragraph(f"✓ {point}", style_bullet))
        
        story.append(Spacer(1, 0.8*cm))
    
    # === RECOMMANDATIONS ===
    recommandations = report.get('recommandations', [])
    
    if recommandations:
        story.append(Paragraph("RECOMMANDATIONS", style_heading))
        story.append(Spacer(1, 0.3*cm))
        
        for reco in recommandations:
            story.append(Paragraph(f"→ {reco}", style_bullet))
        
        story.append(Spacer(1, 0.8*cm))
    
    # Footer
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        f"<i>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Génère le PDF
    try:
        doc.build(story)
        print(f" Rapport généré")
        print(f"  Score : {score}/100")
        print(f"  Incohérences : {incoh_count}")
        print(f"   PDF : {filepath}")
        
        # Enregistre trace ATS
        from mocks import enregistrer_trace_ats
        enregistrer_trace_ats({
            "type": "rapport_web_genere",
            "candidat_id": state.get('candidat_id'),
            "date": datetime.now().isoformat(),
            "type_detail": f"Rapport web généré - Score: {score}/100, {incoh_count} incohérences"
        })
        
        return {
            **state,
            "result": {
                **final_report,
                "pdf_path": filepath,
                "pdf_filename": filename
            },
            "final_message": f"Rapport généré - Score: {score}/100, {incoh_count} incohérences - PDF: {filename}"
        }
    
    except Exception as e:
        print(f" Erreur génération PDF : {e}")
        import traceback
        traceback.print_exc()
        
        return {
            **state,
            "result": final_report,
            "final_message": f"Rapport généré (JSON) - Erreur PDF: {e}"
        }


def should_execute(state: SearchState) -> Literal["execute", "end"]:
    return "execute" if state.get("human_approved") else "end"


def build_search_graph():
    g = StateGraph(SearchState)
    
    g.add_node("analyze", analyze_intent)
    g.add_node("fetch_candidate", fetch_candidate)
    g.add_node("search", web_search)
    g.add_node("cross_check", cross_check_analysis)
    g.add_node("approve", human_approval)
    g.add_node("execute", generate_report)
    
    g.add_edge(START, "analyze")
    g.add_edge("analyze", "fetch_candidate")
    g.add_edge("fetch_candidate", "search")
    g.add_edge("search", "cross_check")
    g.add_edge("cross_check", "approve")
    g.add_conditional_edges(
        "approve",
        should_execute,
        {"execute": "execute", "end": END}
    )
    g.add_edge("execute", END)
    
    return g.compile()

def run_search_agent(user_question: str, use_real: bool = False, auto_approve: bool = False):
    """
    Point d'entrée de l'agent de recherche web + incohérences
    
    Args:
        user_question: Question/demande de l'utilisateur
        use_real: Utiliser API Tavily (True) ou mock (False)
        auto_approve: Auto-approuver (True pour API, False pour CLI)
    
    Returns:
        État final avec résultat
    """
    print("\n" + "="*70)
    print("ACTION 10 - RECHERCHE WEB + INCOHÉRENCES (VIA MCP - CDC 8.10)")
    print("="*70)
    
    start = time.time()
    graph = build_search_graph()
    
    final = graph.invoke({
        "user_question": user_question,
        "use_real": use_real,
        "auto_approve": auto_approve,
        "candidat_id": None,
        "search_types": None,
        "candidat_data": None,
        "web_results": None,
        "cross_check_report": None,
        "human_approved": False,
        "result": None,
        "final_message": None,
    })
    
    print(f"\n{'='*70}\nRÉSUMÉ\n{'='*70}")
    result = final.get('result')
    if result and result.get('status') != 'cancelled':
        analyse = result.get('analyse', {})
        print(f"Score cohérence : {analyse.get('coherence_score', 0)}/100")
        print(f"Incohérences    : {analyse.get('incohérences_count', 0)}")
        print(f"Sources web     : {result.get('sources_web', {}).get('total_found', 0)}")
    else:
        print(f"Statut : Annulé")
    print(f"Message : {final.get('final_message')}")
    print(f"Temps   : {time.time() - start:.2f}s\n{'='*70}\n")
    
    return final


if __name__ == "__main__":
    run_search_agent(
        "Rechercher le profil web de Chaima et croiser avec son CV",
        use_real=True,  
        auto_approve=False
    )