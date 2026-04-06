"""
MCP Tool : Déplacement candidature
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import (
    CANDIDATURE_123_456,
    ETAPES_PIPELINE,
    valider_transition,
    enregistrer_trace_ats
)

async def deplacer_candidature_tool(
    candidature_id: str,
    etape_cible_id: str
) -> dict:
    """
    Déplace une candidature vers une nouvelle étape
    
    Args:
        candidature_id: ID de la candidature
        etape_cible_id: ID de l'étape cible
    
    Returns:
        dict: Résultat du déplacement
    """
    
    if candidature_id == "cand_789":
        candidature = CANDIDATURE_123_456
    else:
        return {
            "status": "error",
            "error": f"Candidature {candidature_id} non trouvée"
        }
    
    etape_source_id = candidature["etape_actuelle_id"]
    
    if etape_cible_id not in ETAPES_PIPELINE:
        return {
            "status": "error",
            "error": f"Étape cible {etape_cible_id} inconnue"
        }
    
    etape_source = ETAPES_PIPELINE[etape_source_id]
    etape_cible = ETAPES_PIPELINE[etape_cible_id]
    
    validation = valider_transition(etape_source_id, etape_cible_id)
    if not validation["valid"]:
        return {
            "status": "error",
            "error": validation["error"]
        }
    
    timestamp = datetime.now().isoformat()
    
    candidature["etape_actuelle_id"] = etape_cible_id
    candidature["etape_actuelle_nom"] = etape_cible["nom"]
    candidature["statut"] = etape_cible["nom"]
    
    candidature["historique_etapes"].append({
        "date": timestamp,
        "de": etape_source_id,
        "vers": etape_cible_id,
        "raison": "Déplacement manuel",
        "par": "Agent IA"
    })
    
    enregistrer_trace_ats({
        "type": "deplacement_candidature",
        "candidat_id": candidature["candidat_id"],
        "date": timestamp,
        "type_detail": f"{etape_source['nom']} → {etape_cible['nom']}"
    })
    
    actions_declenchees = []
    
    for action in etape_cible.get("actions_auto", []):
        if action == "notifier_candidat":
            print(f"  [ACTION AUTO] Email notification envoyé à candidat")
            actions_declenchees.append({
                "type": "email_notification",
                "status": "sent",
                "email_id": f"email_notif_{timestamp}"
            })
        
        elif action == "creer_tache_planification":
            
            print(f"  [ACTION AUTO] Tâche planification créée")
            actions_declenchees.append({
                "type": "task_creation",
                "status": "created",
                "task_id": f"task_plan_{timestamp}"
            })
        
        elif action == "creer_tache_onboarding":
            
            print(f"   [ACTION AUTO] Tâche onboarding créée")
            actions_declenchees.append({
                "type": "task_creation",
                "status": "created",
                "task_id": f"task_onboard_{timestamp}"
            })
    
    
    return {
        "status": "success",
        "candidature_id": candidature_id,
        "etape_precedente": {
            "id": etape_source_id,
            "nom": etape_source["nom"]
        },
        "etape_actuelle": {
            "id": etape_cible_id,
            "nom": etape_cible["nom"]
        },
        "actions_declenchees": actions_declenchees,
        "timestamp": timestamp
    }