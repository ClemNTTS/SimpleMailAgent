# Agent IA d'Analyse de Sentiment

Un agent IA simple qui analyse le sentiment des messages et envoie des réponses automatiques par email.

## Description

Cet agent utilise le modèle Gemma 2B d'Ollama pour analyser le sentiment des messages et envoyer des réponses automatiques par email. Il est capable de :

- Analyser le sentiment d'un message (positif ou négatif)
- Générer une réponse appropriée
- Envoyer un email automatiquement

## Prérequis

- Python 3.x
- Ollama installé localement avec le modèle Gemma 2B
- Un compte email configuré pour l'envoi de messages

## Installation

1. Clonez le repository :

```bash
git clone [URL_DU_REPO]
cd [NOM_DU_DOSSIER]
```

2. Créez un environnement virtuel et activez-le :

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. Installez les dépendances :

```bash
pip install -r requirements.txt
```

4. Configurez les variables d'environnement :
   Créez un fichier `.env` à la racine du projet avec les informations suivantes :

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe_d_application
```

## Utilisation

1. Lancez le programme :

```bash
python main.py
```

2. Entrez le message à analyser
3. Entrez l'adresse email du destinataire
4. L'agent analysera le sentiment et enverra une réponse appropriée

## Structure du Projet

- `main.py` : Programme principal
- `requirements.txt` : Liste des dépendances
- `.env` : Configuration des variables d'environnement
- `.gitignore` : Fichiers ignorés par Git

## Fonctionnalités

- Analyse de sentiment binaire (positif/négatif)
- Génération de réponses automatiques
- Envoi d'emails via SMTP
- Interface en ligne de commande simple

## Sécurité

- Les informations sensibles (email, mot de passe) sont stockées dans le fichier `.env`
- Le fichier `.env` est ignoré par Git pour éviter les fuites d'informations

## Limitations

- Analyse de sentiment binaire uniquement
- Réponses prédéfinies
- Pas d'apprentissage automatique
- Pas de mémoire des conversations précédentes

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT.
