"""
MCP Tool : creer_tache - CONFORME CDC
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import CANDIDATURE_123_456, USERS, enregistrer_trace_ats

async def creer_tache_tool(
    candidature_id: str,
    type: str,  
    description: str,
    assignee_id: str,  
    echeance: str = None,  
    priorite: str = "moyenne"
) -> dict:
    """
    Crée une tâche dans l'ATS
    
    Args:
        candidature_id: ID de la candidature
        type: Type de tâche ("relance" | "verification_references" | "preparation_onboarding")
        description: Description
        assignee_id: ID utilisateur assigné
        echeance: Date échéance (YYYY-MM-DD)
        priorite: Priorité ("haute" | "moyenne" | "basse")
    
    Returns:
        dict: Tâche créée
    """
    
    # Récupère candidature
    if candidature_id == "cand_789":
        candidature = CANDIDATURE_123_456
    else:
        return {"status": "error", "error": f"Candidature {candidature_id} non trouvée"}
    
    # Récupère assigné
    assignee = USERS.get(assignee_id, {"nom": "Inconnu"})
    
    # Simule création tâche (MOCK Phase 3)
    task_id = f"task_{candidature_id}_{type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Enregistre trace ATS
    enregistrer_trace_ats({
        "type": "tache",
        "candidat_id": candidature['candidat_id'],
        "date": datetime.now().isoformat(),
        "type_detail": type,
        "assignee": assignee['nom']
    })
    
    return {
        "status": "success",
        "task_id": task_id,
        "candidature_id": candidature_id,
        "type": type,
        "description": description,
        "assignee_id": assignee_id,
        "assignee_nom": assignee['nom'],
        "echeance": echeance,
        "priorite": priorite
    }