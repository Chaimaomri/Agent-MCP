"""
MCP Tool : Recherche profil web + Croisement CV/Web 
"""

import sys
import os
from datetime import datetime

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from mocks import enregistrer_trace_ats, CANDIDATE_Chaima

async def rechercher_profil_web_tool(
    candidat_id: str,
    candidat_nom: str,
    candidat_email: str,
    search_types: list,
    use_real: bool = False
) -> dict:
    """
    Recherche le profil web d'un candidat et prépare données pour croisement CV/Web
    
    Args:
        candidat_id: ID du candidat dans l'ATS
        candidat_nom: Nom complet du candidat
        candidat_email: Email du candidat
        search_types: Types de recherche (linkedin, github, portfolio, articles)
        use_real: Utiliser API Tavily (True) ou mock (False)
    
    Returns:
        dict: Résultats de recherche enrichis pour analyse croisée
    """
    
    print(f"\n [RECHERCHE PROFIL WEB] Recherche pour : {candidat_nom}")
    print(f"   Types : {', '.join(search_types)}")
    print(f"   Mode : {'TAVILY API' if use_real else 'MOCK (simulation)'}")
    
    timestamp = datetime.now().isoformat()
    
    # ============================================================================
    # MODE MOCK : Données simulées réalistes
    # ============================================================================
    
    if not use_real:
        search_results = {}
        enriched_data = {}
        
        # LinkedIn
        if 'linkedin' in search_types:
            print(f"    LinkedIn...")
            
            search_results['linkedin'] = {
                "found": True,
                "url": f"https://linkedin.com/in/{candidat_nom.lower().replace(' ', '-')}",
                "confidence": 0.92
            }
            
            enriched_data['linkedin'] = {
                "poste_actuel": "Senior Backend Developer",
                "entreprise_actuelle": "TechCorp Solutions",
                "localisation": "Sfax, Tunisie",
                "date_debut_poste": "2022-03",
                "connexions": 487,
                "recommandations": 12,
                "competences_endorsees": [
                    {"nom": "Python", "endorsements": 45},
                    {"nom": "Django", "endorsements": 38},
                    {"nom": "PostgreSQL", "endorsements": 32},
                    {"nom": "Docker", "endorsements": 15},
                    {"nom": "REST APIs", "endorsements": 28}
                ],
                "certifications": [
                    {
                        "titre": "AWS Certified Solutions Architect",
                        "organisme": "Amazon Web Services",
                        "date": "2023-06"
                    },
                    {
                        "titre": "Python Professional Certificate",
                        "organisme": "Python Institute",
                        "date": "2022-11"
                    }
                ],
                "formations": [
                    {
                        "diplome": "Ingénieur en Informatique",
                        "ecole": "ESPRIT",
                        "annee_debut": "2014",
                        "annee_fin": "2018"
                    }
                ],
                "experiences_linkedin": [
                    {
                        "poste": "Senior Backend Developer",
                        "entreprise": "TechCorp Solutions",
                        "debut": "2022-03",
                        "fin": "present",
                        "description": "Lead backend development, microservices architecture"
                    },
                    {
                        "poste": "Backend Developer",
                        "entreprise": "WebSolutions Inc",
                        "debut": "2020-01",
                        "fin": "2022-02",
                        "description": "Django REST API development, database optimization"
                    }
                ]
            }
            
            print(f"       Profil trouvé : {enriched_data['linkedin']['poste_actuel']}")
        
        # GitHub
        if 'github' in search_types:
            print(f"    GitHub...")
            
            search_results['github'] = {
                "found": True,
                "url": f"https://github.com/{candidat_nom.lower().replace(' ', '')}",
                "confidence": 0.85
            }
            
            enriched_data['github'] = {
                "username": candidat_nom.lower().replace(' ', ''),
                "repos_count": 24,
                "repos_public": 18,
                "followers": 45,
                "following": 32,
                "contributions_last_year": 487,
                "account_created": "2018-09",
                "langages": ["Python", "JavaScript", "Go", "TypeScript", "Shell"],
                "langages_stats": {
                    "Python": 45,
                    "JavaScript": 28,
                    "Go": 15,
                    "TypeScript": 8,
                    "Shell": 4
                },
                "repos_populaires": [
                    {
                        "nom": "django-rest-api-boilerplate",
                        "description": "Production-ready Django REST API template with best practices",
                        "stars": 127,
                        "forks": 34,
                        "langage": "Python",
                        "derniere_maj": "2024-02-15",
                        "topics": ["django", "rest-api", "python", "backend"]
                    },
                    {
                        "nom": "microservices-patterns",
                        "description": "Microservices design patterns implementation in Go",
                        "stars": 89,
                        "forks": 21,
                        "langage": "Go",
                        "derniere_maj": "2024-01-20",
                        "topics": ["microservices", "golang", "patterns"]
                    },
                    {
                        "nom": "docker-compose-templates",
                        "description": "Production Docker Compose templates",
                        "stars": 56,
                        "forks": 18,
                        "langage": "Shell",
                        "derniere_maj": "2023-12-10",
                        "topics": ["docker", "devops", "containers"]
                    }
                ],
                "contributions": {
                    "commits": 1247,
                    "pull_requests": 87,
                    "issues": 45,
                    "code_reviews": 124
                }
            }
            
            print(f"       {enriched_data['github']['repos_count']} repos, {enriched_data['github']['contributions_last_year']} contributions")
        
        # Portfolio / Site personnel
        if 'portfolio' in search_types:
            print(f"    Portfolio...")
            
            search_results['portfolio'] = {
                "found": True,
                "url": f"https://{candidat_nom.lower().replace(' ', '')}.dev",
                "confidence": 0.78
            }
            
            enriched_data['portfolio'] = {
                "url": f"https://{candidat_nom.lower().replace(' ', '')}.dev",
                "titre": "Backend Engineer & Python Developer",
                "bio": "Passionate about building scalable backend systems. 5+ years experience with Python, Django, and microservices.",
                "projets": [
                    {
                        "nom": "E-commerce Platform Backend",
                        "description": "Microservices-based e-commerce backend handling 10K+ daily transactions",
                        "technologies": ["Django", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
                        "github_url": "https://github.com/example/ecommerce-backend"
                    },
                    {
                        "nom": "Real-time Analytics Dashboard",
                        "description": "Real-time data processing pipeline with Go and Apache Kafka",
                        "technologies": ["Go", "Kafka", "TimescaleDB", "Grafana"],
                        "github_url": "https://github.com/example/analytics-dashboard"
                    }
                ],
                "stack_technique": ["Python", "Django", "Go", "PostgreSQL", "Docker", "Kubernetes", "Redis", "Kafka"]
            }
            
            print(f"       Portfolio trouvé : {enriched_data['portfolio']['titre']}")
        
        # Articles / Publications
        if 'articles' in search_types:
            print(f"    Articles...")
            
            search_results['articles'] = {
                "found": True,
                "confidence": 0.70
            }
            
            enriched_data['articles'] = {
                "count": 3,
                "publications": [
                    {
                        "titre": "Optimizing Django ORM for High-Traffic Applications",
                        "plateforme": "Medium",
                        "date": "2024-01-15",
                        "url": "https://medium.com/@example/optimizing-django",
                        "vues": 1200,
                        "reactions": 89,
                        "sujets": ["Django", "Performance", "Databases"]
                    },
                    {
                        "titre": "Building Scalable APIs with FastAPI and Microservices",
                        "plateforme": "Dev.to",
                        "date": "2023-11-20",
                        "url": "https://dev.to/example/fastapi-guide",
                        "reactions": 127,
                        "sujets": ["FastAPI", "Microservices", "Python"]
                    },
                    {
                        "titre": "Docker Best Practices for Python Developers",
                        "plateforme": "Blog personnel",
                        "date": "2023-09-10",
                        "url": "https://blog.example.com/docker-python",
                        "sujets": ["Docker", "Python", "DevOps"]
                    }
                ]
            }
            
            print(f"       {enriched_data['articles']['count']} publications trouvées")
        
        # Compte le nombre de sources trouvées
        sources_found = sum(1 for data in search_results.values() if data.get('found'))
        
        print(f"\n    Recherche terminée : {sources_found}/{len(search_types)} sources trouvées")
        
        # Enregistre trace ATS
        enregistrer_trace_ats({
            "type": "recherche_profil_web",
            "candidat_id": candidat_id,
            "date": timestamp,
            "type_detail": f"{sources_found} sources trouvées : {', '.join(search_types)}"
        })
        
        return {
            "status": "success",
            "candidat_id": candidat_id,
            "candidat_nom": candidat_nom,
            "search_types": search_types,
            "sources_found": sources_found,
            "search_results": search_results,
            "enriched_data": enriched_data,
            "mode": "mock",
            "timestamp": timestamp
        }
    
    # ============================================================================
    # MODE RÉEL : API TAVILY
    # ============================================================================
    else:
        try:
            from tavily import TavilyClient
            
            # Récupère la clé API depuis .env
            tavily_api_key = os.getenv('TAVILY_API_KEY')
            if not tavily_api_key:
                return {
                    "status": "error",
                    "error": "TAVILY_API_KEY non configurée dans .env"
                }
            
            tavily_client = TavilyClient(api_key=tavily_api_key)
            
            search_results = {}
            enriched_data = {}
            
            # Recherche générale sur le candidat
            query = f"{candidat_nom} software engineer developer Tunisia"
            
            print(f"   Tavily API : {query}")
            
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=10,
                include_domains=["linkedin.com", "github.com"] if 'linkedin' in search_types or 'github' in search_types else None
            )
            
            # Parse les résultats Tavily
            for result in response.get('results', []):
                url = result.get('url', '').lower()
                content = result.get('content', '')
                title = result.get('title', '')
                
                # LinkedIn
                if 'linkedin.com/in' in url and 'linkedin' in search_types:
                    print(f"       LinkedIn trouvé")
                    search_results['linkedin'] = {
                        "found": True,
                        "url": result.get('url'),
                        "confidence": result.get('score', 0.8)
                    }
                    
                    enriched_data['linkedin'] = {
                        "titre": title,
                        "url": result.get('url'),
                        "extrait": content[:500],
                        "published_date": result.get('published_date', '')
                    }
                
                # GitHub
                elif 'github.com' in url and 'github' in search_types:
                    print(f"      GitHub trouvé")
                    search_results['github'] = {
                        "found": True,
                        "url": result.get('url'),
                        "confidence": result.get('score', 0.8)
                    }
                    
                    enriched_data['github'] = {
                        "titre": title,
                        "url": result.get('url'),
                        "extrait": content[:500]
                    }
                
                # Portfolio
                elif any(x in url for x in ['.dev', 'portfolio', 'blog']) and 'portfolio' in search_types:
                    print(f"      Portfolio/Blog trouvé")
                    if 'portfolio' not in enriched_data:
                        search_results['portfolio'] = {
                            "found": True,
                            "url": result.get('url'),
                            "confidence": result.get('score', 0.7)
                        }
                        enriched_data['portfolio'] = {
                            "titre": title,
                            "url": result.get('url'),
                            "extrait": content[:500]
                        }
                
                # Articles
                elif any(x in url for x in ['medium.com', 'dev.to', 'hashnode', 'substack']) and 'articles' in search_types:
                    print(f"      Article trouvé")
                    if 'articles' not in enriched_data:
                        enriched_data['articles'] = {"publications": []}
                    
                    enriched_data['articles']['publications'].append({
                        "titre": title,
                        "url": result.get('url'),
                        "extrait": content[:200],
                        "published_date": result.get('published_date', '')
                    })
            
            # Recherche spécifique GitHub si pas trouvé dans recherche générale
            if 'github' in search_types and 'github' not in search_results:
                github_query = f"{candidat_nom} github.com"
                print(f"    Tavily GitHub : {github_query}")
                
                github_response = tavily_client.search(
                    query=github_query,
                    search_depth="basic",
                    max_results=3,
                    include_domains=["github.com"]
                )
                
                for result in github_response.get('results', []):
                    if 'github.com' in result.get('url', '').lower():
                        print(f"      ✓ GitHub trouvé (recherche spécifique)")
                        search_results['github'] = {
                            "found": True,
                            "url": result.get('url'),
                            "confidence": result.get('score', 0.75)
                        }
                        enriched_data['github'] = {
                            "titre": result.get('title', ''),
                            "url": result.get('url'),
                            "extrait": result.get('content', '')[:500]
                        }
                        break
            
            sources_found = sum(1 for data in search_results.values() if data.get('found'))
            
            print(f"\n    Recherche Tavily terminée : {sources_found}/{len(search_types)} sources trouvées")
            
            # Enregistre trace ATS
            enregistrer_trace_ats({
                "type": "recherche_profil_web_tavily",
                "candidat_id": candidat_id,
                "date": timestamp,
                "type_detail": f"{sources_found} sources trouvées via Tavily API"
            })
            
            return {
                "status": "success",
                "candidat_id": candidat_id,
                "candidat_nom": candidat_nom,
                "search_types": search_types,
                "sources_found": sources_found,
                "search_results": search_results,
                "enriched_data": enriched_data,
                "mode": "tavily_api",
                "timestamp": timestamp
            }
        
        except ImportError:
            return {
                "status": "error",
                "error": "Package 'tavily-python' non installé. Commande: pip install tavily-python"
            }
        
        except Exception as e:
            print(f"    Erreur Tavily API : {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "error": f"Erreur Tavily API : {str(e)}"
            }