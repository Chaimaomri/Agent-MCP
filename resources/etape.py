"""
MCP Resource : Récupération étape pipeline
"""

import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import ETAPES_PIPELINE

async def get_etape_resource(etape_id: str) -> dict:
    """
    Récupère les détails d'une étape du pipeline
    
    Args:
        etape_id: ID de l'étape (ex: "step_003")
    
    Returns:
        dict: Détails de l'étape
    """
    if etape_id in ETAPES_PIPELINE:
        return ETAPES_PIPELINE[etape_id]
    else:
        raise ValueError(f"Étape {etape_id} non trouvée")