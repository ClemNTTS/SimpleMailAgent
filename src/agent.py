import ollama

def analyser_mail(contenu):
    """Analyse le contenu du mail et le classe dans une catégorie"""
    response = ollama.chat(
        model="gemma:2b",
        messages=[
            {
                "role": "system",
                "content": """Tu es un analyseur de mails intelligent. Classifie les mails en trois catégories:
                - 'important': mails nécessitant une attention personnelle
                - 'automatique': mails non prioritaires pouvant être traités automatiquement
                - 'neutre': mails nécessitant une revue humaine
                Réponds uniquement avec une de ces trois catégories."""
            },
            {
                "role": "user",
                "content": f"Analyse ce mail et classe-le : {contenu}"
            }
        ],
        options={
            "temperature": 0.1,
            "stop": ["\n", ".", "!", "?"]
        }
    )
    return response["message"]["content"].strip().lower()


def generer_reponse(categorie):
    """Génère une réponse appropriée selon la catégorie"""
    reponses = {
        'important': "Ce mail nécessite une attention particulière. Nous vous répondrons dans les plus brefs délais.",
        'automatique': "Merci pour votre message. Nous avons bien reçu votre demande et nous la traiterons en priorité.",
        'neutre': "Nous avons reçu votre message. Notre équipe l'examinera et vous répondra si nécessaire."
    }
    return reponses.get(categorie, "Merci pour votre message.")
