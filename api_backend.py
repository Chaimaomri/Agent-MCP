"""
BACKEND API REST - Agent Recrutement NextGen
"""

import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import uvicorn
import logging
import importlib
import traceback
from fastapi.responses import FileResponse
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# WRAPPERS AGENTS
# ============================================================================

def run_interview_agent(message: str):
    """Wrapper pour Agent2 - Convocation entretien"""
    try:
        module = importlib.import_module('agents.Agent2SendInterview')
        run_func = getattr(module, 'run_interview_agent', None)
        if not run_func:
            run_func = getattr(module, 'run_interview_workflow', None)
        if not run_func:
            raise ImportError("Ni 'run_interview_agent' ni 'run_interview_workflow' trouvé")
        
        logger.info("Appel Agent2 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent2: {e}\n{traceback.format_exc()}")
        raise

def run_task_agent(message: str):
    """Wrapper pour Agent3 - Création tâche"""
    try:
        module = importlib.import_module('agents.Agent3CreateTask')
        run_func = getattr(module, 'run_task_agent', None) or getattr(module, 'run', None)
        if not run_func:
            raise ImportError("Fonction introuvable dans Agent3CreateTask")
        
        logger.info("Appel Agent3 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent3: {e}\n{traceback.format_exc()}")
        raise

def run_comment_agent(message: str):
    """Wrapper pour Agent4 - Ajout commentaire"""
    try:
        module = importlib.import_module('agents.Agent4AddComment')
        run_func = getattr(module, 'run_comment_agent', None) or getattr(module, 'run', None)
        if not run_func:
            raise ImportError("Fonction introuvable dans Agent4AddComment")
        
        logger.info("Appel Agent4 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent4: {e}\n{traceback.format_exc()}")
        raise

def run_move_agent(message: str):
    """Wrapper pour Agent5 - Déplacement candidature"""
    try:
        module = importlib.import_module('agents.Agent5MoveCandidate')
        run_func = getattr(module, 'run_move_agent', None)
        if not run_func:
            raise ImportError("Fonction 'run_move_agent' introuvable dans Agent5MoveCandidate")
        
        logger.info("Appel Agent5 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent5: {e}\n{traceback.format_exc()}")
        raise

def run_evaluation_agent(message: str):
    """Wrapper pour Agent6 - Ajout évaluation"""
    try:
        module = importlib.import_module('agents.Agent6AddEvaluation')
        run_func = getattr(module, 'run_evaluation_agent', None) or getattr(module, 'run', None)
        if not run_func:
            raise ImportError("Fonction introuvable dans Agent6AddEvaluation")
        
        logger.info("Appel Agent6 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent6: {e}\n{traceback.format_exc()}")
        raise

def run_analyze_agent(message: str):
    """Wrapper pour Agent7 - Détection incohérences"""
    try:
        module = importlib.import_module('agents.Agent7DetectInconsistencies')
        run_func = getattr(module, 'run_analyze_agent', None)
        if not run_func:
            raise ImportError("Fonction 'run_analyze_agent' introuvable dans Agent7DetectInconsistencies")
        
        logger.info("Appel Agent7 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent7: {e}\n{traceback.format_exc()}")
        raise

def run_sms_agent(message: str):
    """Wrapper pour Agent8 - Envoi SMS"""
    try:
        module = importlib.import_module('agents.Agent8SendSMS')
        run_func = getattr(module, 'run_sms_agent', None)
        if not run_func:
            raise ImportError("Fonction 'run_sms_agent' introuvable dans Agent8SendSMS")
        
        logger.info("Appel Agent8 avec use_real=True, auto_approve=True")
        result = run_func(message, use_real=True, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent8: {e}\n{traceback.format_exc()}")
        raise

def run_email_agent(message: str):
    """Wrapper pour Agent9 - Envoi email"""
    try:
        module = importlib.import_module('agents.Agent9GenericEmail')
        run_func = getattr(module, 'run_email_agent', None) or getattr(module, 'run', None)
        if not run_func:
            raise ImportError("Fonction introuvable dans Agent9GenericEmail")
        
        logger.info("Appel Agent9 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent9: {e}\n{traceback.format_exc()}")
        raise

def run_pdf_agent(message: str):
    """Wrapper pour Agent1 - Génération Kit PDF"""
    try:
        module = importlib.import_module('agents.Agent1GeneratePDF')
        run_func = getattr(module, 'run_pdf_agent', None)
        if not run_func:
            raise ImportError("Fonction 'run_pdf_agent' introuvable dans Agent1GeneratePDF")
        
        logger.info("Appel Agent1 avec auto_approve=True")
        result = run_func(message, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent1: {e}\n{traceback.format_exc()}")
        raise

# ============================================================================
# WRAPPER ASYNCIO
# ============================================================================

async def run_agent(agent_function, message: str):
    """
    Exécute une fonction agent dans un thread séparé pour ne pas bloquer FastAPI.
    """
    loop = asyncio.get_running_loop()
    try:
        logger.info(f"Exécution agent dans thread séparé: {agent_function.__name__}")
        result = await loop.run_in_executor(None, agent_function, message)
        logger.info(f"Agent {agent_function.__name__} terminé avec succès")
        return result
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de {agent_function.__name__}: {e}")
        raise

def run_search_agent(message: str):
    """Wrapper pour Agent10 - Recherche web + incohérences"""
    try:
        module = importlib.import_module('agents.Agent10WebSearch')
        run_func = getattr(module, 'run_search_agent', None)
        if not run_func:
            raise ImportError("Fonction 'run_search_agent' introuvable dans Agent10WebSearch")
        
        logger.info("Appel Agent10 avec use_real=False (mode mock)")
        result = run_func(message, use_real=False, auto_approve=True)
        
        if asyncio.iscoroutine(result):
            return asyncio.run(result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur Agent10: {e}\n{traceback.format_exc()}")
        raise


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Agent Recrutement NextGen - API",
    description="API REST pour automatiser les actions RH via agents IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODÈLES PYDANTIC
# ============================================================================

class ConvocationRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Convoquer Chaima pour un entretien technique mardi après-midi"}
    )

class TacheRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Créer une tâche pour rappeler Chaima demain"}
    )

class CommentaireRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Ajouter le commentaire 'Excellent profil technique' pour Chaima"}
    )

class DeplacementRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Déplacer candidature de Chaima à l'étape Entretien RH"}
    )

class EvaluationRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Évaluer Chaima avec 4/5 en compétences techniques"}
    )

class DetectionRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Analyser le profil de Chaima pour détecter des incohérences"}
    )

class SMSRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Envoyer un SMS à Chaima pour lui rappeler l'entretien de demain"}
    )

class EmailRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Envoyer un email à Chaima pour la remercier de sa candidature"}
    )

class APIResponse(BaseModel):
    success: bool
    action: str
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[list] = None

class KitPDFRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Générer un kit d'entretien pour Chaima au poste Backend"}
    )

class RechercheRequest(BaseModel):
    message: str = Field(
        ..., 
        json_schema_extra={"example": "Rechercher le profil web de Chaima et croiser avec son CV"}
    )

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "service": "Agent Recrutement NextGen - API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "kit-pdf": "/api/kit-pdf",
            "convocation": "/api/convocation",
            "tache": "/api/tache",
            "commentaire": "/api/commentaire",
            "deplacement": "/api/deplacement",
            "evaluation": "/api/evaluation",
            "detection": "/api/detection",
            "sms": "/api/sms",
            "email": "/api/email", 
            "recherche": "/api/recherche"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2026-03-27"}

@app.post("/api/convocation", response_model=APIResponse, tags=["Actions RH"])
async def convoquer_entretien(request: ConvocationRequest):
    """Convoquer un candidat à un entretien (avec auto-approbation)"""
    logger.info(f"POST /api/convocation: {request.message}")
    try:
        result = await run_agent(run_interview_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="convocation_entretien",
                message="Email de convocation envoyé avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="convocation_entretien",
            message="Erreur lors de l'envoi de la convocation",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/convocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tache", response_model=APIResponse, tags=["Actions RH"])
async def creer_tache(request: TacheRequest):
    """Créer une tâche RH (avec auto-approbation)"""
    logger.info(f"POST /api/tache: {request.message}")
    try:
        result = await run_agent(run_task_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="creation_tache",
                message="Tâche créée avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="creation_tache",
            message="Erreur lors de la création de la tâche",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/tache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commentaire", response_model=APIResponse, tags=["Actions RH"])
async def ajouter_commentaire(request: CommentaireRequest):
    """Ajouter un commentaire sur une candidature (avec auto-approbation)"""
    logger.info(f"POST /api/commentaire: {request.message}")
    try:
        result = await run_agent(run_comment_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="ajout_commentaire",
                message="Commentaire ajouté avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="ajout_commentaire",
            message="Erreur lors de l'ajout du commentaire",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/commentaire: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deplacement", response_model=APIResponse, tags=["Actions RH"])
async def deplacer_candidature(request: DeplacementRequest):
    """Déplacer une candidature vers une nouvelle étape (avec auto-approbation)"""
    logger.info(f"POST /api/deplacement: {request.message}")
    try:
        result = await run_agent(run_move_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="deplacement_candidature",
                message="Candidature déplacée avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="deplacement_candidature",
            message="Erreur lors du déplacement",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/deplacement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluation", response_model=APIResponse, tags=["Actions RH"])
async def ajouter_evaluation(request: EvaluationRequest):
    """Ajouter une évaluation pour un candidat (avec auto-approbation)"""
    logger.info(f"POST /api/evaluation: {request.message}")
    try:
        result = await run_agent(run_evaluation_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="ajout_evaluation",
                message="Évaluation ajoutée avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="ajout_evaluation",
            message="Erreur lors de l'ajout de l'évaluation",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detection", response_model=APIResponse, tags=["Actions RH"])
async def detecter_incoherences(request: DetectionRequest):
    """Analyser un profil candidat pour détecter des incohérences (avec auto-approbation)"""
    logger.info(f"POST /api/detection: {request.message}")
    try:
        result = await run_agent(run_analyze_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="detection_incoherences",
                message="Analyse terminée avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="detection_incoherences",
            message="Erreur lors de l'analyse",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sms", response_model=APIResponse, tags=["Actions RH"])
async def envoyer_sms(request: SMSRequest):
    """Envoyer un SMS à un candidat (avec auto-approbation)"""
    logger.info(f"POST /api/sms: {request.message}")
    try:
        result = await run_agent(run_sms_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="envoi_sms",
                message="SMS envoyé avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="envoi_sms",
            message="Erreur lors de l'envoi du SMS",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/sms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email", response_model=APIResponse, tags=["Actions RH"])
async def envoyer_email(request: EmailRequest):
    """Envoyer un email générique à un candidat (avec auto-approbation)"""
    logger.info(f"POST /api/email: {request.message}")
    try:
        result = await run_agent(run_email_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="envoi_email",
                message="Email envoyé avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="envoi_email",
            message="Erreur lors de l'envoi de l'email",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/downloads/{filename}", tags=["Téléchargements"])
async def download_file(filename: str):
    """Télécharger un fichier PDF généré"""
    
    # Chemin vers le dossier output_pdfs
    output_dir = os.path.join(os.path.dirname(__file__), "output_pdfs")
    filepath = os.path.join(output_dir, filename)
    
    # Vérifie que le fichier existe
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    # Vérifie que c'est bien un PDF
    if not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont autorisés")
    
    # Retourne le fichier
    return FileResponse(
        path=filepath,
        media_type='application/pdf',
        filename=filename
    )

@app.post("/api/kit-pdf", response_model=APIResponse, tags=["Actions RH"])
async def generer_kit_pdf(request: KitPDFRequest):
    """Générer un kit d'entretien PDF complet (avec auto-approbation)"""
    logger.info(f"POST /api/kit-pdf: {request.message}")
    try:
        result = await run_agent(run_pdf_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="generation_kit_pdf",
                message="Kit d'entretien PDF généré avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="generation_kit_pdf",
            message="Erreur lors de la génération du PDF",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/kit-pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recherche", response_model=APIResponse, tags=["Actions RH"])
async def rechercher_profil_web(request: RechercheRequest):
    """Rechercher profil web + croisement CV/Web (avec auto-approbation)"""
    logger.info(f"POST /api/recherche: {request.message}")
    try:
        result = await run_agent(run_search_agent, request.message)
        
        if result and not result.get("errors"):
            return APIResponse(
                success=True,
                action="recherche_web_croisement",
                message="Recherche et analyse croisée terminées avec succès",
                data=result.get("result")
            )
        
        return APIResponse(
            success=False,
            action="recherche_web_croisement",
            message="Erreur lors de la recherche/analyse",
            errors=result.get("errors", []) if result else []
        )
        
    except Exception as e:
        logger.error(f"Erreur endpoint /api/recherche: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" BACKEND API REST - AGENT RECRUTEMENT NEXTGEN")
    print("="*70)
    print("\n Auto-approbation activée pour tous les agents")
    print("\nAPI disponible sur : http://localhost:8000")
    print("Documentation Swagger : http://localhost:8000/docs")
    print("Documentation ReDoc : http://localhost:8000/redoc")
    print("\nEndpoints disponibles :")
    print("  POST /api/convocation")
    print("  POST /api/tache")
    print("  POST /api/commentaire")
    print("  POST /api/deplacement")
    print("  POST /api/evaluation")
    print("  POST /api/detection")
    print("  POST /api/sms")
    print("  POST /api/email")
    print("  POST /api/recherche")
    
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")