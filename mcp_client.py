import httpx
from typing import Dict, Any

class MCPClient:
    """
    Client pour communiquer avec le serveur MCP
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8002"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Appelle un tool MCP
        
        Args:
            tool_name: Nom du tool
            parameters: Paramètres du tool
        
        Returns:
            dict: Résultat du tool
        
        Raises:
            Exception: Si erreur MCP
        """
        url = f"{self.base_url}/tools/call"
        
        payload = {
            "tool_name": tool_name,
            "parameters": parameters
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise Exception(f"MCP Tool Error: {data.get('error')}")
            
            return data.get("result", {})
        
        except httpx.HTTPError as e:
            raise Exception(f"MCP Communication Error: {str(e)}")
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """
        Récupère une resource MCP
        
        Args:
            uri: URI de la resource (ex: "candidat/123")
        
        Returns:
            dict: Données de la resource
        
        Raises:
            Exception: Si erreur MCP
        """
        url = f"{self.base_url}/resources/get"
        
        payload = {
            "uri": uri
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise Exception(f"MCP Resource Error: {data.get('error')}")
            
            return data.get("data", {})
        
        except httpx.HTTPError as e:
            raise Exception(f"MCP Communication Error: {str(e)}")
    
    async def list_tools(self) -> list:
        """
        Liste tous les tools MCP disponibles
        
        Returns:
            list: Liste des tools avec descriptions
        """
        url = f"{self.base_url}/tools"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get("tools", [])
        
        except httpx.HTTPError as e:
            raise Exception(f"MCP Communication Error: {str(e)}")
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.client.aclose()