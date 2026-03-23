import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mocks import OFFRE_BACKEND

async def get_offre_resource(offre_id: str) -> dict:
    if offre_id == "456":
        return OFFRE_BACKEND
    else:
        raise ValueError(f"Offre {offre_id} non trouvée")
