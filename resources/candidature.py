"""
MCP Resource : candidature/{id}
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mocks import CANDIDATURE_123_456, CANDIDATE_Chaima, OFFRE_BACKEND

async def get_candidature_resource(candidature_id: str) -> dict:
    """
    Récupère une candidature
    
    Args:
        candidature_id: ID candidature
    
    Returns:
        dict: Données candidature complètes
    """
    
    if candidature_id == "cand_789":
        return {
            **CANDIDATURE_123_456,
            "candidat_nom": f"{CANDIDATE_Chaima['prenom']} {CANDIDATE_Chaima['nom']}",
            "candidat_email": CANDIDATE_Chaima['email'],
            "offre_titre": OFFRE_BACKEND['titre']
        }
    else:
        raise ValueError(f"Candidature {candidature_id} non trouvée")