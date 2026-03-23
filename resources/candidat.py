import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mocks import CANDIDATE_Chaima

async def get_candidat_resource(candidat_id: str) -> dict:
    if candidat_id == "123":
        return CANDIDATE_Chaima
    else:
        raise ValueError(f"Candidat {candidat_id} non trouvé")