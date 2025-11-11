from flask import Flask, render_template, request, redirect, url_for ,flash , session
import mysql.connector
from mysql.connector import Error
import uuid
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv("variables.env")
class Database:
    
    HOST = os.environ.get("DB_HOST")
    USER = os.environ.get("DB_USER")
    PASSWORD = os.environ.get("DB_PASSWORD")
    DATABASE = os.environ.get("DB_NAME")

    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.HOST,
                user=self.USER,
                passwd=self.PASSWORD,
                database=self.DATABASE
            )
            return connection
        except Error as e:
            print(f"Error connecting to MariaDB: {e}")
            return None

    def get_user_data(self, user_id):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            query = "SELECT user_id, password, role FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result 
        
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def insert_leave_request(self, leave_data):
        connection = self.get_connection()
        if connection is None:
            return False

        cursor = connection.cursor()
        try:
            query = """
            INSERT INTO leaves (leave_id, rollno, reason, start_date, out_time, end_date, in_time, fa_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                leave_data['leave_id'],
                leave_data['rollno'],
                leave_data['reason'],
                leave_data['Sdate'],
                leave_data['OutTime'],
                leave_data['Edate'],
                leave_data['InTime'],
                "Pending"
            )
            cursor.execute(query, values)
            connection.commit()
            return True
        except Error as e:
            print(f"Error submitting leave request: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    def view_leaves(self, role, user_id):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            if role == "student":
                query = 'SELECT * FROM leaves WHERE rollno = %s ORDER BY id DESC'
                cursor.execute(query, (user_id,))
                leaves = cursor.fetchall()
                return leaves
            elif role == "faculty_advisor":
                query = 'SELECT * FROM leaves WHERE fa_status = "Pending" ORDER BY id DESC'
                cursor.execute(query)
                leaves = cursor.fetchall()
                return leaves
            elif role == "hostel_warden":
                query = 'SELECT * FROM leaves WHERE warden_status = "Pending" AND fa_status="Approved" ORDER BY id DESC'
                cursor.execute(query)
                leaves = cursor.fetchall()
                return leaves
            elif role == "academics":
                query = 'SELECT * FROM leaves WHERE admin_status = "Pending" AND warden_status="Approved" ORDER BY id DESC'
                cursor.execute(query)
                leaves = cursor.fetchall()
                return leaves
            elif role == "academics2":
                query = 'SELECT * FROM leaves WHERE admin_status = "Approved" ORDER BY id DESC'
                cursor.execute(query)
                leaves = cursor.fetchall()
                return leaves
            else:
                return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    def fa_approve_leave(self,id):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            query="UPDATE leaves SET fa_status = 'Approved' WHERE id = %s"
            cursor.execute(query,(id,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Some error occured: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    def warden_approve_leave(self,id):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            query="UPDATE leaves SET warden_status = 'Approved' WHERE id = %s"
            cursor.execute(query,(id,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Some error occured: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    def academics_approve_leave(self,id):
        connection = self.get_connection()
        if connection is None:
            return None
        cursor = connection.cursor(dictionary=True)
        try:
            query = "UPDATE leaves SET admin_status = 'Approved' WHERE id = %s"
            cursor.execute(query,(id,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Some error occured: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    

   
   


app = Flask(__name__)
db = Database()
app.secret_key = os.environ.get("APP_KEY")

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password_attempt = request.form.get('password')
        role_attempt = request.form.get('role')

        user_data = db.get_user_data(user_id) 

        if user_data:
            stored_hash_string = user_data.get('password') 

            password_attempt_bytes = password_attempt.encode('utf-8')
            
            stored_hash_bytes = stored_hash_string.encode('utf-8')

            if bcrypt.checkpw(password_attempt_bytes, stored_hash_bytes) and user_data['role'] == role_attempt:
                

                session['user_id'] = user_id
                session['role'] = role_attempt
                
                if role_attempt == 'student':
                    return redirect(url_for('student_dashboard'))
                elif role_attempt == 'faculty_advisor':
                    return redirect(url_for('fa_dashboard'))
                elif role_attempt == 'hostel_warden' :
                    return redirect(url_for('warden_dashboard'))
                elif role_attempt == 'academics' :
                    return redirect(url_for('academics_dashboard'))
                
        flash('Invalid credentials or role. Please try again.')
        return render_template('login_form.html', error_message="Invalid credentials or role. Please try again.")

    return render_template('login_form.html')





@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    return render_template('student_dashboard.html')

@app.route('/create_leave',methods=['GET','POST'])
def create_leave():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        leave_id_str=str(uuid.uuid4())
        reason=request.form.get('reason')
        Sdate=request.form.get('start_date')
        Edate=request.form.get('end_date')
        OutTime=request.form.get('out_time')
        InTime=request.form.get('in_time')
        rollno=session['user_id']
        leave_data={
            "leave_id" : leave_id_str,
            "rollno" : rollno,
            "reason" : reason,
            "Sdate" : Sdate,
            "OutTime" : OutTime,
            "Edate" : Edate,
            "InTime" : InTime
        }
        db = Database()
        if(db.insert_leave_request(leave_data)):
           return redirect(url_for('student_view_leaves'))
        else:
          return redirect(url_for('create_leave'))
    else:
        return render_template('createleave.html')
@app.route('/student_view_leaves')
def student_view_leaves():
          if 'user_id' not in session or session['role'] != 'student':
             flash('Unauthorized access.', 'error')
             return redirect(url_for('login'))
          try:
             leaves = db.view_leaves("student", session['user_id'])
             return render_template('student_view_leaves.html', leaves=leaves)
          except Exception as e:
              flash(f"An error occurred: {e}", 'error')
              return redirect(url_for('student_dashboard'))



@app.route('/fa_dashboard')
def fa_dashboard():
    if 'user_id' not in session or session['role'] != 'faculty_advisor':
        flash('Unauthorized access.','error')
        return redirect(url_for('login'))
    return render_template('fa_dashboard.html')

@app.route('/fa_pending_leaves', methods=['GET', 'POST'])
def fa_pending_leaves():
    if 'user_id' not in session or session['role'] != 'faculty_advisor':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        leave_id = request.form.get('leave_id')
        if db.fa_approve_leave(leave_id):
            flash(f"Leave {leave_id} approved successfully.", 'success')
        else:
            flash(f"Failed to approve leave {leave_id}.", 'error')
        return redirect(url_for('fa_pending_leaves'))
    
    try:
        leaves = db.view_leaves('faculty_advisor', session['user_id'])
        return render_template('fa_pending_leaves.html', leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('fa_dashboard'))
    
@app.route('/warden_dashboard')
def warden_dashboard():
    if 'user_id' not in session or session['role'] != 'hostel_warden':
        flash('Unauthorized access.','error')
        return redirect(url_for('login'))
    return render_template('warden_dashboard.html')

@app.route('/warden_pending_leaves', methods=['GET', 'POST'])
def warden_pending_leaves():
    if 'user_id' not in session or session['role'] != 'hostel_warden':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        leave_id = request.form.get('leave_id')
        if db.warden_approve_leave(leave_id):
            flash(f"Leave {leave_id} approved successfully.", 'success')
        else:
            flash(f"Failed to approve leave {leave_id}.", 'error')
        return redirect(url_for('warden_pending_leaves'))
    
    try:
        leaves = db.view_leaves('hostel_warden', session['user_id'])
        return render_template('warden_pending_leaves.html', leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('warden_dashboard'))

@app.route('/academics_dashboard')
def academics_dashboard():
    if 'user_id' not in session or session['role'] != 'academics':
        flash('Unauthorized access.','error')
        return redirect(url_for('login'))
    return render_template('academics_dashboard.html')

@app.route('/academics_pending_leaves', methods=['GET', 'POST'])
def academics_pending_leaves():
    if 'user_id' not in session or session['role'] != 'academics':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        leave_id = request.form.get('leave_id')
        if db.academics_approve_leave(leave_id):
            flash(f"Leave {leave_id} approved successfully.", 'success')
        else:
            flash(f"Failed to approve leave {leave_id}.", 'error')
        return redirect(url_for('academics_pending_leaves'))
    
    try:
        leaves = db.view_leaves('academics', session['user_id'])
        return render_template('academics_pending_leaves.html', leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('academics_dashboard'))
    
@app.route('/academics_approved_leaves',methods=['GET','POST'])
def academics_approved_leaves():
     if 'user_id' not in session or session['role'] != 'academics':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
     try:
        leaves = db.view_leaves('academics2', session['user_id'])
        return render_template('academics_approved_leaves.html', leaves=leaves)
     except Exception as e:
        flash(f"An error occurred: {e}", 'error')
        return redirect(url_for('academics_dashboard'))
     


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
