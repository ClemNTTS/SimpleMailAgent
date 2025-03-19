from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from src.db import init_db, get_mails, get_mails_par_categorie, ajouter_mail, reset_mails_table, marquer_expediteur_pub, supprimer_mails_pub
from src.auth import init_auth_db, login_user, register_user, update_user_email, get_user as get_user_auth
from src.mails import get_user_emails, get_imap_credentials, get_unread_count, envoyer_email, test_imap_connection, update_imap_settings, update_gemini_api_key, get_gemini_api_key
from src.agent import analyser_mail
import os
from functools import wraps
import sqlite3

app = Flask(__name__, 
            static_folder='frontend/static',
            template_folder='frontend/templates')
app.secret_key = os.urandom(24)

# Initialisation des bases de données
init_auth_db()
init_db()   

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    # Vérifier si l'utilisateur a configuré ses informations IMAP
    credentials = get_imap_credentials(session['user_id'])
    if not credentials or not credentials.get('email') or not credentials.get('password'):
        return redirect(url_for('setup_imap'))
    return render_template('index.html')

@app.route('/setup-imap')
@login_required
def setup_imap():
    # Vérifier si l'utilisateur a déjà configuré ses informations IMAP
    credentials = get_imap_credentials(session['user_id'])
    if credentials and credentials.get('email') and credentials.get('password'):
        return redirect(url_for('index'))
    return render_template('setup_imap.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = login_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        
        return render_template('login.html', error="Identifiants invalides")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if register_user(username, password, email):
            return redirect(url_for('login'))
        
        return render_template('register.html', error="Erreur lors de l'inscription")
    
    return render_template('register.html')

@app.route('/api/user')
@login_required
def get_user():
    try:
        user = get_user_auth(session['user_id'])
        if not user:
            session.clear()
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        return jsonify({
            'username': user['username'],
            'email': user['email']
        })
    except Exception as e:
        print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        return jsonify({'error': 'Erreur serveur'}), 500
    
@app.route('/api/unread-count')
@login_required
def get_unread_mails_count():
    try:
        print(f"Récupération du nombre de mails non lus pour l'utilisateur {session['user_id']}")
        count = get_unread_count(session['user_id'])
        print(f"Nombre de mails non lus : {count}")
        return jsonify({'count': count})
    except Exception as e:
        print(f"Erreur lors de la récupération du nombre de mails non lus : {str(e)}")
        return jsonify({'error': 'Erreur serveur', 'details': str(e)}), 500


@app.route('/api/emails')
@login_required
def get_user_emails_api():
    """Récupère les emails de l'utilisateur connecté"""
    try:
        categorie = request.args.get("categorie")
        print(f"Récupération des emails pour la catégorie: {categorie}")
        
        # Récupération des emails depuis la base de données
        df = get_mails_par_categorie(session['user_id'], categorie)
        
        if df.empty:
            return jsonify([])
            
        # Conversion du DataFrame en liste de dictionnaires
        emails = df.to_dict('records')
        return jsonify(emails)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")
        return jsonify([]), 500

@app.route('/api/fetch-emails', methods=['POST'])
@login_required
def fetch_emails():
    try:
        credentials = get_imap_credentials(session['user_id'])
        if not credentials:
            return jsonify({
                'error': 'Informations IMAP non configurées',
                'message': 'Veuillez configurer vos informations IMAP dans les paramètres'
            }), 400
            
        if not credentials.get('email') or not credentials.get('password'):
            return jsonify({
                'error': 'Informations IMAP incomplètes',
                'message': 'Veuillez configurer votre email et mot de passe IMAP'
            }), 400
            
        emails = get_user_emails(session['user_id'])
        if emails is None:
            return jsonify({
                'error': 'Erreur de connexion IMAP',
                'message': 'Impossible de se connecter au serveur IMAP. Vérifiez vos informations.'
            }), 500
            
        if not emails:
            return jsonify({
                'message': 'Aucun nouvel email trouvé',
                'emails': []
            })
            
        for email in emails:
            try:
                categorie = analyser_mail(email['contenu'], email['expediteur'], session['user_id'])
                email['categorie'] = categorie
                ajouter_mail(email, session['user_id'])
            except Exception as e:
                print(f"Erreur lors du traitement de l'email : {e}")
                continue
        
        return jsonify({
            'message': f'{len(emails)} emails récupérés avec succès',
            'emails': emails
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors de la récupération des emails'
        }), 500

@app.route("/api/update-settings", methods=["POST"])
@login_required
def update_settings():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Aucune donnée reçue"}), 400
            
        if not all(key in data for key in ["email", "imap_password", "imap_server", "gemini_api_key"]):
            return jsonify({"error": "Données manquantes"}), 400

        # Test de la connexion IMAP
        success, message = test_imap_connection(data["email"], data["imap_password"], data["imap_server"])
        if not success:
            return jsonify({"error": message}), 400

        # Mise à jour des paramètres IMAP
        if not update_imap_settings(session['user_id'], data["email"], data["imap_password"], data["imap_server"]):
            return jsonify({"error": "Erreur lors de la mise à jour des paramètres IMAP"}), 500

        # Mise à jour de la clé API Gemini
        if not update_gemini_api_key(session['user_id'], data["gemini_api_key"]):
            return jsonify({"error": "Erreur lors de la mise à jour de la clé API Gemini"}), 500

        return jsonify({
            "message": "Paramètres mis à jour avec succès",
            "test_message": message
        }), 200
        
    except Exception as e:
        print(f"Erreur lors de la mise à jour des paramètres : {str(e)}")
        return jsonify({"error": "Erreur serveur lors de la mise à jour des paramètres"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/mark-sender-pub', methods=['POST'])
@login_required
def mark_sender_pub():
    try:
        data = request.json
        if not data or 'expediteur' not in data:
            return jsonify({'error': 'Données manquantes'}), 400
            
        success = marquer_expediteur_pub(session['user_id'], data['expediteur'])
        
        if success:
            return jsonify({'message': 'Expéditeur marqué comme pub avec succès'})
        return jsonify({'error': 'Erreur lors du marquage de l\'expéditeur'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-pub-emails', methods=['POST'])
@login_required
def delete_pub_emails():
    try:
        nb_supprimes = supprimer_mails_pub(session['user_id'])
        return jsonify({
            'message': f'{nb_supprimes} mails pub supprimés avec succès',
            'count': nb_supprimes
        })
    except Exception as e:
        print(f"Erreur lors de la suppression des mails pub : {e}")
        return jsonify({
            'error': 'Erreur lors de la suppression des mails pub'
        }), 500

@app.route("/api/emails/<int:email_id>", methods=["DELETE"])
@login_required
def delete_email(email_id):
    try:
        # Supprimer l'email de la base de données
        conn = sqlite3.connect("mails.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mails WHERE id = ? AND user_id = ?", (email_id, session["user_id"]))
        conn.commit()
        conn.close()

        return jsonify({"message": "Email supprimé avec succès"}), 200
    except Exception as e:
        print(f"Erreur lors de la suppression de l'email: {e}")
        return jsonify({"error": "Erreur lors de la suppression de l'email"}), 500

@app.route("/api/emails/<int:email_id>", methods=["GET"])
@login_required
def get_email(email_id):
    try:
        conn = sqlite3.connect("mails.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, expediteur, objet, contenu, date_reception, categorie, reponse_automatique 
            FROM mails 
            WHERE id = ? AND user_id = ?
        """, (email_id, session["user_id"]))
        email = cursor.fetchone()
        conn.close()

        if not email:
            return jsonify({"error": "Email non trouvé"}), 404

        # Convertir le tuple en dictionnaire avec les bons noms de champs
        email_dict = {
            "id": email[0],
            "user_id": email[1],
            "expediteur": email[2],
            "objet": email[3],
            "contenu": email[4],
            "date_reception": email[5],
            "categorie": email[6],
            "reponse_automatique": email[7]
        }

        return jsonify(email_dict), 200
    except Exception as e:
        print(f"Erreur lors de la récupération de l'email: {e}")
        return jsonify({"error": "Erreur lors de la récupération de l'email"}), 500

@app.route("/api/send-email", methods=["POST"])
@login_required
def send_email():
    try:
        data = request.json
        if not data or 'to' not in data or 'subject' not in data or 'content' not in data:
            return jsonify({"error": "Données manquantes"}), 400

        success = envoyer_email(
            data['to'],
            data['subject'],
            data['content'],
            user_id=session['user_id']
        )

        if success:
            return jsonify({"message": "Email envoyé avec succès"}), 200
        return jsonify({"error": "Erreur lors de l'envoi de l'email"}), 500

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return jsonify({"error": "Erreur lors de l'envoi de l'email"}), 500

@app.route("/api/get-settings")
@login_required
def get_settings():
    try:
        imap_settings = get_imap_credentials(session['user_id'])
        gemini_api_key = get_gemini_api_key(session['user_id'])
        
        return jsonify({
            "email": imap_settings["email"] if imap_settings else "",
            "imap_server": imap_settings["imap_server"] if imap_settings else "",
            "gemini_api_key": gemini_api_key or ""
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des paramètres : {str(e)}"}), 500

def init_db():
    """Initialise la base de données si elle n'existe pas"""
    try:
        # Vérifier si la base de données existe déjà
        if os.path.exists('mails.db'):
            print("La base de données existe déjà, pas de réinitialisation nécessaire")
            return
            
        # Créer la base de données si elle n'existe pas
        conn = sqlite3.connect('mails.db')
        c = conn.cursor()
        
        # Création de la table des utilisateurs
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      email TEXT UNIQUE NOT NULL,
                      imap_password TEXT,
                      imap_server TEXT)''')
                      
        # Création de la table des emails
        c.execute('''CREATE TABLE IF NOT EXISTS mails
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      expediteur TEXT NOT NULL,
                      objet TEXT,
                      contenu TEXT,
                      date_reception TIMESTAMP,
                      categorie TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(id))''')
                      
        conn.commit()
        conn.close()
        print("Base de données initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        raise

if __name__ == '__main__':
    # Initialiser la base de données si elle n'existe pas
    if not os.path.exists('mails.db'):
        init_db()
    app.run(debug=True) 