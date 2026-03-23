"""
MCP Tool : envoyer_mail - CONFORME CDC
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import CANDIDATE_Chaima, enregistrer_trace_ats

async def envoyer_mail_tool(
    candidat_id: str,
    objet: str,
    contenu: str,
    type_mail: str  
) -> dict:
    """
    Envoie un email générique au candidat
    
    Args:
        candidat_id: ID du candidat
        objet: Objet de l'email
        contenu: Corps HTML
        type_mail: "suivi" | "relance" | "rejet" | "information"
    
    Returns:
        dict: Mail envoyé + trace ATS
    """
    
    # Récupère candidat
    if candidat_id == "123":
        candidat = CANDIDATE_Chaima
    else:
        return {"status": "error", "error": f"Candidat {candidat_id} non trouvé"}
    
    # Validation type_mail
    if type_mail not in ["suivi", "relance", "rejet", "information"]:
        return {
            "status": "error",
            "error": f"Type invalide : {type_mail}. Attendu : suivi/relance/rejet/information"
        }
    
    # ENVOI RÉEL via Resend
    try:
        from dotenv import load_dotenv
        
        env_path = os.path.join(parent_dir, '.env')
        load_dotenv(env_path)
        
        api_key = os.getenv("RESEND_API_KEY")
        
        if not api_key:
            return {
                "status": "error",
                "error": "RESEND_API_KEY manquante",
                "email": candidat["email"]
            }
        
        import resend
        resend.api_key = api_key
        
        params = {
            "from": "NextGen Technologies <onboarding@resend.dev>",
            "to": [candidat["email"]],
            "subject": objet,
            "html": contenu,
        }
        
        email = resend.Emails.send(params)
        
        #  TRACE ATS
        enregistrer_trace_ats({
            "type": "email",
            "candidat_id": candidat_id,
            "date": datetime.now().isoformat(),
            "type_detail": type_mail,
            "statut": "envoyé"
        })
        
        return {
            "status": "sent",
            "candidat_id": candidat_id,
            "email": candidat["email"],
            "objet": objet,
            "type_mail": type_mail,
            "email_id": email.get("id"),
            "provider": "resend",
            "trace_enregistree": True  
        }
    
    except Exception as e:
        return {"status": "error", "error": str(e), "email": candidat["email"]}