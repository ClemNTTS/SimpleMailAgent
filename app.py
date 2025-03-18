from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from src.db import init_db, get_mails, get_mails_par_categorie, ajouter_mail, reset_mails_table, marquer_expediteur_pub, supprimer_mails_pub
from src.auth import init_auth_db, login_user, register_user, update_user_email, get_user as get_user_auth
from src.mails import get_user_emails, get_imap_credentials
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
    return render_template('index.html')

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

@app.route('/api/update-imap', methods=['POST'])
@login_required
def update_imap():
    try:
        data = request.json
        if not data or 'email' not in data or 'imap_password' not in data or 'imap_server' not in data:
            return jsonify({'error': 'Données manquantes'}), 400
            
        success = update_user_email(
            session['user_id'],
            data['email'],
            data['imap_password'],
            data['imap_server']
        )
        
        if success:
            return jsonify({'message': 'Informations IMAP mises à jour avec succès'})
        return jsonify({'error': 'Erreur lors de la mise à jour des informations IMAP'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Déconnexion réussie'})

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