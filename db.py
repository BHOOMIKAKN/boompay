# db.py

import pymysql
import random
import smtplib
from email.mime.text import MIMEText

# Function to establish a connection

def get_bank_names():
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    cursor.execute("SELECT bank_name FROM bank2")  # Fetch bank names
    banks = [row[0] for row in cursor.fetchall()]  # Extract bank names from tuples

    cursor.close()
    connection.close()

    return banks


def bankinfo(bank_name, account_number, ifsc_code):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    cursor.execute("INSERT INTO bank2(bank_name, account_number, ifsc_code) VALUES(%s, %s, %s)", (bank_name, account_number,  ifsc_code))
    connection.commit()

    cursor.close()
    connection.close()

    return "Bank registered successfully!"


def user_bank(bank_name, passcode, phone_number):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    cursor.execute("INSERT INTO user_bank(bank_name, passcode, phone_number) VALUES(%s, %s, %s)",
                   (bank_name, passcode, phone_number))
    connection.commit()

    cursor.close()
    connection.close()

    return "USER Bank connected successfully!"


def is_phone_registered(phone_number):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM users_datas WHERE phone_number = %s", (phone_number,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    return user


import pymysql


def fetch_user_from_db(email):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor(pymysql.cursors.DictCursor)  # Return data as a dictionary
    cursor.execute("SELECT * FROM users_datas WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user  # Returns a dictionary with user details

def register(name, phone_number, email):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    cursor.execute("INSERT INTO users_datas(name, phone_number, email) VALUES(%s, %s, %s)", (name, phone_number, email))
    connection.commit()

    cursor.close()
    connection.close()

    return "User registered successfully!"


# Db Connection
connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
cursor = connection.cursor()


def is_registered(email):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users_datas WHERE email = %s", (email,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result is not None


def register_user(email):
    cursor.execute("INSERT INTO users_datas(email) VALUES(%s)", (email,))
    connection.commit()


def send_otp(email):
    otp = str(random.randint(1000, 9999))  # Generate 4-digit OTP

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "justsecret4411@gmail.com"
    EMAIL_PASSWORD = "tmob lbjy ngnz oway"

    msg = MIMEText(f"Your OTP is: {otp}")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
    server.quit()

    return otp  # Return OTP for verification


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='admin@123',
        database='payment1',
        cursorclass=pymysql.cursors.DictCursor
    )


import pymysql


def get_user_det(user_email):
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor()

    print(f"Executing query: SELECT * FROM user_bank_details WHERE email = '{user_email}'")  # Debugging
    cursor.execute("SELECT * FROM user_bank_details WHERE email = %s", (user_email,))

    result = cursor.fetchone()
    print("Query Result:", result)  # Debugging print

    cursor.close()
    connection.close()

    return result


def get_user_details():
    connection = pymysql.connect(host='localhost', user='root', password='admin@123', database='payment1')
    cursor = connection.cursor(pymysql.cursors.DictCursor)  # ✅ Use DictCursor for dictionary output

    cursor.execute("SELECT * FROM user_bank_details")
    users = cursor.fetchall()  # ✅ Fetch as list of dictionaries

    cursor.close()
    connection.close()
    return users  # ✅ Ensures it returns a list, even if empty


