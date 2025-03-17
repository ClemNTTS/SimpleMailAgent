import sqlite3
import pandas as pd

def init_db():
    """Initialise la base de données des mails"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mails
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sujet TEXT,
                  expediteur TEXT,
                  contenu TEXT,
                  categorie TEXT,
                  date_reception TIMESTAMP,
                  user_id INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def reset_mails_table():
    """Supprime et recrée la table des mails"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS mails')
    c.execute('''CREATE TABLE mails
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sujet TEXT,
                  expediteur TEXT,
                  contenu TEXT,
                  categorie TEXT,
                  date_reception TIMESTAMP,
                  user_id INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def ajouter_mail(mail, user_id):
    """Ajoute un nouveau mail à la base de données"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''INSERT INTO mails (sujet, expediteur, contenu, categorie, date_reception, user_id) 
                 VALUES (?, ?, ?, ?, ?, ?)''', 
              (mail['sujet'], mail['expediteur'], mail['contenu'], 
               mail['categorie'], mail['date_reception'], user_id))
    conn.commit()
    conn.close()

def get_mails(user_id):
    """Récupère tous les mails d'un utilisateur"""
    conn = sqlite3.connect('mails.db')
    df = pd.read_sql_query("""
        SELECT * FROM mails 
        WHERE user_id = ?
        ORDER BY date_reception DESC
    """, conn, params=(user_id,))
    conn.close()
    return df

def supprimer_mail(mail_id, user_id):
    """Supprime un mail spécifique"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''DELETE FROM mails WHERE id = ? AND user_id = ?''', (mail_id, user_id))
    conn.commit()
    conn.close()

def get_mails_par_categorie(user_id):
    """Récupère le nombre de mails par catégorie pour un utilisateur"""
    conn = sqlite3.connect('mails.db')
    df = pd.read_sql_query("""
        SELECT categorie, COUNT(*) as count 
        FROM mails 
        WHERE user_id = ? 
        GROUP BY categorie
    """, conn, params=(user_id,))
    conn.close()
    return df

def delete_table_users():
    """Supprime la table des utilisateurs"""
    conn = sqlite3.connect('mails.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS users''')
    conn.commit()
    conn.close()

