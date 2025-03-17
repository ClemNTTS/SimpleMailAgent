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
      'contenu': mail.text or mail.html,
      'date': mail.date,
    } for mail in mails]

def classer_mails(mails):
    from src.agent import analyser_mail
    from datetime import datetime
    from src.db import ajouter_mail
    import uuid

    mails_classes = []
    for mail in mails:
        # Analyse du mail avec l'agent IA
        reponse = analyser_mail(mail['contenu'])
        categorie = reponse['message']['content'].strip().lower()
        
        # Préparation du mail pour la base de données
        mail_db = {
            'id': str(uuid.uuid4()),
            'sujet': mail['sujet'],
            'expediteur': mail['expediteur'],
            'categorie': categorie,
            'date_reception': mail['date']
        }
        
        # Ajout dans la base de données
        ajouter_mail(mail_db)
        mails_classes.append(mail_db)
        
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
        except Exception as e:
            print(f"Erreur de connexion : {e}")
            return False

    def disconnect(self):
        """Ferme la connexion IMAP"""
        if self.imap:
            self.imap.close()
            self.imap.logout()

    def decode_subject(self, subject):
        """Décode le sujet du mail"""
        decoded_list = decode_header(subject)[0]
        if isinstance(decoded_list[0], bytes):
            return decoded_list[0].decode(decoded_list[1] or 'utf-8')
        return decoded_list[0]

    def fetch_emails(self, folder="INBOX", limit=10):
        """Récupère les derniers mails"""
        if not self.connect():
            return []

        try:
            self.imap.select(folder)
            _, messages = self.imap.search(None, "ALL")
            email_list = messages[0].split()
            
            # Récupère les derniers mails
            emails = []
            for num in email_list[-limit:]:
                _, msg_data = self.imap.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extraction des informations du mail
                subject = self.decode_subject(email_message["subject"])
                from_addr = email_message["from"]
                date_str = email_message["date"]
                date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                
                # Extraction du contenu
                content = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                            break
                else:
                    content = email_message.get_payload(decode=True).decode()
                
                emails.append({
                    "sujet": subject,
                    "expediteur": from_addr,
                    "contenu": content,
                    "date_reception": date
                })
            
            return emails
        except Exception as e:
            print(f"Erreur lors de la récupération des mails : {e}")
            return []
        finally:
            self.disconnect()

def get_user_emails(user_id):
    """Récupère les mails d'un utilisateur depuis sa boîte mail"""
    # Récupérer les informations de connexion de l'utilisateur depuis la base de données
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('SELECT email, password, imap_server FROM users WHERE id = ?', (user_id,))
    user_info = c.fetchone()
    conn.close()
    
    if not user_info:
        return []
    
    email_address, password, imap_server = user_info
    
    # Créer une instance de MailFetcher et récupérer les mails
    fetcher = MailFetcher(email_address, password, imap_server)
    return fetcher.fetch_emails()