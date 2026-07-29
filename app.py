import os
from flask import Flask, request, jsonify, send_file, abort
from supabase import create_client

app = Flask(__name__)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://ujakxcwyahuwcglfbqcp.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqYWt4Y3d5YWh1d2NnbGZicWNwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzMjg0OTMsImV4cCI6MjEwMDkwNDQ5M30.hTOmv_xwWWm1lmnwWgi1gtpfX9yqVUi0dnf7K1KjTHI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def _extract_single_data(response):
    if response is None:
        return None
    return getattr(response, "data", None)

@app.route('/')
def serve_index():
    return send_file(os.path.join(ROOT_DIR, 'index.html'))

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(ROOT_DIR, filename)
    if os.path.isfile(file_path):
        return send_file(file_path)
    return abort(404)

@app.route('/api/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip()
    password = payload.get('password') or ''

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    college_resp = supabase.table('College').select('Cid, College_Name, Tic_email, Academic_Year').eq('Tic_email', email).maybe_single().execute()
    college = _extract_single_data(college_resp)
    if not isinstance(college, dict) or not college:
        return jsonify({"success": False, "message": "This TIC email is not registered in the College table"}), 401

    user_resp = supabase.table('users').select('*').eq('tic_email', email).eq('password', password).maybe_single().execute()
    user = _extract_single_data(user_resp)
    if not isinstance(user, dict) or not user:
        return jsonify({"success": False, "message": "Invalid password for this TIC email"}), 401

    teacher_resp = supabase.table('Teachers_Data').select('Teacher_Name, Mail, Cid').eq('Mail', email).maybe_single().execute()
    teacher = _extract_single_data(teacher_resp)

    return jsonify({
        "success": True,
        "user": {
            "email": email,
            "teacherName": teacher.get('Teacher_Name') if isinstance(teacher, dict) and teacher else email,
            "collegeId": college.get('Cid'),
            "collegeName": college.get('College_Name'),
            "academicYear": college.get('Academic_Year')
        }
    })

@app.route('/api/colleges', methods=['GET'])
def colleges():
    resp = supabase.table('College').select('Cid, College_Name').order('College_Name', desc=False).execute()
    return jsonify({"data": resp.data or []})

@app.route('/api/records', methods=['GET'])
def records():
    resp = supabase.table('College_Course_Teaching_Details').select('*').order('Id', desc=False).execute()
    return jsonify({"data": resp.data or []})

@app.route('/api/records', methods=['POST'])
def create_record():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "message": "No record data provided"}), 400

    resp = supabase.table('College_Course_Teaching_Details').insert(payload).execute()
    if getattr(resp, 'error', None):
        return jsonify({"success": False, "message": str(resp.error)}), 500

    return jsonify({"success": True, "data": resp.data or []})

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port, debug=True)
