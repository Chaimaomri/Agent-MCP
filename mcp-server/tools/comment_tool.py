"""
MCP Tool : ajouter_commentaire - CONFORME CDC
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import CANDIDATE_Chaima, enregistrer_trace_ats

async def ajouter_commentaire_tool(
    candidat_id: str,
    contenu: str,
    categorie: str = None  
) -> dict:
    """
    Ajoute un commentaire sur la fiche candidat
    
    Args:
        candidat_id: ID du candidat
        contenu: Contenu du commentaire
        categorie: Catégorie optionnelle ("entretien" | "relance" | "decision" | "observation")
    
    Returns:
        dict: Commentaire enregistré
    """
    
    # Récupère candidat
    if candidat_id == "123":
        candidat = CANDIDATE_Chaima
    else:
        return {"status": "error", "error": f"Candidat {candidat_id} non trouvé"}
    
    # Génère ID et horodatage
    comment_id = f"comment_{candidat_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.now().isoformat()
    
    # Auteur (simulé)
    auteur = "Agent IA"
    
    # Enregistre trace ATS
    enregistrer_trace_ats({
        "type": "commentaire",
        "candidat_id": candidat_id,
        "date": timestamp,
        "type_detail": categorie or "observation",
        "auteur": auteur
    })
    
    return {
        "status": "success",
        "comment_id": comment_id,
        "candidat_id": candidat_id,
        "contenu": contenu,
        "categorie": categorie,
        "auteur": auteur,
        "timestamp": timestamp
    }