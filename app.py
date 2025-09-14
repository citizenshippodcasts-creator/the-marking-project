import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import re

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

def get_db_connection():
    """Establishes a connection to the database using the external URL."""
    db_url = os.environ.get('DATABASEURL')
    
    # This part correctly parses the URL for the database library
    pattern = re.compile(r"postgresql://(?P<user>.+?):(?P<password>.+?)@(?P<host>.+?):(?P<port>\d+?)/(?P<dbname>.+)")
    match = pattern.match(db_url)
    
    if match:
        db_params = match.groupdict()
        conn = psycopg2.connect(
            dbname=db_params['dbname'],
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port']
        )
        return conn
    else:
        raise ValueError("Invalid DATABASEURL format")

# API ROUTES (These are unchanged)
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

# SERVE THE FRONTEND (These are unchanged)
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
