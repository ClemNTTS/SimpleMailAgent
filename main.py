import streamlit as st
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
    if not df.empty:
        # Affichage des mails importants
        st.subheader("📌 Mails Importants")
        mails_importants = df[df['categorie'] == 'important']
        if not mails_importants.empty:
            for _, mail in mails_importants.iterrows():
                with st.expander(f"📧 {mail['sujet']} - {mail['expediteur']}"):
                    st.write(f"**Date:** {mail['date_reception']}")
                    with st.container():
                        st.markdown(
                            f"""
                            <div style="height: 300px; overflow-y: auto;">
                            **Contenu:** {mail['contenu']}...
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
        else:
            st.info("Aucun mail important")
        
        # Affichage des mails automatiques
        st.subheader("🤖 Mails Automatiques")
        mails_automatiques = df[df['categorie'] == 'automatique']
        if not mails_automatiques.empty:
            for _, mail in mails_automatiques.iterrows():
                with st.expander(f"📧 {mail['sujet']} - {mail['expediteur']}"):
                    st.write(f"**Date:** {mail['date_reception']}")
                    st.write(f"**Contenu:** {mail['contenu'][:200]}...")
        else:
            st.info("Aucun mail automatique")
        
        # Affichage des mails neutres
        st.subheader("📬 Mails Neutres")
        mails_neutres = df[df['categorie'] == 'neutre']
        if not mails_neutres.empty:
            for _, mail in mails_neutres.iterrows():
                with st.expander(f"📧 {mail['sujet']} - {mail['expediteur']}"):
                    st.write(f"**Date:** {mail['date_reception']}")
                    st.write(f"**Contenu:** {mail['contenu'][:200]}...")
        else:
            st.info("Aucun mail neutre")
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
    # Initialisation de la base de données
    init_auth_db()
    init_db()
    
    # Vérification de l'authentification
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.username = None
    
    # Page d'authentification
    if not st.session_state['logged_in']:
        st.title("Connexion / Inscription")
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
            
            # Bouton pour récupérer les nouveaux mails
            if st.button("🔄 Récupérer les nouveaux mails"):
                with st.spinner("Récupération des mails en cours..."):
                    emails = get_user_emails(st.session_state['user_id'])
                    for email in emails:
                        categorie = analyser_mail(email['contenu'])
                        email['categorie'] = categorie
                        ajouter_mail(email, st.session_state['user_id'])
                    st.success(f"{len(emails)} mails récupérés et analysés")
            
            # Paramètres IMAP
            with st.expander("⚙️ Paramètres IMAP"):
                afficher_parametres_imap()
            
            # Bouton de déconnexion
            if st.button("🚪 Se déconnecter"):
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['user_id'] = None
                st.rerun()
        
        # Interface principale
        st.title("📧 Gestionnaire d'Emails")
        
        # Affichage des mails par catégorie
        afficher_derniers_mails()

if __name__ == "__main__":
    main()

