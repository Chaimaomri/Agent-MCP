def display_menu():
    """Affiche le menu principal"""
    print("\n" + "="*70)
    print("AGENT MCP RECRUTEMENT - NEXTGEN TECHNOLOGIES")
    print("="*70)
    print("\nActions disponibles :")
    print("  [3] Créer une tâche")
    print("  [4] Ajouter un commentaire")
    print("  [6] Ajouter une évaluation")
    print("  [8] Envoyer un SMS")
    print("  [9] Envoyer un email générique")
    print("  [0] Quitter")
    print("="*70)
    
def action_9_email():
    """Action 9 : Envoi email"""
    from agents.Agent9GenericEmail import run_email_agent
    
    print("\n### ACTION 9 : ENVOI EMAIL GÉNÉRIQUE ###\n")
    
    # Mode d'envoi
    print("Mode d'envoi :")
    print("1. MOCK (simulation)")
    print("2. RÉEL (Resend)")
    mode = input("Choix [1/2] : ").strip()
    use_real = (mode == "2")
    
    if use_real:
        print("\n  MODE RÉEL - Un vrai email sera envoyé !")
        print("   Via : Resend (onboarding@resend.dev)")
        confirm = input("   Confirmer ? [o/N] : ").lower()
        if confirm != 'o':
            print(" Annulé.\n")
            return
    
    # Question
    default_question = """
    Envoie un email à Chaima pour lui demander ses références 
    professionnelles et sa disponibilité pour un entretien 
    la semaine prochaine.
    """
    
    use_default = input("\nUtiliser le scénario par défaut ? [O/n] : ").lower().strip()
    
    if use_default in ['', 'o', 'oui']:
        question = default_question.strip()
    else:
        question = input("Entrez votre demande : ").strip()
    
    # Exécution
    run_email_agent(question, use_real=use_real)


def action_4_comment():
    """Action 4 : Ajout commentaire"""
    from agents.Agent4AddComment import run_comment_agent
    
    print("\n### ACTION 4 : AJOUT COMMENTAIRE ###\n")
    
    # Question
    default_question = "Ajoute un commentaire sur Chaima : Excellent profil technique, à recontacter rapidement"
    
    use_default = input("Utiliser le scénario par défaut ? [O/n] : ").lower().strip()
    
    if use_default in ['', 'o', 'oui']:
        question = default_question
    else:
        question = input("Entrez votre demande : ").strip()
    
    # Exécution
    run_comment_agent(question, use_real=False)


def action_3_task():
    """Action 3 : Création tâche"""
    from agents.Agent3CreateTask import run_task_agent
    
    print("\n### ACTION 3 : CRÉATION TÂCHE ###\n")
    
    default_question = "Crée une tâche pour rappeler Chaima la semaine prochaine pour discuter des références"
    
    use_default = input("Utiliser le scénario par défaut ? [O/n] : ").lower().strip()
    
    if use_default in ['', 'o', 'oui']:
        question = default_question
    else:
        question = input("Entrez votre demande : ").strip()
    
    run_task_agent(question, use_real=False)


def action_6_evaluation():
    """Action 6 : Ajout évaluation"""
    from agents.Agent6AddEvaluation import run_evaluation_agent
    
    print("\n### ACTION 6 : AJOUT ÉVALUATION ###\n")
    
    default_question = "Ajoute une évaluation pour Chaima : 4/5 en technique, 5/5 en communication, recommandation positive"
    
    use_default = input("Utiliser le scénario par défaut ? [O/n] : ").lower().strip()
    
    if use_default in ['', 'o', 'oui']:
        question = default_question
    else:
        question = input("Entrez votre demande : ").strip()
    
    run_evaluation_agent(question, use_real=False)


def action_8_sms():
    """Action 8 : Envoi SMS"""
    from agents.Agent8SendSMS import run_sms_agent
    
    print("\n### ACTION 8 : ENVOI SMS ###\n")
    
    print("Mode d'envoi :")
    print("1. MOCK (simulation)")
    print("2. RÉEL ")
    mode = input("Choix [1/2] : ").strip()
    use_real = (mode == "2")
    
    if use_real:
        print("\n  MODE RÉEL - Un vrai SMS sera envoyé !")
        confirm = input("   Confirmer ? [o/N] : ").lower()
        if confirm != 'o':
            print(" Annulé.\n")
            return
    
    default_question = "Envoie un SMS à Chaima pour confirmer le RDV de demain à 14h"
    
    use_default = input("\nUtiliser le scénario par défaut ? [O/n] : ").lower().strip()
    
    if use_default in ['', 'o', 'oui']:
        question = default_question
    else:
        question = input("Entrez votre demande : ").strip()
    
    run_sms_agent(question, use_real=use_real)


def main():
    
    while True:
        display_menu()
        
        choice = input("\nChoisir une action : ").strip()
        
        if choice == "9":
            action_9_email()
        
        elif choice == "4":
            action_4_comment()
        
        elif choice == "3":
            action_3_task()
        
        elif choice == "6":
            action_6_evaluation()
        
        elif choice == "8":
            action_8_sms()
        
        elif choice == "0":
            print("\n Au revoir !\n")
            break
        
        else:
            print("\n Action non reconnue. Choisissez une action valide.\n")
        
        continue_choice = input("\nContinuer ? [O/n] : ").lower().strip()
        if continue_choice in ['n', 'non']:
            print("\n Au revoir !\n")
            break


if __name__ == "__main__":
    main()
