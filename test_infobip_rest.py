"""
Test Infobip via REST API (sans SDK)
"""

import requests

# Configuration
API_KEY = "34e022415cda54e39f6ca3ab89bec491-c0f539b1-71e4-4185-b4d9-816e6fb0bdb5"
BASE_URL = "https://y4p6pg.api.infobip.com"

print("="*70)
print("TEST INFOBIP REST API - ENVOI SMS RÉEL")
print("="*70)

try:
    # Configuration
    url = f"{BASE_URL}/sms/2/text/advanced"
    headers = {
        "Authorization": f"App {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Payload
    payload = {
        "messages": [
            {
                "destinations": [{"to": "+216 28073537"}],
                "from": "NextGen ",
                "text": "Bonjour Chaima, Rappel : Entretien demain (15/03) à 14h NextGen Technologies.  À bientôt ! NextGen RH"
            }
        ]
    }
    
    print("\n Configuration OK")
    print(f"   URL: {url}")
    print(f"   API Key: {API_KEY[:20]}...")
    
    # Envoi
    print("\n Envoi SMS en cours...")
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    # Résultat
    data = response.json()
    
    if data.get('messages'):
        message = data['messages'][0]
        
        print("\n" + "="*70)
        print(" SMS ENVOYÉ AVEC SUCCÈS !")
        print("="*70)
        print(f"Message ID : {message.get('messageId')}")
        print(f"Status     : {message.get('status', {}).get('name')}")
        print(f"À          : +216 28073537")
        print(f"De         : NextGen")
        print("="*70)
        print("\n VÉRIFIE TON TÉLÉPHONE ! SMS arrivera en 2-5 secondes.")
    else:
        print(f"\n Réponse inattendue: {data}")

except requests.exceptions.HTTPError as e:
    print("\n" + "="*70)
    print(" ERREUR HTTP")
    print("="*70)
    print(f"Status Code : {e.response.status_code}")
    print(f"Réponse     : {e.response.text}")
    print("\nVérifie :")
    print("  - API Key correcte")
    print("  - Base URL correcte")
    print("="*70)

except Exception as e:
    print("\n" + "="*70)
    print(" ERREUR")
    print("="*70)
    print(f"Erreur : {str(e)}")
    print("="*70)