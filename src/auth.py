import sqlite3
import hashlib
import streamlit as st
from src.mails import MailFetcher

def init_auth_db():
    """Initialise la table des utilisateurs dans la base de données"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  imap_server TEXT DEFAULT "imap.gmail.com",
                  imap_password TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash le mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def test_imap_connection(email, password, imap_server="imap.gmail.com"):
    """Teste la connexion IMAP"""
    try:
        fetcher = MailFetcher(email, password, imap_server)
        if fetcher.connect():
            fetcher.disconnect()  # Ferme proprement la connexion
            return True
        return False
    except Exception as e:
        print(f"Erreur de connexion IMAP : {str(e)}")
        return False

def register_user(username, password, email, imap_password, imap_server="imap.gmail.com"):
    """Enregistre un nouvel utilisateur"""
    try:
        # Test de la connexion IMAP avant l'inscription
        if not test_imap_connection(email, imap_password, imap_server):
            return False, "Impossible de se connecter à la boîte mail. Vérifiez vos identifiants IMAP."

        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        hashed_password = hash_password(password)
        c.execute('''INSERT INTO users (username, password, email, imap_password, imap_server) 
                    VALUES (?, ?, ?, ?, ?)''',
                 (username, hashed_password, email, imap_password, imap_server))
        conn.commit()
        conn.close()
        return True, "Inscription réussie"
    except sqlite3.IntegrityError:
        return False, "Ce nom d'utilisateur ou cet email est déjà utilisé"
    except Exception as e:
        return False, f"Erreur lors de l'inscription : {str(e)}"

def update_user_email(user_id, new_email, imap_password, imap_server="imap.gmail.com"):
    """Met à jour l'email et les informations IMAP d'un utilisateur"""
    try:
        # Test de la connexion IMAP avant la mise à jour
        if not test_imap_connection(new_email, imap_password, imap_server):
            return False, "Impossible de se connecter à la nouvelle boîte mail. Vérifiez vos identifiants IMAP."

        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        c.execute('''UPDATE users 
                    SET email = ?, imap_password = ?, imap_server = ?
                    WHERE id = ?''',
                 (new_email, imap_password, imap_server, user_id))
        conn.commit()
        conn.close()
        return True, "Email et informations IMAP mises à jour avec succès"
    except Exception as e:
        return False, f"Erreur lors de la mise à jour : {str(e)}"

def verify_user(username, password):
    """Vérifie les identifiants de l'utilisateur"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?',
             (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user is not None

def login_form():
    """Affiche le formulaire de connexion"""
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
        
        if submit:
            if verify_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['user_id'] = get_user_id(username)
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Identifiants incorrects")

def register_form():
    """Affiche le formulaire d'inscription"""
    with st.form("register_form"):
        st.subheader("Informations de compte")
        username = st.text_input("Nom d'utilisateur")
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        
        st.subheader("Informations de la boîte mail")
        imap_server = st.text_input("Serveur IMAP", value="imap.gmail.com")
        imap_password = st.text_input("Mot de passe IMAP", type="password")
        
        submit = st.form_submit_button("S'inscrire")
        
        if submit:
            if password != confirm_password:
                st.error("Les mots de passe ne correspondent pas")
                return
            
            success, message = register_user(username, password, email, imap_password, imap_server)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def get_user_id(username):
    """Récupère l'ID d'un utilisateur à partir de son nom d'utilisateur"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

