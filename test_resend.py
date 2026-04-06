from mock_data import send_email

if __name__ == "__main__":
    print("="*70)
    print("TEST ENVOI EMAIL - RESEND")
    print("="*70)
    
    # ========== CONFIGURATION ==========
    test_email = "ton.email@gmail.com" 
    
    # Contenu du test
    test_subject = " Test Agent IA - Resend"
    test_content = """
    <h2>Bonjour ! 👋</h2>
    
    <p>Ceci est un <strong>email de test</strong> envoyé par l'agent IA de recrutement.</p>
    
    <p>Fonctionnalités testées :</p>
    <ul>
        <li> Envoi via Resend</li>
        <li> Template HTML professionnel</li>
        <li> Configuration API Key</li>
    </ul>
    
    <p>Si tu reçois cet email, tout fonctionne parfaitement ! 🎉</p>
    
    <p>Cordialement,<br>
    L'équipe NextGen Technologies</p>
    """
    
    print("\nMode d'envoi :")
    print("1. MOCK (simulation uniquement)")
    print("2. RÉEL (envoi via Resend)")
    
    choice = input("\nChoix [1/2] : ").strip()
    
    use_real = (choice == "2")
    
    if use_real:
        print(f"\n  MODE RÉEL activé !")
        print(f"   Un vrai email sera envoyé à : {test_email}")
        print(f"   Via : Resend (onboarding@resend.dev)")
        
        confirm = input("\nConfirmer l'envoi ? [o/N] : ").lower().strip()
        
        if confirm != 'o':
            print("\n Test annulé.")
            exit()
    
    print("\n Envoi en cours...")
    
    result = send_email(
        to=test_email,
        subject=test_subject,
        content=test_content,
        use_real=use_real
    )
    
    print("\n" + "="*70)
    print("RÉSULTAT")
    print("="*70)
    
    if result["status"] in ["sent", "mock_sent"]:
        print(" Succès !")
        if use_real:
            print(f"\n📧 Vérifie ta boîte email : {test_email}")
            print(f"   (L'email arrive en 2-3 secondes)")
            print(f"\n   Email ID : {result.get('email_id', 'N/A')}")
    else:
        print(" Erreur !")
        print(f"   Détails : {result.get('error', 'Erreur inconnue')}")
    
    print("="*70)