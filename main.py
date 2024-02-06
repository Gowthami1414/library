from flask import Flask, request,abort, render_template, redirect, url_for, session,jsonify
import mysql.connector
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import base64
import csv
import json
from flask import send_file
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
app = Flask(__name__)
app.secret_key = '47af353f9906eb7c0c3048aaede906adb041888131b17116'
app.config['LOGIN_VIEW'] = 'login'
login_manager = LoginManager(app)
login_manager.init_app(app)
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Gokul@2004",
    database="students"
)
def send_email(recipient, subject, body):
    outlook_email = "gokultupakula@outlook.com"
    outlook_password = "Gokul@7868"
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    msg = MIMEMultipart()
    msg['From'] = outlook_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(outlook_email, outlook_password)
    server.sendmail(outlook_email, recipient, msg.as_string())
    server.quit()
@app.route('/secure_page')
@login_required
def secure_page():
    return "Welcome to the secure page!"
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
def validate_user_credentials(username, password):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM student_details WHERE Roll_number = %s AND password = %s', (username, password))
    user_data = cursor.fetchone()
    cursor.close()
    return user_data is not None
def get_user_data(username):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT Name, photo FROM student_details WHERE Roll_number = %s', (username,))
    user_data = cursor.fetchone()
    cursor.close()
    return user_data
def validate_admin_credentials(username, password):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM admins WHERE username = %s AND password = %s', (username, password))
    admin_data = cursor.fetchone()
    cursor.close()
    return admin_data is not None
@app.route('/', methods=['GET', 'POST'])
def login():
    error_message = None  # Initialize error message variable

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_admin_credentials(username, password):
            session['logged_in'] = True
            session['role'] = 'admin'
            return redirect(url_for('index'))  # Redirect to admin dashboard
        elif validate_user_credentials(username, password):
            session['logged_in'] = True
            session['role'] = 'user'
            user_data = get_user_data(username)
            if user_data:
                session['user_name'] = user_data.get('Name', 'User') 
            return redirect(url_for('student'))  # Redirect to user dashboard
        else:
            error_message = "Invalid credentials. Please try again."

    return render_template('login.html', error_message=error_message)

@app.route('/s')
def student():
    return render_template('excel.html')
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        roll_number = request.form['Roll_Number']
        name = request.form['Name']
        department = request.form['Department']
        year = request.form['Year']
        outlook = request.form['Outlook']
        photo = request.files['Photo'] 
        if 'Year' not in request.form:
            return "Year is missing in the form data. Please make sure the form includes a 'Year' field."
        cursor = conn.cursor()
        cursor.execute('INSERT INTO student_details (Roll_number, Name, year, Department,Outlook,photo) VALUES (%s, %s,%s, %s, %s,%s)', (roll_number, name, year, department, outlook,photo))
        conn.commit()
        cursor.close()
        print("""<script>document.getElementById('myForm').reset();</script>""")
        cursor.close()
    return render_template('add_student.html')
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_id = request.form['Bookid']
        book_name = request.form['Book_name']
        author_name = request.form['authorname']
        isbn_number = request.form['isbn']
        department = request.form['department']
        publisher = request.form['publisher']
        book_type = request.form.get('type', '')
        row_number = request.form['row']
        rack = request.form['rack']
        location = request.form['location']
        cursor = conn.cursor()
        cursor.execute('INSERT INTO book_details (bookid, bookname, authorname, isbn, department, publisher, type, `row`, rack, location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
               (book_id, book_name, author_name, isbn_number, department, publisher, book_type, row_number, rack, location))
        conn.commit()
        cursor.close()
        return "Book details added successfully."
    return render_template('add_book.html')
@app.route('/check_details', methods=['GET'])
def check_details():
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM student_details ORDER BY Roll_number DESC LIMIT 5')
    recent_students = cursor.fetchall()
    cursor.close()
    return render_template('check_details.html', recent_students=recent_students)
@app.route('/update_photo', methods=['GET', 'POST'])
def update_photo():
    if request.method == 'POST':
        roll_number = request.form['Roll_Number']
        image_file = request.files['Image_File']
        cursor = conn.cursor()
        check_query = 'SELECT * FROM student_details WHERE roll_number = %s'
        cursor.execute(check_query, (roll_number,))
        existing_student = cursor.fetchone()
        if existing_student:
            new_image_binary = image_file.read()
            update_query = 'UPDATE student_details SET photo = %s WHERE roll_number = %s'
            cursor.execute(update_query, (new_image_binary, roll_number))
            conn.commit()
            cursor.close()
            return f"Photo updated for student with roll number: {roll_number}"
        else:
            cursor.close()
            return f"Student with roll number {roll_number} not found in the database."
    return render_template('update_photo_form.html')
@app.route('/edit_student/<string:roll_number>', methods=['GET', 'POST'])
def edit_student(roll_number):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM student_details WHERE Roll_number = %s', (roll_number,))
    student_data = cursor.fetchone()
    cursor.close()
    if request.method == 'POST':
        new_name = request.form['Name']
        new_department = request.form['Department']
        new_year = request.form['Year']
        new_outlook = request.form['Outlook']
        cursor = conn.cursor()
        cursor.execute('UPDATE student_details SET Name = %s, Department = %s, year = %s, Outlook = %s WHERE Roll_number = %s',
                       (new_name, new_department, new_year, new_outlook, roll_number))
        conn.commit()
        cursor.close()
        return f"Student details for Roll Number {roll_number} updated successfully."
    return render_template('edit_student.html', roll_number=roll_number, student_data=student_data)
@app.route('/start', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        roll_number = request.form['Roll_Number']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM student_details WHERE Roll_number = %s', (roll_number,))
        student_data = cursor.fetchone()
        cursor.execute('SELECT * FROM book_transactions WHERE Roll_number = %s AND action = %s', (roll_number, 'taken'))
        book_transactions = cursor.fetchall()
        cursor.close()
        if student_data:
            can_take_book = len(book_transactions) < 4
            if 'photo' in student_data and student_data['photo']:
                photo_data = base64.b64encode(student_data['photo']).decode('utf-8')
                student_data['photo_data'] = f"data:image/png;base64,{photo_data}"
            else:
                student_data['photo_data'] = None
            return render_template('web.html', student_data=student_data, book_transactions=book_transactions, can_take_book=can_take_book)
        else:
            return "No data found for the provided Roll Number."
    return render_template('web.html', student_data=None, book_transactions=None, can_take_book=None)
from flask import request, render_template
@app.route('/view_book', methods=['GET', 'POST'])
def view_book():
    if request.method == 'POST':
        search_option = request.form['search_option']
        book_id = request.form.get('book_id', None)
        department = request.form.get('department', None)
        book_type = request.form.get('type', None)
        cursor = conn.cursor(dictionary=True)
        if search_option == 'bookid' and book_id:
            cursor.execute('SELECT * FROM book_details WHERE bookid = %s', (book_id,))
        elif search_option == 'department' and department:
            cursor.execute('SELECT * FROM book_details WHERE department = %s', (department,))
        elif search_option == 'department_type' and department and book_type:
            cursor.execute('SELECT * FROM book_details WHERE department = %s AND type = %s', (department, book_type))
        else:
            cursor.close()
            return "Invalid search parameters."
        book_data = cursor.fetchall()
        cursor.close()
        if book_data:
            return render_template('viewbook.html', book_data=book_data)
        else:
            return "Book not found."
    return render_template('viewbook.html', book_data=None)

@app.route('/history', methods=['GET', 'POST'])
def history_details():
    from datetime import datetime as dt, timedelta
    history = []
    if request.method == 'POST':
        roll_number = request.form['roll_number']
        taken_date = request.form['taken_date']
        if roll_number and taken_date:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history WHERE roll_number=%s AND DATE(taken_date)=DATE(%s)", (roll_number, taken_date))
            history = cursor.fetchall()
            cursor.close()
        elif roll_number:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history WHERE roll_number=%s", (roll_number,))
            history = cursor.fetchall()
            cursor.close()
        elif taken_date:
            input_date = dt.strptime(taken_date, '%Y-%m-%d').date()  
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history WHERE DATE(taken_date) = DATE(%s)", (input_date,))
            history = cursor.fetchall()
            cursor.close()
    return render_template('history.html', history=history)
@app.route('/download', methods=['POST'])
def download_csv():
    try:
        data = request.form['data']
        history_data = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Invalid JSON data: {str(e)}", 400
    csv_data = []
    for row in history_data:
        csv_data.append([str(value) for value in row.values()])
    with open('temp.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Roll Number', 'Book ID', 'Book Name', 'Author Name', 'Taken Date', 'Submitted'])
        csv_writer.writerows(csv_data)
    # Send the CSV file for download
    return send_file('temp.csv', as_attachment=True, download_name='search_results.csv')
@app.route('/get_roll_number_suggestions')
def get_roll_number_suggestions():
    query = request.args.get('query')
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT Roll_number FROM student_details WHERE Roll_number LIKE %s', (f'{query}%',))
    suggestions = cursor.fetchall()
    cursor.close()
    return jsonify(suggestions)
@app.route('/getbook/<string:Roll_number>', methods=['GET', 'POST'])
def get_book(Roll_number):
    book_data = None
    outlook_email = None
    if request.method == 'POST':
        book_id = request.form['book_id']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM book_transactions WHERE Roll_number = %s AND book_id = %s AND action = %s',
                       (Roll_number, book_id, 'taken'))
        taken = cursor.fetchone()
        if taken:
            return "Sorry, the book is already taken by you."
        cursor.execute('SELECT * FROM book_details WHERE bookid = %s', (book_id,))
        book_data = cursor.fetchone()
        cursor.execute('SELECT Outlook FROM student_details WHERE Roll_number = %s', (Roll_number,))
        outlook_data = cursor.fetchone()
        if outlook_data:
            outlook_email = outlook_data['Outlook']
        cursor.close()
        if book_data:
            final_submission_date = datetime.now() + timedelta(days=14)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO book_transactions (Roll_number, book_id, action, taken_date, Final_date) VALUES (%s, %s, %s, NOW(),%s)',
               (Roll_number, book_data['bookid'], 'taken',final_submission_date))
            cursor.execute('INSERT INTO history (roll_number, bookid, bookname,authorname, taken_date) VALUES (%s, %s,%s,%s, NOW())',
               (Roll_number, book_data['bookid'], book_data['bookname'], book_data['authorname'],))
            conn.commit()
            cursor.close()
            final_submission_date = datetime.now() + timedelta(days=14)
            format_date=final_submission_date.strftime("%d-%m-%Y %I:%M:%S %p")
            cursor = conn.cursor()
            conn.commit()
            cursor.close()
            subject = "Book Details Confirmation"
            current_date = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
            body = f"Book ID: {book_data['bookid']}\nBook Name: {book_data['bookname']}\nDate: {current_date}\nSubmit_within:{format_date}"
            send_email(outlook_email, subject, body)
            return "Book details stored successfully. Check your outlook."
        else:
            return "No book found for the provided Book ID."
    return render_template('getbook.html', roll_number=Roll_number, book_data=book_data, outlook_email=outlook_email)
@app.route('/submit_book/<string:Roll_number>', methods=['POST'])
def submit_book(Roll_number):
    if request.method == 'POST':
        book_id = request.form['book_id']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT Roll_number, book_id FROM book_transactions WHERE Roll_number = %s AND book_id = %s AND action = %s',
                       (Roll_number, book_id, 'taken'))
        book_transaction = cursor.fetchone()
        cursor.execute('SELECT Outlook FROM student_details WHERE Roll_number = %s', (Roll_number,))
        student_data = cursor.fetchone()
        if book_transaction and student_data:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM book_details WHERE bookid = %s', (book_id,))
            book_data = cursor.fetchone()
            if book_data:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM book_transactions WHERE Roll_number = %s AND book_id = %s', (Roll_number, book_id))
                cursor.execute('UPDATE history SET submited = NOW() WHERE roll_number = %s AND bookid=%s',(Roll_number,book_id))
                conn.commit()
                cursor.close()
                outlook_email = student_data['Outlook']
                subject = "Book Submission Confirmation"
                current_date = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                body = f"Book ID: {book_id}\nSubmission Date: {current_date}"
                cursor = conn.cursor()
                cursor.execute('UPDATE history SET submited = NOW() WHERE roll_number = %s AND bookid = %s', (Roll_number, book_id))
                conn.commit()
                cursor.close()
                send_email(outlook_email, subject, body)
                return "Book details submitted successfully."
            else:
                return "Invalid Book ID. Book not found in the book details database."
        else:
            return "Invalid Book ID for the provided Roll Number."
    return "Invalid request."
@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))
def generate_otp():
    import random
    return str(random.randint(1000, 9999))
def send_otp_to_email(outlook_email, otp):
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    sender_email = "gokultupakula@outlook.com"
    sender_password = "Gokul@7868"  
    msg = MIMEText(f"Your OTP: {otp}")
    msg['From'] = sender_email
    msg['To'] = outlook_email
    msg['Subject'] = "Password Reset OTP"
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, outlook_email, msg.as_string())
    server.quit()
@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    error_message=None
    if request.method == 'POST':
        username = request.form['username']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM student_details WHERE Roll_number = %s', (username,))
        user_data = cursor.fetchone()
        cursor.close()
        if user_data:
            outlook_email = user_data.get('Outlook')
            otp = generate_otp()
            send_otp_to_email(outlook_email, otp)
            session['reset_username'] = username
            session['reset_otp'] = otp
            return render_template('enter_otp.html')
        else:
            error_message = "Invalid user. Please enter a valid Roll number."
    return render_template('forgotpassword.html',error_message=error_message)
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form['otp']
    if entered_otp == session.get('reset_otp'):
        return render_template('reset_password.html')
    else:
        return "Incorrect OTP. Please try again."
@app.route('/reset_password', methods=['POST'])
def reset_password():
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    if new_password == confirm_password:
        username = session.get('reset_username')
        cursor = conn.cursor()
        cursor.execute('UPDATE student_details SET password = %s WHERE Roll_number = %s', (new_password, username))
        conn.commit()
        cursor.close()
        session.pop('reset_username', None)
        session.pop('reset_otp', None)
        return "Password reset successful. Please login with your new password."
    else:
        return "Passwords do not match. Please try again."
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
    app.secret_key = '47af353f9906eb7c0c3048aaede906adb041888131b17116'
