"""
MCP Tool : Analyse de cohérence profil candidat
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import (
    CANDIDATE_Chaima,
    enregistrer_trace_ats
)

async def analyser_coherence_tool(
    candidat_id: str,
    inconsistencies: list,
    coherence_score: int,
    recommendations: list
) -> dict:
    """
    Génère un rapport d'analyse de cohérence
    
    Args:
        candidat_id: ID du candidat
        inconsistencies: Liste des incohérences détectées
        coherence_score: Score de cohérence (0-100)
        recommendations: Liste des recommandations
    
    Returns:
        dict: Rapport d'analyse complet
    """
    
    # 1. Récupère candidat
    if candidat_id == "123":
        candidat = CANDIDATE_Chaima
    else:
        return {
            "status": "error",
            "error": f"Candidat {candidat_id} non trouvé"
        }
    
    timestamp = datetime.now().isoformat()
    
    # 2. Catégorise les incohérences par sévérité
    high_severity = [inc for inc in inconsistencies if inc.get('severity') == 'high']
    medium_severity = [inc for inc in inconsistencies if inc.get('severity') == 'medium']
    low_severity = [inc for inc in inconsistencies if inc.get('severity') == 'low']
    
    # 3. Détermine le statut global
    if coherence_score >= 80:
        status_global = "coherent"
        status_label = "Profil cohérent"
    elif coherence_score >= 60:
        status_global = "minor_issues"
        status_label = "Quelques incohérences mineures"
    else:
        status_global = "major_issues"
        status_label = "Incohérences significatives"
    
    # 4. Enregistre trace ATS
    enregistrer_trace_ats({
        "type": "analyse_coherence",
        "candidat_id": candidat_id,
        "date": timestamp,
        "type_detail": f"Score: {coherence_score}/100 - {len(inconsistencies)} incohérence(s)"
    })
    
    # 5. Affiche résumé
    print(f"\n [ANALYSE TERMINÉE]")
    print(f"   Candidat : {candidat.get('prenom')} {candidat.get('nom')}")
    print(f"   Score : {coherence_score}/100")
    print(f"   Statut : {status_label}")
    
    if inconsistencies:
        print(f"\n   Incohérences :")
        if high_severity:
            print(f"      🔴 Haute : {len(high_severity)}")
        if medium_severity:
            print(f"      🟡 Moyenne : {len(medium_severity)}")
        if low_severity:
            print(f"      🟢 Basse : {len(low_severity)}")
    else:
        print(f"   Aucune incohérence détectée")
    
    # 6. Génère actions recommandées
    actions_recommandees = []
    
    if high_severity:
        actions_recommandees.append({
            "action": "entretien_approfondi",
            "description": "Entretien approfondi requis pour clarifier les incohérences majeures",
            "priorite": "haute"
        })
    
    if coherence_score < 60:
        actions_recommandees.append({
            "action": "verification_documents",
            "description": "Vérification des documents justificatifs nécessaire",
            "priorite": "haute"
        })
    
    if medium_severity or low_severity:
        actions_recommandees.append({
            "action": "clarification_entretien",
            "description": "Points à clarifier lors du prochain entretien",
            "priorite": "moyenne"
        })
    
    # 7. Retourne rapport complet
    return {
        "status": "success",
        "candidat_id": candidat_id,
        "candidat_nom": f"{candidat.get('prenom')} {candidat.get('nom')}",
        "coherence_score": coherence_score,
        "status_global": status_global,
        "status_label": status_label,
        "inconsistencies": inconsistencies,
        "inconsistencies_count": {
            "total": len(inconsistencies),
            "high": len(high_severity),
            "medium": len(medium_severity),
            "low": len(low_severity)
        },
        "recommendations": recommendations,
        "actions_recommandees": actions_recommandees,
        "timestamp": timestamp,
        "rapport_id": f"rapport_{candidat_id}_{timestamp.replace(':', '-')}"
    }
