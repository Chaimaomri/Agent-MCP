import asyncio
from mcp_client import MCPClient

async def test_mcp():
    print("="*70)
    print("TEST SERVEUR MCP")
    print("="*70)
    
    # Créer client
    client = MCPClient("http://127.0.0.1:8002")
    
    try:
        # 1. Liste des tools
        print("\n1. Liste des tools disponibles :")
        tools = await client.list_tools()
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # 2. Test resource candidat
        print("\n2. Test resource candidat/123 :")
        candidat = await client.get_resource("candidat/123")
        print(f"   Candidat: {candidat['prenom']} {candidat['nom']}")
        print(f"   Email: {candidat['email']}")
        
        # 3. Test tool ajouter_commentaire
        print("\n3. Test tool ajouter_commentaire :")
        result = await client.call_tool(
            tool_name="ajouter_commentaire",
            parameters={
                "candidat_id": "123",
                "contenu": "Excellent profil technique",
                "categorie": "technique"
            }
        )
        print(f"   Status: {result['status']}")
        print(f"   Comment ID: {result['comment_id']}")
        
        # 4. Test tool envoyer_sms (mock)
        print("\n4. Test tool envoyer_sms (mock) :")
        result = await client.call_tool(
            tool_name="envoyer_sms",
            parameters={
                "candidat_id": "123",
                "message": "Test MCP - SMS via serveur MCP",
                "use_real": False
            }
        )
        print(f"   Status: {result['status']}")
        print(f"   Téléphone: {result['telephone']}")
        
        print("\n" + "="*70)
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("="*70)
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_mcp())