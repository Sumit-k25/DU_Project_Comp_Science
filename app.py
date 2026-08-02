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

    user_resp = (
    supabase.table('Users')
    .select('*')
    .eq('tic_mail', email)
    .eq('password', password)
    .maybe_single()
    .execute()
                )
    
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

@app.route('/api/programs', methods=['GET'])
def programs():
    college_id = request.args.get('collegeId') or request.args.get('Cid')
    if not college_id:
        return jsonify({"data": []})
    try:
        college_id = int(college_id)
    except ValueError:
        return jsonify({"data": []})

    resp = (
        supabase.table('College_Program')
        .select('Program_id, Program_Name')
        .eq('Cid', college_id)
        .order('Program_Name', desc=False)
        .execute()
    )
    return jsonify({"data": resp.data or []})

@app.route('/api/records', methods=['GET'])
def records():
    tic_email = (request.args.get('ticEmail') or '').strip()
    college_id = request.args.get('collegeId') or request.args.get('Cid')

    builder = supabase.table('College_Course_Teaching_Details').select('*')

    if tic_email:
        teacher_resp = (
            supabase.table('Teachers_Data')
            .select('Cid')
            .eq('Mail', tic_email)
            .maybe_single()
            .execute()
        )
        teacher_data = _extract_single_data(teacher_resp)
        if isinstance(teacher_data, dict) and teacher_data.get('Cid') is not None:
            college_id = teacher_data.get('Cid')

    if college_id:
        try:
            builder = builder.eq('Cid', int(college_id))
        except ValueError:
            pass

    resp = builder.order('Id', desc=False).execute()
    rows = resp.data or []
    enriched = []

    for row in rows:
        program_name = None
        paper_name = None
        teacher_name = None

        if row.get('Program_Id') is not None:
            program_resp = (
                supabase.table('College_Program')
                .select('Program_Name')
                .eq('Program_id', int(row['Program_Id']))
                .maybe_single()
                .execute()
            )
            program_data = _extract_single_data(program_resp)
            if isinstance(program_data, dict):
                program_name = program_data.get('Program_Name')

        if row.get('UPC_Code') is not None:
            paper_resp = (
                supabase.table('Papers')
                .select('Paper_Name')
                .eq('UPC_Code', int(row['UPC_Code']))
                .maybe_single()
                .execute()
            )
            paper_data = _extract_single_data(paper_resp)
            if isinstance(paper_data, dict):
                paper_name = paper_data.get('Paper_Name')

        if row.get('Teacher_id') is not None:
            teacher_resp = (
                supabase.table('Teachers_Data')
                .select('Teacher_Name')
                .eq('Teacher_Id', int(row['Teacher_id']))
                .maybe_single()
                .execute()
            )
            teacher_data = _extract_single_data(teacher_resp)
            if isinstance(teacher_data, dict):
                teacher_name = teacher_data.get('Teacher_Name')

        enriched.append({
            **row,
            'Program_Name': program_name,
            'Paper_Name': paper_name,
            'Teacher_Name': teacher_name,
        })

    return jsonify({"data": enriched})

@app.route('/api/teachers', methods=['GET'])
def teachers():
    college_id = request.args.get('collegeId') or request.args.get('Cid')
    if not college_id:
        return jsonify({"data": []})
    try:
        college_id = int(college_id)
    except ValueError:
        return jsonify({"data": []})

    resp = (
        supabase.table('Teachers_Data')
        .select('Teacher_Id, Teacher_Name')
        .eq('Cid', college_id)
        .eq('Status', 'Active')
        .order('Teacher_Name', desc=False)
        .execute()
    )
    return jsonify({"data": resp.data or []})

@app.route('/api/teacher-details', methods=['GET'])
def teacher_details():
    teacher_id = request.args.get('teacherId')
    academic_year = request.args.get('academicYear')

    if not teacher_id:
        return jsonify({"success": False, "message": "teacherId is required"}), 400

    try:
        teacher_id = int(teacher_id)
    except ValueError:
        return jsonify({"success": False, "message": "teacherId must be numeric"}), 400

    teacher_resp = (
        supabase.table('Teachers_Data')
        .select('Teacher_Id, Teacher_Name, Mail, Cid, Status')
        .eq('Teacher_Id', teacher_id)
        .maybe_single()
        .execute()
    )
    teacher_data = _extract_single_data(teacher_resp)

    builder = supabase.table('College_Course_Teaching_Details').select('*').eq('Teacher_id', teacher_id)
    if academic_year:
        builder = builder.eq('Academic_Year', int(academic_year))
    records_resp = builder.order('Id', desc=False).execute()
    records = records_resp.data or []

    enriched_courses = []
    for row in records:
        program_name = None
        paper_name = None

        if row.get('Program_Id') is not None:
            program_resp = (
                supabase.table('College_Program')
                .select('Program_Name')
                .eq('Program_id', int(row['Program_Id']))
                .maybe_single()
                .execute()
            )
            program_data = _extract_single_data(program_resp)
            if isinstance(program_data, dict):
                program_name = program_data.get('Program_Name')

        if row.get('UPC_Code') is not None:
            paper_resp = (
                supabase.table('Papers')
                .select('Paper_Name')
                .eq('UPC_Code', int(row['UPC_Code']))
                .maybe_single()
                .execute()
            )
            paper_data = _extract_single_data(paper_resp)
            if isinstance(paper_data, dict):
                paper_name = paper_data.get('Paper_Name')

        enriched_courses.append({
            **row,
            'Program_Name': program_name,
            'Paper_Name': paper_name,
        })

    return jsonify({
        "success": True,
        "teacher": teacher_data or {},
        "courses": enriched_courses,
    })

@app.route('/api/papers', methods=['GET'])
def papers():
    semester = request.args.get('semester')

    builder = supabase.table('Papers').select('UPC_Code, Paper_Name, Semester, Paper_Type')
    if semester:
        try:
            builder = builder.eq('Semester', int(semester))
        except ValueError:
            pass

    resp = builder.order('Paper_Name', desc=False).execute()
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
