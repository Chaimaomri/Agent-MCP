"""
Serveur MCP - Agent Recrutement NextGen
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

app = FastAPI(title="MCP Server - Agent Recrutement NextGen")

class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ResourceRequest(BaseModel):
    uri: str

class ResourceResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ============================================================================
# IMPORT TOOLS
# ============================================================================

try:
    from tools.email_tool import envoyer_mail_tool
    print(" email_tool importé")
except Exception as e:
    print(f" Erreur email_tool: {e}")
    envoyer_mail_tool = None

try:
    from tools.sms_tool import envoyer_sms_tool
    print(" sms_tool importé")
except Exception as e:
    print(f" Erreur sms_tool: {e}")
    envoyer_sms_tool = None

try:
    from tools.comment_tool import ajouter_commentaire_tool
    print(" comment_tool importé")
except Exception as e:
    print(f" Erreur comment_tool: {e}")
    ajouter_commentaire_tool = None

try:
    from tools.task_tool import creer_tache_tool
    print(" task_tool importé")
except Exception as e:
    print(f" Erreur task_tool: {e}")
    creer_tache_tool = None

try:
    from tools.evaluation_tool import ajouter_evaluation_tool
    print(" evaluation_tool importé")
except Exception as e:
    print(f" Erreur evaluation_tool: {e}")
    ajouter_evaluation_tool = None

try:
    from tools.interview_tool import envoyer_mail_entretien
    print(" interview_tool importé")
except Exception as e:
    print(f" Erreur interview_tool: {e}")
    envoyer_mail_entretien = None

try:
    from tools.move_tool import deplacer_candidature_tool
    print(" move_tool importé")
except Exception as e:
    print(f" Erreur move_tool: {e}")
    deplacer_candidature_tool = None

try:
    from tools.analyze_tool import analyser_coherence_tool
    print(" analyze_tool importé")
except Exception as e:
    print(f" Erreur analyze_tool: {e}")
    analyser_coherence_tool = None

try:
    from tools.pdf_tool import creer_kit_entretien_tool
    print(" pdf_tool importé")
except Exception as e:
    print(f" Erreur pdf_tool: {e}")
    creer_kit_entretien_tool = None

# ============================================================================
# IMPORT RESOURCES
# ============================================================================

try:
    from resources.candidat import get_candidat_resource
    print(" candidat resource importée")
except Exception as e:
    print(f" Erreur candidat: {e}")
    get_candidat_resource = None

try:
    from resources.candidature import get_candidature_resource
    print(" candidature resource importée")
except Exception as e:
    print(f" Erreur candidature: {e}")
    get_candidature_resource = None

try:
    from resources.offre import get_offre_resource
    print(" offre resource importée")
except Exception as e:
    print(f" Erreur offre: {e}")
    get_offre_resource = None

try:
    from resources.etape import get_etape_resource
    print(" etape resource importée")
except Exception as e:
    print(f" Erreur etape: {e}")
    get_etape_resource = None

try:
    from tools.search_tool import rechercher_profil_web_tool
    print("✓ search_tool importé")
except Exception as e:
    print(f"✗ Erreur search_tool: {e}")
    rechercher_profil_web_tool = None

# ============================================================================
# TOOLS REGISTRY
# ============================================================================

TOOLS_REGISTRY = {}

if envoyer_mail_tool:
    TOOLS_REGISTRY["envoyer_mail"] = {
        "function": envoyer_mail_tool,
        "description": "Envoie un email à un candidat"
    }

if envoyer_sms_tool:
    TOOLS_REGISTRY["envoyer_sms"] = {
        "function": envoyer_sms_tool,
        "description": "Envoie un SMS à un candidat"
    }

if ajouter_commentaire_tool:
    TOOLS_REGISTRY["ajouter_commentaire"] = {
        "function": ajouter_commentaire_tool,
        "description": "Ajoute un commentaire"
    }

if creer_tache_tool:
    TOOLS_REGISTRY["creer_tache"] = {
        "function": creer_tache_tool,
        "description": "Crée une tâche"
    }

if ajouter_evaluation_tool:
    TOOLS_REGISTRY["ajouter_evaluation"] = {
        "function": ajouter_evaluation_tool,
        "description": "Ajoute une évaluation"
    }

if envoyer_mail_entretien:
    TOOLS_REGISTRY["envoyer_mail_entretien"] = {
        "function": envoyer_mail_entretien,
        "description": "Envoie un email de convocation d'entretien"
    }

if deplacer_candidature_tool:
    TOOLS_REGISTRY["deplacer_candidature"] = {
        "function": deplacer_candidature_tool,
        "description": "Déplace une candidature vers une nouvelle étape"
    }

if analyser_coherence_tool:
    TOOLS_REGISTRY["analyser_coherence"] = {
        "function": analyser_coherence_tool,
        "description": "Analyse la cohérence d'un profil candidat"
    }

if creer_kit_entretien_tool:
    TOOLS_REGISTRY["creer_kit_entretien"] = {
        "function": creer_kit_entretien_tool,
        "description": "Génère un kit d'entretien PDF complet"
    }

if rechercher_profil_web_tool:
    TOOLS_REGISTRY["rechercher_profil_web"] = {
        "function": rechercher_profil_web_tool,
        "description": "Recherche profil web candidat et croise avec CV "
    }

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "MCP Server - Agent Recrutement NextGen",
        "version": "1.0.0",
        "tools": list(TOOLS_REGISTRY.keys())
    }

@app.get("/tools")
async def list_tools():
    tools_info = []
    for name, data in TOOLS_REGISTRY.items():
        tools_info.append({
            "name": name,
            "description": data["description"]
        })
    return {"tools": tools_info}

@app.post("/tools/call")
async def call_tool(request: ToolCall) -> ToolResponse:
    tool_name = request.tool_name
    parameters = request.parameters
    
    print(f"\n[MCP] Tool: {tool_name}")
    print(f"[MCP] Params: {parameters}")
    
    if tool_name not in TOOLS_REGISTRY:
        return ToolResponse(success=False, error=f"Tool {tool_name} non trouvé")
    
    try:
        tool_function = TOOLS_REGISTRY[tool_name]["function"]
        result = await tool_function(**parameters)
        
        print(f"[MCP] Résultat: {result}")
        
        return ToolResponse(success=True, result=result)
    
    except Exception as e:
        print(f"[MCP] Erreur: {e}")
        return ToolResponse(success=False, error=str(e))

@app.post("/resources/get")
async def get_resource(request: ResourceRequest) -> ResourceResponse:
    uri = request.uri
    
    print(f"\n[MCP] Resource: {uri}")
    
    try:
        parts = uri.split("/")
        
        if parts[0] == "candidat" and len(parts) == 2:
            if not get_candidat_resource:
                raise Exception("Resource candidat non disponible")
            candidat_id = parts[1]
            data = await get_candidat_resource(candidat_id)
    
        elif parts[0] == "candidature" and len(parts) == 2:
            if not get_candidature_resource:
                raise Exception("Resource candidature non disponible")
            candidature_id = parts[1]
            data = await get_candidature_resource(candidature_id)
        
        elif parts[0] == "offre" and len(parts) == 2:
            if not get_offre_resource:
                raise Exception("Resource offre non disponible")
            offre_id = parts[1]
            data = await get_offre_resource(offre_id)
        
        elif parts[0] == "etape" and len(parts) == 2:
            if not get_etape_resource:
                raise Exception("Resource etape non disponible")
            etape_id = parts[1]
            data = await get_etape_resource(etape_id)
        
        else:
            return ResourceResponse(success=False, error=f"URI non reconnue: {uri}")
        
        return ResourceResponse(success=True, data=data)
    
    except Exception as e:
        print(f"[MCP] Erreur: {e}")
        return ResourceResponse(success=False, error=str(e))


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" DÉMARRAGE SERVEUR MCP")
    print("="*70)
    print(f"Tools disponibles: {len(TOOLS_REGISTRY)}")
    for tool_name in TOOLS_REGISTRY.keys():
        print(f"   {tool_name}")
    print("="*70 + "\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        log_level="info"
    )