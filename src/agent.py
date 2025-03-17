import google.generativeai as genai
import os
from dotenv import load_dotenv
from src.mails import envoyer_email
import re
from src.db import est_expediteur_pub

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'API Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialisation du modèle
model = genai.GenerativeModel('gemini-2.0-flash')

def nettoyer_texte(texte):
    """Nettoie le texte pour l'analyse"""
    if not isinstance(texte, str):
        return ""
    
    # Suppression des caractères spéciaux et conversion en minuscules
    texte = re.sub(r'[^\w\s]', ' ', texte.lower())
    # Suppression des espaces multiples
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte

def analyser_mail(contenu, expediteur, user_id):
    """Analyse le contenu d'un email et retourne sa catégorie"""
    try:
        # Vérifier si l'expéditeur est marqué comme pub
        if est_expediteur_pub(user_id, expediteur):
            return "pub"
            
        # Nettoyage du texte
        text = nettoyer_texte(contenu)
        
        # Création du prompt pour Gemini
        prompt = f"""Analyse cet email et catégorise-le dans l'une des catégories suivantes :
        - "important" : pour les emails importants, urgents ou nécessitant une action
        - "pub" : pour les publicités, promotions, offres commerciales
        - "automatique" : pour les notifications automatiques, confirmations, rappels système

        Email de : {expediteur}
        Contenu : {text}

        Réponds uniquement avec le nom de la catégorie (important, pub, ou automatique)."""

        # Appel à Gemini
        response = model.generate_content(prompt)
        categorie = response.text.strip().lower()
        
        # Validation de la catégorie
        if categorie not in ["important", "pub", "automatique"]:
            print(f"Catégorie invalide reçue de Gemini : {categorie}")
            return "important"  # Par défaut, considérer comme important
            
        return categorie
            
    except Exception as e:
        print(f"Erreur lors de l'analyse du mail : {e}")
        return "important"  # En cas d'erreur, considérer comme important

def generer_reponse_automatique(contenu, expediteur):
    """Génère une réponse appropriée pour un mail automatique"""
    prompt = f"""Tu es un assistant qui doit répondre automatiquement à un email de façon humaine.
    Analyse le contenu et génère une réponse appropriée, professionnelle et concise.
    La réponse doit être en français et ne pas dépasser 3-4 phrases.
    
    Email reçu de {expediteur}:
    {contenu}
    
    Génère une réponse appropriée :"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erreur lors de la génération de la réponse automatique : {str(e)}")
        return "Merci pour votre message. Nous avons bien reçu votre demande."

def generer_reponse(categorie):
    """Génère une réponse appropriée selon la catégorie"""
    reponses = {
        'important': "Ce mail nécessite une attention particulière. Nous vous répondrons dans les plus brefs délais.",
        'pub': "Ce mail a été identifié comme une publicité ou une newsletter. Aucune réponse n'est nécessaire.",
        'automatique': "Ce mail a été traité automatiquement par notre système d'IA."
    }
    return reponses.get(categorie, "Merci pour votre message.")
