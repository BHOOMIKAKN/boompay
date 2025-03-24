# db.py
import pymysql


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
    cursor.execute("SELECT * FROM users_datas WHERE email = %s", (email,))
    return cursor.fetchone() is not None


def register_user(email):
    cursor.execute("INSERT INTO users_datas(email) VALUES(%s)", (email,))
    connection.commit()


def get_user(email):
    cursor.execute("SELECT name, phone_number FROM users_datas WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user:
        return {"name": user[0], "phone_number": user[1]}  # Return as dictionary
    return None
