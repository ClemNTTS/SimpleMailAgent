import google.generativeai as genai
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'API Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialisation du modèle
model = genai.GenerativeModel('gemini-2.0-flash')

def analyser_mail(contenu):
    """Analyse un mail et retourne sa catégorie"""
    prompt = f"""Tu es un assistant spécialisé dans la classification d'emails.
    Tu dois catégoriser chaque email en une seule catégorie parmi :
    - 'important' : emails urgents, personnels, professionnels importants
    - 'automatique' : newsletters, publicités, notifications automatiques
    - 'neutre' : tous les autres emails
    
    Tu dois UNIQUEMENT répondre avec un seul mot en minuscules parmi ces trois options.
    Analyse le contenu, l'urgence, la personnalisation et la source de l'email.
    
    Email à analyser : {contenu}"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower()
    except Exception as e:
        print(f"Erreur lors de l'analyse du mail : {str(e)}")
        return "neutre"  # Catégorie par défaut en cas d'erreur


def generer_reponse(categorie):
    """Génère une réponse appropriée selon la catégorie"""
    reponses = {
        'important': "Ce mail nécessite une attention particulière. Nous vous répondrons dans les plus brefs délais.",
        'automatique': "Merci pour votre message. Nous avons bien reçu votre demande et nous la traiterons en priorité.",
        'neutre': "Nous avons reçu votre message. Notre équipe l'examinera et vous répondra si nécessaire."
    }
    return reponses.get(categorie, "Merci pour votre message.")
