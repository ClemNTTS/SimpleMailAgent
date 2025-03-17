from imap_tools import MailBox, AND
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import sqlite3

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def recuperer_mails(email, password, server_imap):
  with MailBox(server_imap).login(email, password) as mailbox:
    mails = mailbox.fetch(AND(all=True))
    return [{
      'sujet': mail.subject,
      'expediteur': mail.from_,
      'contenu': mail.text or mail.html or mail.text_html,
      'date': mail.date,
    } for mail in mails]

def classer_mails(mails):
    from src.agent import analyser_mail
    from src.db import ajouter_mail
    import uuid

    mails_classes = []
    for mail in mails:
        try:
            # Vérifier si le mail existe déjà dans la base de données
            conn = sqlite3.connect('mails.db')
            c = conn.cursor()
            c.execute('''
                SELECT id FROM mails 
                WHERE sujet = ? AND expediteur = ? AND date_reception = ?
            ''', (mail['sujet'], mail['expediteur'], mail['date_reception']))
            existing_mail = c.fetchone()
            conn.close()

            if existing_mail:
                print(f"Mail déjà traité: {mail['sujet']}")
                continue

            # Analyse du mail avec l'agent IA
            reponse = analyser_mail(mail['contenu'])
            categorie = reponse['message']['content'].strip().lower()
            
            # Préparation du mail pour la base de données
            mail_db = {
                'id': str(uuid.uuid4()),
                'sujet': mail['sujet'],
                'expediteur': mail['expediteur'],
                'categorie': categorie,
                'date_reception': mail['date_reception']
            }
            
            # Ajout dans la base de données
            ajouter_mail(mail_db)
            mails_classes.append(mail_db)
            print(f"Mail classé avec succès: {mail['sujet']}")
            
        except Exception as e:
            print(f"Erreur lors du traitement du mail {mail['sujet']}: {str(e)}")
            continue
        
    return mails_classes


def envoyer_email(destinataire, sujet, message):
    """Envoie un email"""
    msg = MIMEText(message)
    msg['Subject'] = sujet
    msg['From'] = SMTP_USER
    msg['To'] = destinataire

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, destinataire, msg.as_string())

class MailFetcher:
    def __init__(self, email_address, password, imap_server="imap.gmail.com"):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap = None

    def connect(self):
        """Établit la connexion IMAP"""
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server)
            self.imap.login(self.email_address, self.password)
            return True
        except imaplib.IMAP4.error as e:
            print(f"Erreur d'authentification IMAP : {str(e)}")
            return False
        except Exception as e:
            print(f"Erreur de connexion IMAP : {str(e)}")
            return False

    def disconnect(self):
        """Ferme la connexion IMAP"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass

    def decode_subject(self, subject):
        """Décode le sujet du mail"""
        try:
            decoded_list = decode_header(subject)[0]
            if isinstance(decoded_list[0], bytes):
                return decoded_list[0].decode(decoded_list[1] or 'utf-8')
            return decoded_list[0]
        except:
            return subject

    def parse_date(self, date_str):
        """Parse la date du mail avec gestion des différents formats"""
        try:
            # Suppression des parenthèses et leur contenu
            date_str = date_str.split('(')[0].strip()
            
            # Liste des formats de date courants
            date_formats = [
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%d %b %Y %H:%M:%S %z",
                "%d %b %Y %H:%M:%S %Z",
                "%Y-%m-%d %H:%M:%S %z",
                "%Y-%m-%d %H:%M:%S %Z"
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Si aucun format ne fonctionne, retourner la date actuelle
            return datetime.now()
        except Exception as e:
            print(f"Erreur lors du parsing de la date '{date_str}': {str(e)}")
            return datetime.now()

    def extract_content(self, email_message):
        """Extrait le contenu du mail"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode()
                    elif part.get_content_type() == "text/html":
                        return part.get_payload(decode=True).decode()
            else:
                return email_message.get_payload(decode=True).decode()
        except Exception as e:
            print(f"Erreur lors de l'extraction du contenu: {str(e)}")
            return ""

    def fetch_emails(self, folder="INBOX", limit=10):
        """Récupère les derniers mails non lus"""
        if not self.connect():
            return []

        try:
            self.imap.select(folder)
            # Recherche des emails non lus avec le critère UNSEEN
            _, messages = self.imap.search(None, "UNSEEN")
            email_list = messages[0].split()
            
            if not email_list:
                print("Aucun email non lu trouvé")
                return []
                        
            # Récupère les derniers mails non lus
            emails = []
            for num in email_list[-limit:]:
                try:
                    _, msg_data = self.imap.fetch(num, "(RFC822)")
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extraction des informations du mail
                    subject = self.decode_subject(email_message.get("subject", "Sans sujet"))
                    from_addr = email_message.get("from", "Inconnu")
                    date_str = email_message.get("date", "")
                    date = self.parse_date(date_str)
                    
                    # Extraction du contenu
                    content = self.extract_content(email_message)
                    
                    if content:  # N'ajouter que si le contenu a été extrait avec succès
                        emails.append({
                            "sujet": subject,
                            "expediteur": from_addr,
                            "contenu": content,
                            "date_reception": date
                        })
                        print(f"Email traité avec succès: {subject}")
                    else:
                        print(f"Impossible d'extraire le contenu de l'email: {subject}")
                        
                except Exception as e:
                    print(f"Erreur lors du traitement d'un mail : {str(e)}")
                    continue
            
            print(f"Nombre d'emails traités avec succès: {len(emails)}")
            return emails
        except Exception as e:
            print(f"Erreur lors de la récupération des mails : {str(e)}")
            return []
        finally:
            self.disconnect()

def get_user_emails(user_id):
    """Récupère les mails d'un utilisateur depuis sa boîte mail"""
    try:
        # Récupérer les informations de connexion de l'utilisateur depuis la base de données
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        c.execute('SELECT email, imap_password, imap_server FROM users WHERE id = ?', (user_id,))
        user_info = c.fetchone()
        conn.close()
        
        if not user_info:
            print("Utilisateur non trouvé")
            return []
        
        email_address, password, imap_server = user_info
        
        # Créer une instance de MailFetcher et récupérer les mails
        fetcher = MailFetcher(email_address, password, imap_server)
        return fetcher.fetch_emails()
    except Exception as e:
        print(f"Erreur lors de la récupération des mails : {str(e)}")
        return []