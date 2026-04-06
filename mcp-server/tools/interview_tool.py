"""
MCP TOOL - ENVOI MAIL CONVOCATION ENTRETIEN
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    FROM_EMAIL = "NextGen Technologies <onboarding@resend.dev>"
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    TIMEOUT = 30


try:
    import resend
    resend.api_key = Config.RESEND_API_KEY
    RESEND_AVAILABLE = True
    logger.info("✓ Resend API disponible")
except ImportError:
    RESEND_AVAILABLE = False
    logger.error("✗ Resend non installé")


def validate_params(
    candidat_id: str,
    candidat_email: str,
    objet: str,
    corps_html: str,
    type_entretien: str,
    creneaux: List[Dict[str, str]],
    lien_visio: str
) -> Optional[str]:
    """
    Valide tous les paramètres
    
    Returns:
        Message d'erreur ou None si valide
    """
    if not candidat_id:
        return "candidat_id requis"
    
    if not candidat_email or '@' not in candidat_email:
        return f"Email invalide: {candidat_email}"
    
    if not objet or len(objet) < 10:
        return "Objet email trop court"
    
    if not corps_html or len(corps_html) < 50:
        return "Corps email trop court"
    
    if type_entretien not in ["technique", "rh", "final", "culture"]:
        return f"Type d'entretien invalide: {type_entretien}"
    
    if not creneaux or not isinstance(creneaux, list):
        return "Créneaux requis"
    
    if len(creneaux) < 2:
        return "Minimum 2 créneaux requis"
    
    for i, creneau in enumerate(creneaux):
        if not all(k in creneau for k in ["date", "heure", "duree"]):
            return f"Créneau {i+1} invalide: champs manquants"
    
    if not lien_visio or not lien_visio.startswith("http"):
        return f"Lien visio invalide: {lien_visio}"
    
    return None


async def envoyer_mail_entretien(
    candidat_id: str,
    candidat_email: str,
    objet: str,
    corps_html: str,
    type_entretien: str,
    creneaux: List[Dict[str, str]],
    lien_visio: str
) -> Dict[str, Any]:
    """
    Envoie un email de convocation via Resend
    Version optimale avec validation, retry et logging
    
    Args:
        candidat_id: ID du candidat
        candidat_email: Email destinataire
        objet: Objet de l'email
        corps_html: Corps HTML
        type_entretien: Type d'entretien
        creneaux: Liste des créneaux
        lien_visio: Lien visioconférence
    
    Returns:
        Résultat de l'envoi
    """
    
    logger.info("="*70)
    logger.info("MCP TOOL - ENVOI MAIL CONVOCATION")
    logger.info("="*70)
    
    # Validation des paramètres
    if error := validate_params(
        candidat_id, candidat_email, objet, corps_html,
        type_entretien, creneaux, lien_visio
    ):
        logger.error(f"Validation échouée: {error}")
        return {
            "success": False,
            "error": f"Validation: {error}"
        }
    
    logger.info(f"✓ Paramètres validés")
    logger.info(f"  Destinataire: {candidat_email}")
    logger.info(f"  Type: {type_entretien}")
    logger.info(f"  Créneaux: {len(creneaux)}")
    
    # Vérifier disponibilité Resend
    if not RESEND_AVAILABLE:
        logger.error("Resend non disponible")
        return {
            "success": False,
            "error": "Resend non installé"
        }
    
    # Retry logic
    for attempt in range(Config.MAX_RETRIES):
        try:
            logger.info(f"Tentative d'envoi {attempt + 1}/{Config.MAX_RETRIES}")
            
            # Préparer params Resend
            params = {
                "from": Config.FROM_EMAIL,
                "to": [candidat_email],
                "subject": objet,
                "html": corps_html
            }
            
            # Envoi
            start_time = time.time()
            email = resend.Emails.send(params)
            duration = time.time() - start_time
            
            # Succès
            logger.info(f"✓ Email envoyé en {duration:.2f}s")
            logger.info(f"  Message ID: {email['id']}")
            
            # Trace ATS
            trace = {
                "type": "convocation_entretien",
                "candidat_id": candidat_id,
                "mail_id": email['id'],
                "objet": objet,
                "type_entretien": type_entretien,
                "creneaux_count": len(creneaux),
                "lien_visio": lien_visio,
                "sent_at": datetime.now().isoformat(),
                "sent_by": "Agent IA",
                "duration_ms": int(duration * 1000)
            }
            
            logger.info(" Trace ATS enregistrée")
            logger.debug(json.dumps(trace, indent=2, ensure_ascii=False))
            
            return {
                "success": True,
                "mail_id": email['id'],
                "candidat_email": candidat_email,
                "type_entretien": type_entretien,
                "creneaux_count": len(creneaux),
                "sent_at": datetime.now().isoformat(),
                "real_send": True,
                "trace": trace,
                "duration_ms": int(duration * 1000)
            }
            
        except Exception as e:
            logger.error(f"Tentative {attempt + 1} échouée: {e}")
            
            if attempt < Config.MAX_RETRIES - 1:
                logger.info(f"Retry dans {Config.RETRY_DELAY}s...")
                time.sleep(Config.RETRY_DELAY)
            else:
                logger.error("Échec définitif après toutes les tentatives")
                return {
                    "success": False,
                    "error": str(e),
                    "attempts": Config.MAX_RETRIES
                }


# Test unitaire
if __name__ == "__main__":
    import asyncio
    
    print(" Test unitaire - envoi_mail_entretien\n")
    
    result = asyncio.run(
        envoyer_mail_entretien(
            candidat_id="123",
            candidat_email="shaima.omri@esprit.tn",
            objet="Convocation - Entretien technique Backend Developer",
            corps_html="""
<p>Bonjour Chaima,</p>
<p>Nous avons le plaisir de vous convier à un entretien technique.</p>
<ul>
<li>Mardi 25 mars à 14h00</li>
<li>Mercredi 26 mars à 15h00</li>
</ul>
<p>Lien: <a href="https://meet.google.com/test">meet.google.com/test</a></p>
<p>Cordialement,<br>NextGen Technologies</p>
""",
            type_entretien="technique",
            creneaux=[
                {"date": "2025-03-25", "heure": "14:00", "duree": "1h"},
                {"date": "2025-03-26", "heure": "15:00", "duree": "1h"}
            ],
            lien_visio="https://meet.google.com/test-123"
        )
    )
    
    print(f"\n Test terminé")
    print(f"Résultat: {json.dumps(result, indent=2, ensure_ascii=False)}")