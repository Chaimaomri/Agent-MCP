"""
MCP Tool : ajouter_evaluation - CONFORME CDC
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import CANDIDATURE_123_456, enregistrer_trace_ats

async def ajouter_evaluation_tool(
    candidature_id: str,
    scores: dict,  
    commentaire: str,
    recommandation: str  
) -> dict:
    """
    Enregistre une évaluation suite à un entretien
    
    Args:
        candidature_id: ID de la candidature
        scores: Scores par compétence (dict flexible, ex: {"technique": 4.5, "communication": 4.0})
        commentaire: Appréciation qualitative
        recommandation: "poursuivre" | "attente" | "rejet"
    
    Returns:
        dict: Évaluation enregistrée
    """
    
    # Récupère candidature
    if candidature_id == "cand_789":
        candidature = CANDIDATURE_123_456
    else:
        return {"status": "error", "error": f"Candidature {candidature_id} non trouvée"}
    
    # Validation recommandation
    if recommandation not in ["poursuivre", "attente", "rejet"]:
        return {
            "status": "error",
            "error": f"Recommandation invalide : {recommandation}. Attendu : poursuivre/attente/rejet"
        }
    
    # Calcul score global
    if scores:
        score_global = sum(scores.values()) / len(scores)
    else:
        score_global = 0.0
    
    # Génère ID
    evaluation_id = f"eval_{candidature_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.now().isoformat()
    
    # Enregistre trace ATS
    enregistrer_trace_ats({
        "type": "evaluation",
        "candidat_id": candidature['candidat_id'],
        "date": timestamp,
        "type_detail": recommandation,
        "score_global": round(score_global, 2)
    })
    
    return {
        "status": "success",
        "evaluation_id": evaluation_id,
        "candidature_id": candidature_id,
        "scores": scores,
        "score_global": round(score_global, 2),
        "commentaire": commentaire,
        "recommandation": recommandation,
        "timestamp": timestamp
    }