import traceback

import pymysql
from flask import Flask, jsonify, redirect, render_template, request, url_for, session, flash
import random
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
        # Check if the request is JSON
        if request.is_json:
            data = request.get_json()
            name = data.get("name")
            phone_number = data.get("phone_number")
            email = data.get("email")
        else:
            # Default to form-data
            name = request.form.get("name")
            phone_number = request.form.get("phone_number")
            email = request.form.get("email")

        if not all([name, phone_number, email]):
            return "Missing data", 400  # Return error if any field is missing

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

    if request.method == 'GET':
        return render_template('enter_passcode.html')  # Ensure a valid response for GET requests

    if request.method == 'POST':
        payment_type = request.form.get('payment_type')
        entered_passcode = request.form.get('passcode')
        amount = request.form.get('amount')

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    # ✅ Fetch stored passcode from `user_bank_details`
                    sql_fetch_passcode = "SELECT passcode FROM user_bank_details WHERE email = %s"
                    cursor.execute(sql_fetch_passcode, (email,))
                    stored_passcode_result = cursor.fetchone()

                    if not stored_passcode_result or not stored_passcode_result["passcode"]:
                        return {"error": "Passcode not found for this email."}, 400

                    stored_passcode = stored_passcode_result["passcode"]
                    print("Stored Passcode:", stored_passcode)

                    if entered_passcode == stored_passcode:
                        print(f"Received payment_type: '{payment_type}'")

                        if payment_type == 'bank':
                            # ✅ Deduct balance for Bank Payment
                            print("✅ Entered Bank Payment block")
                            bank_name = request.form.get('bank_name')
                            recipient_name = request.form.get('recipient_name')
                            account_number = request.form.get('account_number')
                            ifsc_code = request.form.get('ifsc_code')

                            cursor.execute("SELECT balance_amnt FROM user_bank_details WHERE email = %s", (email,))
                            sender_balance_result = cursor.fetchone()
                            if sender_balance_result:
                                if isinstance(sender_balance_result, dict):  # If dict, extract correctly
                                    sender_balance = int(sender_balance_result.get('balance_amnt', 0))
                                elif isinstance(sender_balance_result, tuple):  # If tuple, extract first element
                                    sender_balance = int(sender_balance_result[0])
                                else:
                                    sender_balance = 0  # Handle unexpected cases
                            else:
                                sender_balance = 0  # Handle case where balance is missing

                            print(f"✅ Extracted Sender's Balance (Bank): {sender_balance}")
                            amount = int(amount)
                            if sender_balance >= amount:
                                cursor.execute("UPDATE user_bank_details SET balance_amnt = balance_amnt - %s WHERE email = %s",
                                               (amount, email))

                                cursor.execute(
                                    """INSERT INTO payments_bank (bank_name, recipient_name, account_number, ifsc_code, amount) 
                                       VALUES (%s, %s, %s, %s, %s)""",
                                    (bank_name, recipient_name, account_number, ifsc_code, amount)
                                )

                                details = f"Bank Payment - {bank_name}, {recipient_name}"

                                cursor.execute(
                                    """INSERT INTO transactions1 (details, amount, timestamp, status)
                                       VALUES (%s, %s, NOW(), %s)""",
                                    (details, amount, "positive")
                                )

                                connection.commit()
                                print("✅ Bank Payment successful!")
                                return redirect(url_for('confirm_page'))
                            else:
                                return "❌ Insufficient Balance for Bank Payment", 400



                        elif payment_type == 'phone_number':
                            print(email)
                            print("✅ Entered phone_number payment block")

                            name = request.form.get('name')

                            phone_number = request.form.get('phone_number')

                            print(f"Phone Payment Details: {name}, {phone_number}, {amount}")

                            # Fetch the balance safely

                            cursor.execute("SELECT balance_amnt FROM user_bank_details WHERE email = %s",
                                           (email,))
                            sender_balance_result = cursor.fetchone()

                            print(f"DEBUG: sender_balance_result = {sender_balance_result}")  # ✅ Debugging step

                            if sender_balance_result is not None and len(sender_balance_result) > 0:

                                sender_balance = int(sender_balance_result['balance_amnt'])  # ✅ Correct way for DictCursor

                                print(f"✅ Extracted Sender's Balance (Phone): {sender_balance}")

                                if sender_balance >= int(amount):

                                    # Deduct the amount

                                    cursor.execute(
                                        "UPDATE user_bank_details SET balance_amnt = balance_amnt - %s WHERE email = %s",

                                        (amount, email))
                                    connection.commit()
                                    # Insert payment details

                                    sql_insert_phone = """INSERT INTO payments_phone (name, phone_number, amount) 

                                                          VALUES (%s, %s, %s)"""

                                    cursor.execute(sql_insert_phone, (name, phone_number, amount))
                                    connection.commit()
                                    # Insert transaction record

                                    details_phone = f"Phone Payment - {name}, {phone_number}"

                                    sql_transaction_phone = """INSERT INTO transactions1 (details, amount, timestamp, status)

                                                               VALUES (%s, %s, NOW(), %s)"""

                                    cursor.execute(sql_transaction_phone, (details_phone, amount, "positive"))
                                    connection.commit()
                                    print("✅ Phone Payment Successful, Amount Deducted")

                                else:

                                    print("❌ Insufficient Balance in Phone Account")

                            else:

                                print("❌ Phone Number Not Found in Database or No Balance Record")

                        elif payment_type == 'upi_id':

                            print("✅ Entered UPI Payment block")

                            upi_id = request.form.get('upi_id')
                            print(upi_id)
                            recipient_name = request.form.get('name')
                            print(recipient_name)
                            print(f"UPI Payment Details: {recipient_name}, {upi_id}, {amount}")
                            sender_phone = session.get('phone_number')  # Get sender's phone number
                            print(sender_phone)
                            cursor.execute("SELECT upi_id FROM user_bank_details WHERE email = %s", (email,))

                            sender_upi_id = cursor.fetchone()
                            print(sender_upi_id) #okay upto here
                            if sender_upi_id:
                                if isinstance(sender_upi_id, dict):
                                    sender_upi_id = sender_upi_id.get('upi_id')  # Extract from dict
                                    print(sender_upi_id)
                                elif isinstance(sender_upi_id, tuple):
                                    sender_upi_id = sender_upi_id[0]  # Extract from tuple
                                    print(sender_upi_id)
                                else:
                                    sender_upi_id = None  # Handle unexpected cases
                                    print("None UPI ID")
                            print(f"✅ Sender's UPI ID: {sender_upi_id}")
                            cursor.execute("SELECT balance_amnt FROM bank3 WHERE upi_id = %s", (sender_upi_id,))
                            sender_balance_result = cursor.fetchone()

                            if sender_balance_result:
                                if isinstance(sender_balance_result, dict):  # ✅ If dict, extract correctly
                                    sender_balance = int(sender_balance_result.get('balance_amnt', 0))
                                elif isinstance(sender_balance_result, tuple):  # ✅ If tuple, extract first element
                                    sender_balance = int(sender_balance_result[0])
                                else:
                                    sender_balance = 0  # Handle unexpected cases
                            else:
                                sender_balance = 0  # Handle case where balance is missing

                            print(f"✅ Extracted Sender's Balance: {sender_balance}")
                            amount= int(amount)
                            if sender_balance >= amount:  # ✅ Corrected check
                                print("✅ Sufficient balance, proceeding with transaction...") # Convert to integer
                            else:
                                sender_balance = None  # Handle cases where balance is not found

                            print(f"✅ Extracted Sender's Balance: {sender_balance}")

                            if sender_balance is not None and sender_balance >= int(
                                    amount):  # Ensure amount is also an integer
                                try:
                                    # Deduct amount from sender's balance
                                    cursor.execute(
                                        "UPDATE bank3 SET balance_amnt = balance_amnt - %s WHERE upi_id = %s",
                                        (amount, sender_upi_id)
                                    )

                                    # Insert payment record
                                    sql_insert_upi = """INSERT INTO payments_upi 
                                                        (upi_id, recipient_name, amount, passcode) 
                                                        VALUES (%s, %s, %s, %s)"""
                                    cursor.execute(sql_insert_upi, (upi_id, recipient_name, amount, stored_passcode))

                                    # Insert transaction record
                                    details_upi = f"UPI Payment - {recipient_name}, {upi_id}"
                                    sql_transaction_phone = """INSERT INTO transactions1 (details, amount, timestamp, status)
                                                               VALUES (%s, %s, NOW(), %s)"""
                                    cursor.execute(sql_transaction_phone, (details_upi, amount, "positive"))

                                    # Commit transaction
                                    connection.commit()
                                    print("✅ Payment successful and balance updated!")
                                    print("✅ Transaction committed")

                                    return redirect(url_for('confirm_page'))

                                except Exception as e:
                                    connection.rollback()  # Rollback in case of error
                                    print(f"❌ Transaction failed! Error: {e}")
                                    return "Transaction Failed", 500

                            else:
                                print("❌ Insufficient balance! Transaction failed.")
                                return "Insufficient Balance", 400

                    return redirect(url_for('confirm_page'))

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
        # Handle JSON and form-data correctly
        if request.is_json:
            data = request.get_json()
            bank_name = data.get('bank_name')
            account_number = data.get('account_number')
            ifsc_code = data.get('ifsc_code')
            upi_id = data.get('upi_id')
            #balance_amnt = data.get('balance_amnt')
            passcode = data.get('passcode')
            phone_number = data.get('phone_number')
        else:
            bank_name = request.form.get('bank_name')
            account_number = request.form.get('account_number')
            ifsc_code = request.form.get('ifsc_code')
            upi_id = request.form.get('upi_id')
            #balance_amnt = request.form.get('balance_amnt')
            passcode = request.form.get('passcode')
            phone_number = request.form.get('phone_number')

        # Ensure all fields are provided
        if not all([bank_name, account_number, ifsc_code, upi_id, passcode, phone_number]):
            return jsonify({"error": "All fields are required"}), 400

        try:
            # Database connection
            connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
            cursor = connection.cursor()

            # Insert into the database
            cursor.execute("""
                INSERT INTO bank3 (bank_name, account_number, ifsc_code, upi_id, passcode, phone_number) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (bank_name, account_number, ifsc_code, upi_id, passcode, phone_number))
            connection.commit()

        except Exception as e:
            return f"Database Error: {str(e)}", 500  # Returns string error

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('index2'))  # Redirect after successful form submission

    return render_template("bankinfo.html")


def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))


@app.route('/upi_payment', methods=['POST'])
def upi_payment():
    try:
        data = request.json
        sender_upi = data.get('upi_id')  # Sender's UPI ID from another application
        amount = data.get('amount')

        if not sender_upi or not amount:
            return jsonify({"error": "Sender UPI ID and amount are required"}), 400

        # Fetch sender details from users_bank_details view
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT account_holder, passcode FROM users_bank_details WHERE upi_id = %s", (sender_upi,))
                sender_data = cursor.fetchone()

        if not sender_data:
            return jsonify({"error": "Sender details not found"}), 404

        sender_name, sender_passcode = sender_data

        print(f"✅ Sender Found: {sender_name} ({sender_upi}) | Amount: ₹{amount}")

        # Store transaction in database
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                sql_insert_upi_payment = """INSERT INTO payments_upi (upi_id, account_holder, amount, passcode)
                                            VALUES (%s, %s, %s, %s)"""
                cursor.execute(sql_insert_upi_payment, (sender_upi, sender_name, amount, sender_passcode))
                connection.commit()

        print(f"✅ Payment of ₹{amount} from {sender_upi} processed successfully.")

        return jsonify({
            "message": "Payment successful",
            "upi_id": sender_upi,
            "account_holder": sender_name,
            "amount": amount
        })

    except Exception as e:
        print("Full Error Traceback:\n", traceback.format_exc())
        return jsonify({"error": "Internal Server Error"}), 500


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


@app.route("/paymentupi")
def paymentupi():
    return redirect(url_for('paying2'))


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


@app.route("/paying2")
def paying2():
    return render_template("paying2.html")


@app.route("/users", methods=["GET"])
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

