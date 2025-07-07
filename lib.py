from flask import Flask, request, render_template
import mysql.connector
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import base64
app = Flask(__name__)
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Gowthu@149",
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
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        roll_number = request.form['Roll_Number']
        name = request.form['Name']
        department = request.form['Department']
        outlook = request.form['Outlook']
        cursor = conn.cursor()
        cursor.execute('INSERT INTO student_details (Roll_number, Name, Department, Outlook) VALUES (%s, %s, %s, %s)', (roll_number, name, department, outlook))
        conn.commit()
        cursor.close()
        return "Student details added successfully."
    return render_template('add_student.html')
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_id = request.form['Book_id']
        book_name = request.form['Book_name']
        author_name = request.form['authorname']
        cursor = conn.cursor()
        cursor.execute('INSERT INTO book_details (bookid, bookname,authorname) VALUES (%s, %s, %s)',(book_id,book_name,author_name))
        conn.commit()
        cursor.close()
        return "Book details added successfully."
    return render_template('add_book.html')
'''@app.route('/remove_book',methods=['POST','GET'])
def remove_book():
    if request.method=='POST':
        bood_id=request.form['book_id']
        cursor=conn.cursor()
        cursor.excetue(slect * from book_details)'''
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
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        roll_number = request.form['Roll_Number']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM student_details WHERE Roll_number = %s', (roll_number,))
        student_data = cursor.fetchone()
        cursor.close()
        if student_data:
            can_take_book = student_data['bookid'] is None
            if 'photo' in student_data and student_data['photo']:
                photo_data = base64.b64encode(student_data['photo']).decode('utf-8')
                student_data['photo_data'] = f"data:image/png;base64,{photo_data}"
            else:
                student_data['photo_data'] = None
            return render_template('web.html', student_data=student_data, can_take_book=can_take_book)
        else:
            return "No data found for the provided Roll Number."
    return render_template('web.html', student_data=None, can_take_book=None)
@app.route('/taken_books/<string:Roll_number>')
def taken_books(Roll_number):
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT book_id FROM book_transactions WHERE Roll_number = %s AND action = %s', (Roll_number, 'taken'))
    taken_books = cursor.fetchall()
    cursor.close()
    return render_template('taken_books.html', taken_books=taken_books)
@app.route('/getbook/<string:Roll_number>', methods=['GET', 'POST'])
def get_book(Roll_number):
    book_data = None
    outlook_email = None
    if request.method == 'POST':
        book_id = request.form['book_id']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM book_details WHERE bookid = %s', (book_id,))
        book_data = cursor.fetchone()
        cursor.execute('SELECT Outlook FROM student_details WHERE Roll_number = %s', (Roll_number,))
        outlook_data = cursor.fetchone()
        if outlook_data:
            outlook_email = outlook_data['Outlook']
        cursor.close()
        if book_data:
            cursor = conn.cursor()
            cursor.execute('UPDATE student_details SET bookid = %s, bookname = %s, authorname = %s, date = NOW() WHERE Roll_number = %s',
                           (book_data['bookid'], book_data['bookname'], book_data['authorname'], Roll_number))
            cursor.execute('INSERT INTO book_transactions (Roll_number, book_id, action, taken_date, submitted_date) VALUES (%s, %s, %s, NOW(), NULL)',
               (Roll_number, book_data['bookid'], 'taken'))
            conn.commit()
            cursor.close()
            final_submission_date = datetime.now() + timedelta(days=14)
            format_date=final_submission_date.strftime("%d-%m-%Y %I:%M:%S %p")
            cursor = conn.cursor()
            cursor.execute('UPDATE student_details SET final_submitted_date = %s WHERE Roll_number = %s',
                           (final_submission_date, Roll_number))
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
@app.route('/submitbook/<string:Roll_number>', methods=['POST'])
def submit_book(Roll_number):
    if request.method == 'POST':
        book_id = request.form['book_id']
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM student_details WHERE Roll_number = %s AND bookid = %s', (Roll_number, book_id))
        student_data = cursor.fetchone()
        if student_data:
            cursor.execute('SELECT * FROM book_details WHERE bookid = %s', (book_id,))
            book_data = cursor.fetchone()
            if book_data:
                cursor.execute('UPDATE student_details SET bookid = NULL, bookname = NULL, authorname = NULL, date=NULL WHERE Roll_number = %s AND bookid = %s', (Roll_number, book_id))
                cursor.execute('INSERT INTO book_transactions (Roll_number, book_id, action, taken_date, submitted_date) VALUES (%s, %s, %s, NULL, NOW())',
               (Roll_number, book_id, 'submitted'))
                conn.commit()
                cursor.close()
                outlook_email = student_data['Outlook']
                subject = "Book Submission Confirmation"
                current_date = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
                body = f"Book ID: {book_id}\nSubmission Date: {current_date}"
                send_email(outlook_email, subject, body)
                return "Book details submitted and deleted successfully."
            else:
                return "Invalid Book ID. Book not found in the book details database."
        else:
            return "Invalid Book ID for the provided Roll Number."
    return "Invalid request."
if __name__ == '__main__':
    app.run(debug=True)
