"""
Données mock et fonctions d'envoi d'email
"""

import os
import resend
from typing import Dict, Any
from datetime import datetime

# ============================================================================
# CONFIGURATION RESEND
# ============================================================================

resend.api_key = "re_DjbtCPXF_BeaBuSCkHiJdqYfUpnU5gZwd"
RESEND_FROM_EMAIL = "onboarding@resend.dev"

# ============================================================================
# CANDIDAT MOCK
# ============================================================================

CANDIDATE_Chaima = {
    "id": "123",
    "nom": "Omri",
    "prenom": "Chaima",
    "email": "shaima.omri@esprit.tn",
    "telephone": "+216 28 073 537",
    "competences": ["Python", "Django", "PostgreSQL", "Docker", "REST APIs"],
    "experiences": [
        {
            "entreprise": "TechCorp",
            "poste": "Développeur Backend",
            "debut": "2020-06",
            "fin": "2023-12",
            "description": "Développement d'APIs REST avec Django et PostgreSQL.",
        },
        {
            "entreprise": "StartupXYZ",
            "poste": "Développeur Full Stack",
            "debut": "2018-03",
            "fin": "2020-05",
            "description": "Développement full stack (React + Django).",
        }
    ],
}

# ============================================================================
# OFFRE MOCK
# ============================================================================

OFFRE_BACKEND = {
    "id": "456",
    "titre": "Développeur Backend Senior",
    "entreprise": "NewGen",
    "competences_requises": ["Python", "Django", "PostgreSQL", "Docker"],
    "localisation": "Sfax, Tunisie",
}

# ============================================================================
# CANDIDATURE ÉTENDUE (AVEC ÉTAPES)
# ============================================================================

CANDIDATURE_123_456 = {
    "id": "cand_789",
    "candidat_id": "123",
    "offre_id": "456",
    "candidat_nom": "Chaima Omri",
    "offre_titre": "Développeur Backend Senior",
    "date_candidature": "2024-03-01",
    "etape_actuelle_id": "step_002",  # ✅ CORRIGÉ
    "etape_actuelle_nom": "En évaluation",  # ✅ CORRIGÉ
    "statut": "En cours d'évaluation",
    "consentement_email": True,
    "consentement_sms": True,
    "consentement_rgpd_date": "2024-03-01",
    "historique_etapes": [
        {
            "date": "2024-03-01T10:00:00Z",
            "de": None,
            "vers": "step_001",
            "raison": "Candidature initiale",
            "par": "Système"
        },
        {
            "date": "2024-03-05T14:30:00Z",
            "de": "step_001",
            "vers": "step_002",
            "raison": "CV intéressant",
            "par": "Sarah Martin"
        }
    ]
}

# ============================================================================
# UTILISATEURS
# ============================================================================

USERS = {
    "user_001": {"id": "user_001", "nom": "Sarah Martin", "role": "Recruteur Senior"},
    "user_002": {"id": "user_002", "nom": "Thomas Dubois", "role": "Recruteur Junior"},
    "user_003": {"id": "user_003", "nom": "Agent IA", "role": "Assistant IA"}
}

# ============================================================================
# ÉTAPES DU PIPELINE (ACTION 5)
# ============================================================================

ETAPES_PIPELINE = {
    "step_001": {
        "id": "step_001",
        "nom": "Candidature reçue",
        "ordre": 1,
        "description": "Candidature vient d'arriver",
        "actions_auto": []
    },
    "step_002": {
        "id": "step_002",
        "nom": "En évaluation",
        "ordre": 2,
        "description": "CV en cours d'évaluation",
        "actions_auto": []
    },
    "step_003": {
        "id": "step_003",
        "nom": "Entretien RH",
        "ordre": 3,
        "description": "Première phase d'entretien avec RH",
        "actions_auto": [
            "notifier_candidat",
            "creer_tache_planification"
        ]
    },
    "step_004": {
        "id": "step_004",
        "nom": "Entretien technique",
        "ordre": 4,
        "description": "Entretien technique approfondi",
        "actions_auto": [
            "notifier_candidat",
            "creer_tache_planification"
        ]
    },
    "step_005": {
        "id": "step_005",
        "nom": "Entretien final",
        "ordre": 5,
        "description": "Dernier entretien avec direction",
        "actions_auto": [
            "notifier_candidat",
            "creer_tache_planification"
        ]
    },
    "step_006": {
        "id": "step_006",
        "nom": "Offre envoyée",
        "ordre": 6,
        "description": "Offre d'emploi envoyée au candidat",
        "actions_auto": [
            "notifier_candidat"
        ]
    },
    "step_007": {
        "id": "step_007",
        "nom": "Acceptée",
        "ordre": 7,
        "description": "Candidature acceptée - ÉTAT FINAL",
        "actions_auto": [
            "notifier_candidat",
            "creer_tache_onboarding"
        ],
        "final": True
    },
    "step_008": {
        "id": "step_008",
        "nom": "Rejetée",
        "ordre": 8,
        "description": "Candidature rejetée - ÉTAT FINAL",
        "actions_auto": [
            "notifier_candidat"
        ],
        "final": True
    }
}

# ============================================================================
# FONCTION VALIDATION TRANSITION (ACTION 5)
# ============================================================================

def valider_transition(etape_source_id: str, etape_cible_id: str) -> dict:
    """
    Valide si une transition entre 2 étapes est autorisée
    
    Returns:
        {"valid": bool, "error": str|None}
    """
    
    if etape_source_id not in ETAPES_PIPELINE:
        return {"valid": False, "error": f"Étape source {etape_source_id} inconnue"}
    
    if etape_cible_id not in ETAPES_PIPELINE:
        return {"valid": False, "error": f"Étape cible {etape_cible_id} inconnue"}
    
    source = ETAPES_PIPELINE[etape_source_id]
    cible = ETAPES_PIPELINE[etape_cible_id]
    
    # Règle 1: Ne pas partir d'une étape finale
    if source.get("final"):
        return {"valid": False, "error": f"Impossible de modifier une candidature {source['nom']}"}
    
    # Règle 2: Autorise avancement (ordre croissant)
    if cible["ordre"] > source["ordre"]:
        return {"valid": True, "error": None}
    
    # Règle 3: Autorise rejet à tout moment
    if cible["id"] == "step_008":  # Rejetée
        return {"valid": True, "error": None}
    
    # Règle 4: Interdit retour arrière
    if cible["ordre"] < source["ordre"]:
        return {"valid": False, "error": "Retour arrière non autorisé"}
    
    return {"valid": True, "error": None}

# ============================================================================
# FONCTION TRACE ATS
# ============================================================================

def enregistrer_trace_ats(trace_data: dict):
    """
    Enregistre une trace dans l'ATS (simulation Phase 3)
    En Phase 5 : INSERT en base de données
    """
    print(f"📋 [ATS TRACE] {trace_data['type'].upper()}")
    print(f"   Candidat : {trace_data.get('candidat_id')}")
    print(f"   Date : {trace_data.get('date')}")
    print(f"   Type : {trace_data.get('type_detail')}")
    
    return {
        "trace_id": f"trace_{trace_data['type']}_{trace_data['candidat_id']}",
        "enregistree": True
    }

# ============================================================================
# FONCTIONS EMAIL
# ============================================================================

def mock_send_email(to: str, subject: str, content: str) -> Dict[str, Any]:
    """
    Mode MOCK: Affiche l'email dans la console sans l'envoyer
    
    Args:
        to: Email destinataire
        subject: Objet de l'email
        content: Corps de l'email (HTML ou texte)
    
    Returns:
        Dict avec status "mock_sent"
    """
    print("\n" + "="*70)
    print("📧 [MOCK] EMAIL SIMULÉ - Aucun email réel envoyé")
    print("="*70)
    print(f"À      : {to}")
    print(f"Sujet  : {subject}")
    print(f"Date   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*70)
    print(f"Contenu:\n{content}")
    print("="*70 + "\n")
    
    return {
        "status": "mock_sent",
        "timestamp": datetime.now().isoformat(),
        "to": to,
        "subject": subject
    }

def send_real_email_resend(to: str, subject: str, content: str) -> Dict[str, Any]:
    """
    Mode RÉEL: Envoie un vrai email via Resend
    
    Args:
        to: Email destinataire
        subject: Objet de l'email
        content: Corps de l'email (texte simple ou HTML)
    
    Returns:
        Dict avec status "sent" ou "error"
    """
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h2 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border-left: 1px solid #e0e0e0;
                    border-right: 1px solid #e0e0e0;
                }}
                .footer {{
                    background: #f5f5f5;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border: 1px solid #e0e0e0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>NextGen Technologies</h2>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>Cet email a été envoyé par NextGen Technologies</p>
                <p style="color: #999; font-size: 11px; margin-top: 10px;">
                    Agent IA de recrutement - Action 9
                </p>
            </div>
        </body>
        </html>
        """
        
        response = resend.Emails.send({
            "from": f"NextGen Technologies <{RESEND_FROM_EMAIL}>",
            "to": to,
            "subject": subject,
            "html": html_content
        })
        
        print("\n" + "="*70)
        print(" EMAIL RÉEL ENVOYÉ VIA RESEND")
        print("="*70)
        print(f"À      : {to}")
        print(f"Sujet  : {subject}")
        print(f"ID     : {response['id']}")
        print(f"Date   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")
        
        return {
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "to": to,
            "subject": subject,
            "email_id": response['id'],
            "provider": "resend"
        }
    
    except Exception as e:
        print("\n" + "="*70)
        print(" ERREUR LORS DE L'ENVOI EMAIL")
        print("="*70)
        print(f"Erreur : {str(e)}")
        print("="*70 + "\n")
        
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "to": to,
            "error": str(e)
        }

def send_email(to: str, subject: str, content: str, use_real: bool = False) -> Dict[str, Any]:
    """
    Fonction principale pour envoyer un email
    
    Args:
        to: Email destinataire
        subject: Objet de l'email
        content: Corps de l'email
        use_real: 
            - False (défaut) = Mode MOCK (simulation)
            - True = Mode RÉEL (envoi via Resend)
    
    Returns:
        Dict avec le résultat de l'envoi
    
    Exemples:
        >>> # Mode MOCK (simulation)
        >>> send_email("test@example.com", "Test", "Bonjour", use_real=False)
        
        >>> # Mode RÉEL (envoi via Resend)
        >>> send_email("test@example.com", "Test", "Bonjour", use_real=True)
    """
    if use_real:
        return send_real_email_resend(to, subject, content)
    else:
        return mock_send_email(to, subject, content)