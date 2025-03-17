import sqlite3
import pandas as pd
import os
from imap_tools import MailBox, AND
from datetime import datetime

def init_db():
    """Initialise la base de données des emails si elle n'existe pas"""
    try:
        # Vérifier si la base de données existe déjà
        if os.path.exists('mails.db'):
            print("La base de données existe déjà, pas de réinitialisation nécessaire")
            return
            
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS mails
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      expediteur TEXT NOT NULL,
                      objet TEXT,
                      contenu TEXT,
                      date_reception TIMESTAMP,
                      categorie TEXT,
                      reponse_automatique TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(id))''')
                      
        # Table pour les expéditeurs marqués comme pub
        c.execute('''CREATE TABLE IF NOT EXISTS expediteurs_pub
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      expediteur TEXT NOT NULL,
                      date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(id),
                      UNIQUE(user_id, expediteur))''')
                      
        conn.commit()
        conn.close()
        print("Base de données initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        raise

def reset_mails_table():
    """Réinitialise la table des mails"""
    try:
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        c.execute('DELETE FROM mails')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la réinitialisation de la table des mails : {e}")
        return False

def ajouter_mail(email, user_id):
    """Ajoute un email à la base de données"""
    try:
        # Vérification des champs requis
        required_fields = ['objet', 'expediteur', 'contenu', 'date_reception']
        for field in required_fields:
            if field not in email:
                print(f"Champ manquant dans l'email : {field}")
                return False

        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        
        # Vérification si l'email existe déjà
        c.execute('''
            SELECT id FROM mails 
            WHERE user_id = ? AND objet = ? AND expediteur = ? AND date_reception = ?
        ''', (user_id, email['objet'], email['expediteur'], email['date_reception']))
        
        if c.fetchone():
            print(f"Email déjà existant : {email['objet']}")
            return False
            
        # Insertion de l'email
        c.execute('''
            INSERT INTO mails (user_id, expediteur, objet, contenu, date_reception, categorie, reponse_automatique)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            email['expediteur'],
            email['objet'],
            email['contenu'],
            email['date_reception'],
            email.get('categorie', 'non classé'),
            email.get('reponse_automatique', '')
        ))
        
        conn.commit()
        conn.close()
        print(f"Email ajouté avec succès : {email['objet']}")
        return True
    except sqlite3.Error as e:
        print(f"Erreur de base de données lors de l'ajout de l'email : {e}")
        return False
    except Exception as e:
        print(f"Erreur inattendue lors de l'ajout de l'email : {e}")
        return False

def get_mails(user_id):
    """Récupère les emails d'un utilisateur"""
    try:
        conn = sqlite3.connect('mails.db')
        df = pd.read_sql_query('''
            SELECT id, expediteur, objet, contenu, date_reception, categorie 
            FROM mails 
            WHERE user_id = ? 
            ORDER BY date_reception DESC
        ''', conn, params=(user_id,))
        conn.close()
        return df
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")
        return None

def supprimer_mail(mail_id, user_id):
    """Supprime un mail spécifique"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''DELETE FROM mails WHERE id = ? AND user_id = ?''', (mail_id, user_id))
    conn.commit()
    conn.close()

def get_mails_par_categorie(user_id, categorie=None):
    """Récupère les emails d'un utilisateur, filtrés par catégorie si spécifiée"""
    try:
        conn = sqlite3.connect('mails.db')
        
        if categorie:
            query = '''
                SELECT id, expediteur, objet, contenu, date_reception, categorie, reponse_automatique 
                FROM mails 
                WHERE user_id = ? AND categorie = ?
                ORDER BY date_reception DESC
            '''
            params = (user_id, categorie)
        else:
            query = '''
                SELECT id, expediteur, objet, contenu, date_reception, categorie, reponse_automatique 
                FROM mails 
                WHERE user_id = ?
                ORDER BY date_reception DESC
            '''
            params = (user_id,)
            
        df = pd.read_sql_query(query, conn, params=params)
        print(f"Nombre d'emails trouvés: {len(df)}")
        print(f"Colonnes disponibles: {df.columns.tolist()}")
        
        conn.close()
        return df
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")
        return pd.DataFrame()

def delete_table_users():
    """Supprime la table des utilisateurs"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS users''')
    conn.commit()
    conn.close()

def marquer_expediteur_pub(user_id, expediteur):
    """Marque un expéditeur comme pub pour un utilisateur"""
    try:
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO expediteurs_pub (user_id, expediteur)
                     VALUES (?, ?)''', (user_id, expediteur))
        conn.commit()
        conn.close()
        print(f"Expéditeur marqué comme pub : {expediteur}")
        return True
    except Exception as e:
        print(f"Erreur lors du marquage de l'expéditeur comme pub : {e}")
        return False

def est_expediteur_pub(user_id, expediteur):
    """Vérifie si un expéditeur est marqué comme pub pour un utilisateur"""
    try:
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        c.execute('''SELECT 1 FROM expediteurs_pub 
                     WHERE user_id = ? AND expediteur = ?''', (user_id, expediteur))
        result = c.fetchone() is not None
        conn.close()
        return result
    except Exception as e:
        print(f"Erreur lors de la vérification de l'expéditeur : {e}")
        return False

def supprimer_mails_pub(user_id):
    """Supprime tous les mails de catégorie pub pour un utilisateur"""
    try:
        # Récupérer les informations IMAP de l'utilisateur
        from src.mails import get_imap_credentials
        credentials = get_imap_credentials(user_id)
        if not credentials:
            print("Impossible de récupérer les informations IMAP")
            return 0

        # Connexion à la base de données
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        
        # Récupérer les mails à supprimer
        c.execute('''SELECT id, expediteur, objet, contenu, date_reception 
                     FROM mails 
                     WHERE user_id = ? AND categorie = "pub"''', (user_id,))
        mails = c.fetchall()
        
        if not mails:
            conn.close()
            return 0

        # Connexion au serveur IMAP
        with MailBox(credentials['server']).login(credentials['email'], credentials['password']) as mailbox:
            # Pour chaque mail à supprimer
            for mail in mails:
                try:
                    # Nettoyage du sujet pour enlever les caractères spéciaux
                    sujet = mail[2].encode('ascii', 'ignore').decode('ascii')
                    
                    # Rechercher le mail sur le serveur IMAP (sans la date)
                    messages = mailbox.fetch(AND(
                        from_=mail[1],  # expediteur
                        subject=sujet  # objet nettoyé
                    ))
                    
                    # Supprimer le mail sur le serveur IMAP
                    for message in messages:
                        mailbox.delete(message.uid)
                        print(f"Mail supprimé sur le serveur IMAP : {sujet}")
                except Exception as e:
                    print(f"Erreur lors de la suppression du mail sur IMAP : {e}")
                    continue
        
        # Supprimer les mails de la base de données locale
        c.execute('''DELETE FROM mails 
                     WHERE user_id = ? AND categorie = "pub"''', (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"{len(mails)} mails pub supprimés")
        return len(mails)
    except Exception as e:
        print(f"Erreur lors de la suppression des mails pub : {e}")
        return 0

