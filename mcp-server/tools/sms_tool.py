"""
MCP Tool : envoyer_sms - CONFORME CDC
"""

import os
import sys
import requests
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import CANDIDATE_Chaima, CANDIDATURE_123_456, enregistrer_trace_ats

async def envoyer_sms_tool(
    candidat_id: str,
    message: str,
    type_communication: str  
) -> dict:
    """
    Envoie un SMS au candidat avec vérification RGPD
    
    Args:
        candidat_id: ID du candidat
        message: Texte SMS (max 160 caractères)
        type_communication: "rappel" | "confirmation" | "notification"
    
    Returns:
        dict: SMS envoyé + trace
    """
    
    # Récupère candidat
    if candidat_id == "123":
        candidat = CANDIDATE_Chaima
    else:
        return {
            "status": "error",
            "error": f"Candidat {candidat_id} non trouvé",
            "telephone": "inconnu"
        }
    
    # VÉRIFICATION CONSENTEMENT RGPD
    candidature = CANDIDATURE_123_456  # Contient consentement_sms
    
    if not candidature.get('consentement_sms'):
        return {
            "status": "error",
            "error": "Candidat n'a pas consenti à recevoir des SMS (RGPD)",
            "telephone": candidat["telephone"]
        }
    
    # Validation type_communication
    if type_communication not in ["rappel", "confirmation", "notification"]:
        return {
            "status": "error",
            "error": f"Type invalide : {type_communication}. Attendu : rappel/confirmation/notification",
            "telephone": candidat["telephone"]
        }
    
    # Limite 160 caractères
    if len(message) > 160:
        message = message[:157] + "..."
    
    # ENVOI RÉEL via Infobip
    try:
        from dotenv import load_dotenv
        
        env_path = os.path.join(parent_dir, '.env')
        load_dotenv(env_path)
        
        api_key = os.getenv("INFOBIP_API_KEY")
        base_url = os.getenv("INFOBIP_BASE_URL", "https://y4p6pg.api.infobip.com")
        from_name = os.getenv("INFOBIP_FROM_NAME", "NextGen")
        
        if not api_key:
            return {
                "status": "error",
                "error": "INFOBIP_API_KEY manquante",
                "telephone": candidat["telephone"]
            }
        
        # Appel API Infobip
        url = f"{base_url}/sms/2/text/advanced"
        headers = {
            "Authorization": f"App {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [{
                "destinations": [{"to": candidat['telephone']}],
                "from": from_name,
                "text": message
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        enregistrer_trace_ats({
            "type": "sms",
            "candidat_id": candidat_id,
            "date": datetime.now().isoformat(),
            "type_detail": type_communication,
            "statut": "envoyé"
        })
        
        return {
            "status": "sent",
            "candidat_id": candidat_id,
            "telephone": candidat["telephone"],
            "message": message,
            "type_communication": type_communication,
            "sms_id": data['messages'][0]['messageId'],
            "provider": "infobip",
            "trace_enregistree": True  
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "telephone": candidat["telephone"]
        }