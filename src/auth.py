import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

def init_auth_db():
    """Initialise la base de données d'authentification"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    
    # Création de la table users avec tous les champs nécessaires
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT UNIQUE,
                  imap_password TEXT,
                  imap_server TEXT,
                  gemini_api_key TEXT)''')
    
    conn.commit()
    conn.close()

def register_user(username, password, email=None, imap_password=None, imap_server="imap.gmail.com"):
    """Enregistre un nouvel utilisateur"""
    try:
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        hashed_password = generate_password_hash(password)
        c.execute('''INSERT INTO users (username, password, email, imap_password, imap_server) 
                    VALUES (?, ?, ?, ?, ?)''',
                 (username, hashed_password, email, imap_password, imap_server))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    """Authentifie un utilisateur"""
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user[2], password):
        return {'id': user[0], 'username': user[1], 'email': user[3]}
    return None

def update_user_email(user_id, new_email, imap_password=None, imap_server=None):
    """Met à jour l'email et les informations IMAP d'un utilisateur"""
    try:
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ? AND id != ?', (new_email, user_id))
        existing_user = c.fetchone()
        
        if existing_user:
            conn.close()
            raise ValueError("Cet email est déjà utilisé par un autre utilisateur")
        
        if imap_password and imap_server:
            c.execute('''UPDATE users 
                        SET email = ?, imap_password = ?, imap_server = ?
                        WHERE id = ?''',
                     (new_email, imap_password, imap_server, user_id))
        else:
            c.execute('UPDATE users SET email = ? WHERE id = ?',
                     (new_email, user_id))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Erreur lors de la mise à jour de l'email : {e}")
        if 'UNIQUE constraint failed' in str(e):
            raise ValueError("Cet email est déjà utilisé par un autre utilisateur")
        raise Exception(f"Erreur de base de données : {str(e)}")
    except Exception as e:
        print(f"Erreur inattendue lors de la mise à jour de l'email : {e}")
        raise

def get_user(user_id):
    """Récupère les informations d'un utilisateur"""
    try:
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[3],
                'imap_server': user[5] or 'imap.gmail.com'
            }
        return None
    except sqlite3.Error as e:
        print(f"Erreur de base de données lors de la récupération de l'utilisateur : {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue lors de la récupération de l'utilisateur : {e}")
        return None

def update_gemini_api_key(user_id, api_key):
    """Met à jour la clé API Gemini d'un utilisateur"""
    try:
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        c.execute('UPDATE users SET gemini_api_key = ? WHERE id = ?', (api_key, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Erreur lors de la mise à jour de la clé API : {e}")
        return False

def get_gemini_api_key(user_id):
    """Récupère la clé API Gemini d'un utilisateur"""
    try:
        conn = sqlite3.connect('auth.db')
        c = conn.cursor()
        c.execute('SELECT gemini_api_key FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération de la clé API : {e}")
        return None

