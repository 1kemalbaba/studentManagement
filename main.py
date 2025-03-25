from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_filtered_students(search='', sort='name', grade_filter='', attendance_filter=''):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f'%{search}%')

    if grade_filter:
        query += " AND grade >= ?"
        params.append(float(grade_filter))

    if attendance_filter:
        query += " AND attendance_rate >= ?"
        params.append(float(attendance_filter))

    query += f" ORDER BY {sort}"
    
    cursor.execute(query, params)
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

@app.route('/')
def index():
    students = get_filtered_students(
        search=request.args.get('search', ''),
        sort=request.args.get('sort', 'name'),
        grade_filter=request.args.get('grade', ''),
        attendance_filter=request.args.get('attendance', '')
    )
    return render_template('index.html', students=students, search=request.args.get('search', ''))

@app.route('/get_students')
def get_students():
    students = get_filtered_students(
        search=request.args.get('search', ''),
        sort=request.args.get('sort', 'name'),
        grade_filter=request.args.get('grade', ''),
        attendance_filter=request.args.get('attendance', '')
    )
    return jsonify(students)

@app.route('/grades/<int:id>', methods=['GET', 'POST'])
def student_grades(id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        subject = request.form['subject']
        grade = float(request.form['grade'])
        cursor.execute(
            "INSERT INTO grades (student_id, subject, grade, date) VALUES (?, ?, ?, date('now'))",
            (id, subject, grade)
        )
        
        cursor.execute("""
            UPDATE students 
            SET grade = (SELECT AVG(grade) FROM grades WHERE student_id = ?)
            WHERE id = ?
        """, (id, id))
        
        conn.commit()
    
    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT * FROM grades WHERE student_id = ? ORDER BY date DESC", (id,))
    grades = cursor.fetchall()
    
    conn.close()
    return render_template('grades.html', student=student, grades=grades)

@app.route('/attendance/<int:id>', methods=['GET', 'POST'])
def student_attendance(id):
    from datetime import date
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        date = request.form['date']
        status = request.form['status']
        cursor.execute(
            "INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
            (id, date, status)
        )
        
        cursor.execute("""
            UPDATE students 
            SET attendance_rate = (
                SELECT (COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*))
                FROM attendance 
                WHERE student_id = ?
            )
            WHERE id = ?
        """, (id, id))
        
        conn.commit()
    
    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT * FROM attendance WHERE student_id = ? ORDER BY date DESC", (id,))
    attendance = cursor.fetchall()
    
    conn.close()
    return render_template('attendance.html', student=student, attendance=attendance, today=date.today())

@app.route('/add', methods=['POST'])
def add_student():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (student_id, name, email, date_of_birth, contact_info, class_id) VALUES (?, ?, ?, ?, ?, ?)",
        (
            request.form['student_id'],
            request.form['name'],
            request.form['email'],
            request.form['date_of_birth'],
            request.form['contact_info'],
            request.form['class_id'] or None
        )
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        if name:
            cursor.execute(
                "UPDATE students SET name=? WHERE id=?",
                (name, id)
            )
            conn.commit()
            return redirect(url_for('index'))

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    conn.close()

    if student is None:
        return redirect(url_for('index'))

    return render_template('edit.html', student=student)

@app.route('/delete/<int:id>')
def delete_student(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            date_of_birth DATE,
            grade REAL DEFAULT 0,
            attendance_rate REAL DEFAULT 100,
            contact_info TEXT,
            profile_photo TEXT,
            class_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date DATE,
            status TEXT CHECK(status IN ('present', 'absent', 'tardy')),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            grade REAL,
            date DATE,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)
    conn.commit()
    conn.close()
    app.run(host='0.0.0.0', port=3000, debug=True)