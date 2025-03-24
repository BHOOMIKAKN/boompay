import traceback

import pymysql
from flask import Flask, jsonify, redirect, render_template, request, url_for, session, flash

import db
from db import is_registered, register, send_otp, bankinfo, get_bank_names, is_phone_registered

app = Flask(__name__)
app.secret_key = "your_secret_key"

otp_store = {}


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='admin@123',
        database='payment1',
        cursorclass=pymysql.cursors.DictCursor
    )


@app.route("/")
def hi():
    return render_template("index.html")


@app.route('/add_user', methods=['POST'])
def add_user():
    email = request.form.get('email')

    if is_registered(email):
        otp = send_otp(email)
        otp_store[email] = otp  # Store OTP in session
        session["otp_email"] = email
        return render_template('verify.html', email=email)  # Redirect to OTP verification page
    else:
        return redirect('/register')


@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    email = session.get("otp_email")  # 🔹 Retrieve email from session
    if not email:
        return "No email found in session. Please generate OTP first.", 400

    entered_otp = request.form.get("otp")
    if otp_store.get(email) == entered_otp:
        return redirect('/home')
    else:
        return "Invalid OTP"


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/transaction_history')
def transaction_history():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT details, amount, timestamp, status FROM transactions1 ORDER BY timestamp DESC")
            transactions = cursor.fetchall()
    finally:
        connection.close()

    return render_template('transaction.html', transactions=transactions)


@app.route("/register", methods=["GET", "POST"])
def hello():
    if request.method == "POST":
        name = request.form["name"]
        phone_number = request.form["phone_number"]
        email = request.form["email"]
        add_new = register(name, phone_number, email)
        return redirect(url_for('hi'))
    return render_template('register.html')


@app.route("/index2")
def index2():
    return render_template("index2.html")  # Serve index2.html after OTP verification


@app.route("/bank")
def bank():
    return redirect(url_for('bankinfo1'))  # Redirect to bankinfo.html


@app.route("/user_bank", methods=["GET", "POST"])
def user_bank():
    return redirect(url_for('users'))


from flask import session  # Ensure session is imported


@app.route('/submit_passcode', methods=['POST'])
def submit_passcode():
    email = session.get("otp_email")  # Fetch email from session
    print("Session Email:", email)  # Debugging line

    if not email:
        return "No email found in session. Please generate OTP first.", 400

    print("Full Form Data:", request.form.to_dict(flat=False))  # Debugging line

    entered_passcode = request.form.get('passcode', '').strip()
    phone_number = request.form.getlist('phone_number')[0].strip() if request.form.getlist('phone_number') else ''  # FIXED HERE
    name = request.form.getlist('name')[0].strip() if request.form.getlist('name') else ''
    amount = request.form.getlist('amount')[0].strip() if request.form.getlist('amount') else ''

    print(f"Received Data - Phone: {phone_number}, Name: {name}, Amount: {amount}")  # Debugging line

    if not entered_passcode:
        return "Passcode is required.", 400
    if not phone_number or not name or not amount:
        return "All payment details are required.", 400

    try:
        amount = float(amount)  # Convert to float to ensure valid number
    except ValueError:
        return "Invalid amount format.", 400

    try:
        with get_db_connection() as connection:
            print("Database Connection Established")  # Debugging line
            with connection.cursor() as cursor:
                # Fetch stored passcode
                sql_fetch = "SELECT passcode FROM user_bank_details WHERE email = %s"
                cursor.execute(sql_fetch, (email,))
                stored_passcode = cursor.fetchone()

                print("Stored Passcode:", stored_passcode)  # Debugging line

                if not stored_passcode or stored_passcode['passcode'] is None:
                    return "Email not found in records! Please check again.", 404

                # Compare entered passcode with stored passcode
                if entered_passcode == stored_passcode['passcode']:
                    # Insert data into payments_phone
                    sql_insert = """INSERT INTO payments_phone (phone_number, name, amount) 
                                    VALUES (%s, %s, %s)"""
                    cursor.execute(sql_insert, (phone_number, name, amount))
                    connection.commit()

                    print("Payment details added successfully!")  # Debugging line
                    return redirect(url_for('index2'))  # Redirect on success
                else:
                    return "Incorrect Passcode. Please try again.", 401

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("Full Error Traceback:\n", error_details)  # Debugging line
        return f"Database Error: {str(e)}", 500


@app.route('/enter_passcode', methods=['POST', 'GET'])
def enter_passcode():
    email = session.get("otp_email")
    print("Session Email:", email)

    if not email:
        return "No email found in session. Please generate OTP first.", 400

    if request.method == 'POST':
        payment_type = request.form.get('payment_type')
        entered_passcode = request.form.get('passcode')
        amount = request.form.get('amount')

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    # Fetch stored passcode
                    sql_fetch = "SELECT passcode FROM user_bank_details WHERE email = %s"
                    cursor.execute(sql_fetch, (email,))
                    stored_passcode = cursor.fetchone()

                    if not stored_passcode or not stored_passcode["passcode"]:
                        return "Email not found in records! Please check again.", 404

                    stored_passcode = stored_passcode["passcode"]
                    print("Stored Passcode:", stored_passcode)

                    if entered_passcode == stored_passcode:
                        print(f"Received payment_type: '{payment_type}'")

                        if payment_type == 'bank':
                            bank_name = request.form.get('bank_name')
                            recipient_name = request.form.get('recipient_name')
                            account_number = request.form.get('account_number')
                            ifsc_code = request.form.get('ifsc_code')

                            print(f"Bank Payment Details: {bank_name}, {recipient_name}, {account_number}, {ifsc_code}, {amount}")

                            sql_insert_bank = """INSERT INTO payments_bank (bank_name, recipient_name, account_number, ifsc_code, amount) 
                                                 VALUES (%s, %s, %s, %s, %s)"""
                            cursor.execute(sql_insert_bank, (bank_name, recipient_name, account_number, ifsc_code, amount))

                            details_bank = f"Bank Payment - {bank_name}, {recipient_name}"
                            sql_transaction_bank = """INSERT INTO transactions1 (details, amount, timestamp, status)
                                                      VALUES (%s, %s, NOW(), %s)"""
                            cursor.execute(sql_transaction_bank, (details_bank, amount, "positive"))

                        elif payment_type == 'phone_number':
                            print("✅ Entered phone_number payment block")
                            name = request.form.get('name')

                            phone_number = request.form.get('phone_number')

                            print(f"Phone Payment Details: {name}, {phone_number}, {amount}")

                            sql_insert_phone = """INSERT INTO payments_phone (name, phone_number, amount) 

                                                      VALUES (%s, %s, %s)"""

                            cursor.execute(sql_insert_phone, (name, phone_number, amount))

                            details_phone = f"Phone Payment - {name}, {phone_number}"

                            sql_transaction_phone = """INSERT INTO transactions1 (details, amount, timestamp, status)

                                                           VALUES (%s, %s, NOW(), %s)"""

                            cursor.execute(sql_transaction_phone, (details_phone, amount, "positive"))

                        connection.commit()  # Commit changes for both cases

                        print("Transaction committed ✅")

                        return redirect(url_for('index2'))
        except Exception as e:
            print("Full Error Traceback:\n", traceback.format_exc())
            return f"Database Error: {str(e)}", 500


@app.route('/passcode', methods=['GET', 'POST'])  # Allow both GET and POST
def passcode():
    if request.method == 'POST':
        otp = ''.join([
            request.form.get('otp1', ''),
            request.form.get('otp2', ''),
            request.form.get('otp3', ''),
            request.form.get('otp4', ''),
            request.form.get('otp5', ''),
            request.form.get('otp6', ''),
        ])
        return f"Received OTP: {otp}"  # Replace this with actual verification logic

    return render_template('payverify.html')  # Make sure you have this file


@app.route('/user_details')
def user_details():
    users = db.get_user_details() or []
    return render_template('user_details.html', users=users)


@app.route('/verify_passcode', methods=['POST', 'GET'])
def verify_passcode():
    if 'payment_details' not in session:
        flash("Session expired. Please enter passcode again.", "error")
        return redirect(url_for('enter_passcode'))

    entered_passcode = request.form.get('passcode')  # Get full passcode
    payment_details = session['payment_details']
    phone_number = payment_details.get('phone_number')

    if not phone_number:
        flash("Phone number not found in session.", "error")
        return redirect(url_for('enter_passcode'))

    try:
        # Connect to database and fetch correct passcode for the provided phone number
        with db.get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT passcode FROM users_bank_details WHERE phone_number = %s", (phone_number,))
                result = cursor.fetchone()

                if result:
                    stored_passcode = str(result['passcode'])  # Convert to string for accurate comparison
                    if entered_passcode == stored_passcode:
                        flash("Passcode verified successfully!", "success")
                        return redirect(url_for('confirm_page'))  # Redirect to confirmation page
                    else:
                        flash("Incorrect passcode. Try again.", "error")
                else:
                    flash("No matching record found for this phone number.", "error")
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")

    return render_template('payverify.html', phone_number=phone_number)  # Stay on verification page if incorrect


@app.route('/confirm')
def confirm_page():
    return render_template("confirm.html")


@app.route('/bankinfo', methods=['GET', 'POST'])
def bankinfo1():
    if request.method == 'POST':
        bank_name = request.form['bank_name']
        account_number = request.form['account_number']
        ifsc_code = request.form['ifsc_code']
        passcode = request.form['passcode']
        phone_number = request.form['phone_number']  # Fetch phone number from form

        try:
            connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
            cursor = connection.cursor()

            # Insert into the database including phone_number
            cursor.execute("""
                INSERT INTO bank3 (bank_name, account_number, ifsc_code, passcode, phone_number) 
                VALUES (%s, %s, %s, %s, %s)
            """, (bank_name, account_number, ifsc_code, passcode, phone_number))
            connection.commit()

        except Exception as e:
            return f"Database Error: {str(e)}", 500

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('index2'))  # Redirect after successful submission

    return render_template("bankinfo.html")  # Ensure this template includes a phone number input field


@app.route('/user_bank')
def user_bank_page():
    if 'phone_number' in session:  # Get phone number from session
        phone_number = session['phone_number']
    else:
        phone_number = ""

    banks = get_bank_names()  # Fetch bank names from DB
    return render_template("user_bank.html", banks=banks, phone_number=phone_number)


@app.route("/payment")
def payment():
    return redirect(url_for('paying1'))


@app.route("/transaction")
def transaction():
    return redirect(url_for('paying'))  # Redirect to paying.html


@app.route("/paying")
def paying():
    return render_template("paying.html")


@app.route("/transaction2")
def transaction2():
    return render_template("transaction.html")


@app.route("/paying1")
def paying1():
    return render_template("paying1.html")


@app.route("/users", methods=["GET", "POST"])
def users():
    user_email = session.get("otp_email")
    if not user_email:
        return "No email found in session. Please generate OTP first.", 400

    user_email = request.args.get("email", user_email)
    users = db.get_user_det(user_email)

    if users is None:
        return "No user details found.", 404

    print("User details passed to template:", users)  # Debugging output
    return render_template("user_details.html", users=users)


if __name__ == "__main__":
    app.run(debug=True)

