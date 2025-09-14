
import os
from flask import Flask, jsonify, send_from_directory
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app) # Allows the frontend to communicate with the backend

def get_db_connection():
    """Establishes a connection to the database."""
    # Use DATABASEURL key, which was corrected for Render
    conn = psycopg2.connect(os.environ.get('DATABASEURL'))
    return conn

# API ROUTES
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM Subjects ORDER BY name;')
    subjects = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(subjects)

@app.route('/api/essays/subject/<int:subject_id>', methods=['GET'])
def get_essays_by_subject(subject_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT name FROM Subjects WHERE id = %s;', (subject_id,))
    subject = cur.fetchone()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    cur.execute('''
        SELECT e.*, COUNT(r.id) AS response_count
        FROM Essays e
        LEFT JOIN Responses r ON e.id = r.essay_id
        WHERE e.subject_id = %s
        GROUP BY e.id
        ORDER BY e.title;
    ''', (subject_id,))
    essays = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify({"subject_name": subject['name'], "essays": essays})

@app.route('/api/essays/<int:essay_id>', methods=['GET'])
def get_essay_details(essay_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM Essays WHERE id = %s;', (essay_id,))
    essay = cur.fetchone()
    if not essay:
        return jsonify({"error": "Essay not found"}), 404

    cur.execute('SELECT id, name FROM Subjects WHERE id = %s;', (essay['subject_id'],))
    subject = cur.fetchone()
    essay['subject'] = subject

    cur.execute('SELECT * FROM Responses WHERE essay_id = %s ORDER BY grade DESC;', (essay_id,))
    responses = cur.fetchall()

    total_grade = sum(r.get('grade', 0) for r in responses)
    essay['average_grade'] = (total_grade / len(responses)) if responses else 0

    for resp in responses:
        cur.execute('SELECT * FROM Highlights WHERE response_id = %s;', (resp['id'],))
        highlights = cur.fetchall()
        resp['highlights'] = highlights

    essay['responses'] = responses
    
    cur.close()
    conn.close()
    return jsonify(essay)

# SERVE THE FRONTEND
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # This will serve style.css and script.js
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
