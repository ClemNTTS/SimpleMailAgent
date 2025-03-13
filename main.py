import os
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib
import ollama

load_dotenv()

# SMTP server settings
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def analyser_sentiment(prompt):
  response = ollama.chat(
    model="gemma:2b",
    messages=[
      {
        "role": "system",
        "content": "Tu es un analyseur de sentiment binaire. Tu dois répondre UNIQUEMENT par le mot 'positif' ou 'négatif', sans ponctuation ni autre mot."
      },
      {
        "role": "user",
        "content": f"Analyse le sentiment de ce texte et réponds par UNIQUEMENT le mot 'positif' ou 'négatif' : {prompt}"
      }
    ],
    options={
      "temperature": 0.1,
      "stop": ["\n", ".", "!", "?"]
    }
  )
  # Nettoyage de la réponse pour ne garder que 'positif' ou 'négatif'
  reponse = response["message"]["content"].strip().lower()
  if "positif" in reponse:
    return "positif"
  elif "négatif" in reponse:
    return "négatif"
  else:
    return "négatif"  # réponse par défaut en cas d'erreur

def generer_email(sentiment):
  print(sentiment)
  if sentiment == 'positif':
    return "Merci pour votre gentil message !"
  else:
    return "Nous sommes désolés de ne pas avoir pu répondre à votre message. Nous allons nous en assurer et vous recontacter dans les plus brefs délais."

def envoyer_email(destinataire, sujet, message):
  msg = MIMEText(message)
  msg['Subject'] = sujet
  msg['From'] = SMTP_USER
  msg['To'] = destinataire

  with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(SMTP_USER, destinataire, msg.as_string())

def agent_ia(prompt, destinataire):
  sentiment = analyser_sentiment(prompt)
  email = generer_email(sentiment)
  envoyer_email(destinataire, "Réponse automatisée", email)

if __name__ == "__main__":
  prompt = input("Entrez votre message : ")
  destinataire = input("Entrez l'adresse email du destinataire : ")
  agent_ia(prompt, destinataire)

