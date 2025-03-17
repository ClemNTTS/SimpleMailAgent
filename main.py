import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from src.db import init_db, delete_table_users, ajouter_mail, get_mails_par_categorie, get_mails, reset_mails_table
from src.agent import analyser_mail, generer_reponse
from src.auth import init_auth_db, login_form, register_form, update_user_email
from src.mails import get_user_emails

# Chargement des variables d'environnement
load_dotenv()

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Assistant IA de Gestion des Emails",
    page_icon="📧",
    layout="wide"
)

# Initialisation de la session
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

def traiter_nouveau_mail():
    """Interface pour traiter un nouveau mail"""
    st.subheader("Traitement d'un nouveau mail")
    
    # Bouton pour récupérer les mails automatiquement
    if st.button("Récupérer les nouveaux mails"):
        with st.spinner("Récupération des mails en cours..."):
            emails = get_user_emails(st.session_state['user_id'])
            for email in emails:
                categorie = analyser_mail(email['contenu'])
                email['categorie'] = categorie
                ajouter_mail(email, st.session_state['user_id'])
            st.success(f"{len(emails)} mails récupérés et analysés")
    
    # Formulaire manuel
    with st.form("nouveau_mail"):
        sujet = st.text_input("Sujet du mail")
        expediteur = st.text_input("Expéditeur")
        contenu = st.text_area("Contenu du mail")
        
        if st.form_submit_button("Analyser"):
            if sujet and expediteur and contenu:
                categorie = analyser_mail(contenu)
                
                # Création du dictionnaire mail
                mail = {
                    'sujet': sujet,
                    'expediteur': expediteur,
                    'contenu': contenu,
                    'categorie': categorie,
                    'date_reception': datetime.now()
                }
                
                # Sauvegarde dans la base de données
                ajouter_mail(mail, st.session_state['user_id'])
                
                st.success(f"Mail classé comme : {categorie}")
                st.write("Réponse générée :", generer_reponse(categorie))

def afficher_statistiques():
    """Affiche les statistiques de classification"""
    df = get_mails_par_categorie(st.session_state['user_id'])
    st.subheader("Statistiques de classification")
    if not df.empty:
        st.bar_chart(df.set_index('categorie'))
    else:
        st.info("Aucun mail traité pour le moment")

def afficher_derniers_mails():
    """Affiche les derniers mails traités"""
    df = get_mails(st.session_state['user_id'])
    st.subheader("Derniers mails traités")
    if not df.empty:
        st.dataframe(df.head())
    else:
        st.info("Aucun mail traité pour le moment")

def afficher_parametres_imap():
    """Affiche le formulaire de mise à jour des paramètres IMAP"""
    st.subheader("Paramètres de la boîte mail")
    with st.form("update_imap"):
        new_email = st.text_input("Nouvelle adresse email")
        imap_password = st.text_input("Nouveau mot de passe IMAP", type="password")
        imap_server = st.text_input("Serveur IMAP", value="imap.gmail.com")
        
        if st.form_submit_button("Mettre à jour"):
            if new_email and imap_password:
                success, message = update_user_email(st.session_state['user_id'], new_email, imap_password, imap_server)
                if success:
                    st.success(message)
                else:
                    st.error(message)

def main():
    # Initialisation des bases de données
    init_auth_db()
    reset_mails_table()  # Réinitialise la table des mails avec la bonne structure
    
    # Page d'authentification
    if not st.session_state['logged_in']:
        st.title("Connexion / Inscription")
        st.button("Supprimer la table des utilisateurs", on_click=delete_table_users)
        
        tab1, tab2 = st.tabs(["Connexion", "Inscription"])
        
        with tab1:
            login_form()
        
        with tab2:
            register_form()
    
    # Application principale
    else:
        # Barre latérale avec informations utilisateur
        with st.sidebar:
            st.write(f"Connecté en tant que : {st.session_state['username']}")
            
            # Paramètres IMAP
            afficher_parametres_imap()
            
            # Boutons de déconnexion et de réinitialisation
            if st.button("Se déconnecter"):
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['user_id'] = None
                st.rerun()
            
            st.divider()
            st.write("Options de maintenance")
            st.button("Supprimer la table des mails", on_click=reset_mails_table)
            st.button("Supprimer la table des utilisateurs", on_click=delete_table_users)
        
        # Interface principale
        st.title(f"Assistant IA de Gestion des Emails 📧")
        
        # Création des onglets
        tab1, tab2, tab3 = st.tabs(["Nouveau Mail", "Statistiques", "Historique"])
        
        with tab1:
            traiter_nouveau_mail()
        
        with tab2:
            afficher_statistiques()
        
        with tab3:
            afficher_derniers_mails()

if __name__ == "__main__":
    main()

