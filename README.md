# studentManagementStudent Management Web Application

Database Schema:
Table: students
- id (INTEGER PRIMARY KEY AUTOINCREMENT): Unique student identifier
- name (TEXT): Student's name
- grade (REAL): Student's grade (0-100)

How the Application Uses the Database:
1. The app uses SQLite to store data in 'students.db'.
2. On startup, it creates the 'students' table if it doesn't exist.
3. The main page (/) queries all students with 'SELECT * FROM students ORDER BY name' and displays them.
4. Adding a student (POST /add) inserts a new row with 'INSERT INTO students (name, grade) VALUES (?, ?)'.
5. Editing a student (POST /edit/<id>) updates a row with 'UPDATE students SET name=?, grade=? WHERE id=?'.
6. Deleting a student (/delete/<id>) removes a row with 'DELETE FROM students WHERE id=?'.
7. Each operation connects to the database using get_db(), commits changes, and closes the connection.

Routes:
- GET /: Main page displaying all students
- POST /add: Add a new student
- GET/POST /edit/<id>: Edit existing student
- GET /delete/<id>: Delete a student
