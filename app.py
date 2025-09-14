import os
from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows the frontend to communicate with the backend

def get_db_connection():
    """Establishes a connection to the database."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """Fetches a list of all subjects."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM Subjects ORDER BY name;')
    subjects = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(subjects)

@app.route('/api/essays/subject/<int:subject_id>', methods=['GET'])
def get_essays_by_subject(subject_id):
    """Fetches all essays for a specific subject, including a count of responses."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Get subject name
    cur.execute('SELECT name FROM Subjects WHERE id = %s;', (subject_id,))
    subject = cur.fetchone()
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    
    # Get essays with response count
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
    """Fetches all details for a single essay, including all its responses and feedback."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch essay details
    cur.execute('SELECT * FROM Essays WHERE id = %s;', (essay_id,))
    essay = cur.fetchone()
    if not essay:
        return jsonify({"error": "Essay not found"}), 404

    # Fetch subject details for the essay
    cur.execute('SELECT id, name FROM Subjects WHERE id = %s;', (essay['subject_id'],))
    subject = cur.fetchone()
    essay['subject'] = subject

    # Fetch all responses for this essay
    cur.execute('SELECT * FROM Responses WHERE essay_id = %s ORDER BY grade DESC;', (essay_id,))
    responses = cur.fetchall()

    # Calculate average grade
    total_grade = 0
    if responses:
        for r in responses:
            total_grade += r.get('grade', 0)
        essay['average_grade'] = total_grade / len(responses)
    else:
        essay['average_grade'] = 0

    # Fetch highlights for each response
    for resp in responses:
        cur.execute('SELECT * FROM Highlights WHERE response_id = %s;', (resp['id'],))
        highlights = cur.fetchall()
        # The feedback is stored as JSONB, so it's already in the right format
        resp['highlights'] = highlights

    essay['responses'] = responses
    
    cur.close()
    conn.close()
    return jsonify(essay)

if __name__ == '__main__':
    # This part is for local development and not used by Render
    app.run(debug=True)
