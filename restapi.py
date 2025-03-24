from flask import Flask, jsonify, request
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin@123'
app.config['MYSQL_DB'] = 'payment1'

mysql = MySQL(app)


@app.route('/')
def hello():
    return 'Hello, Bhoomi'


@app.route('/readall', methods=['GET'])
def get_data():
    cur = mysql.connection.cursor()
    cur.execute('''select * from users_datas''')
    data = cur.fetchall()
    cur.close()
    print(data)
    return jsonify(data)


@app.route('/readall/<int:id>', methods=['GET'])
def get_one_data(id):
    cur = mysql.connection.cursor()
    cur.execute('''select * from users_datas where id= %s''', (id,))
    data = cur.fetchall()
    cur.close()
    print(data)
    return jsonify(data)


@app.route('/dlt_user/<int:id>', methods=['DELETE'])
def get_dlt_data(id):
    cur = mysql.connection.cursor()
    cur.execute('''DELETE FROM users_datas WHERE id = %s''', (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'User deleted successfully'})


@app.route('/update_user/<int:id>', methods=['PUT'])
def update_user(id):
    cur = mysql.connection.cursor()
    data = request.json
    cur.execute('''UPDATE users_datas SET name = %s, phone_number = %s, email = %s WHERE id = %s''',
                (data['name'], data['phone_number'], data['email'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'User updated successfully!'})


@app.route('/add_user', methods=['POST'])
def add_user():
    cur = mysql.connection.cursor()
    name = request.json['name']
    phone_number = request.json['phone_number']
    email = request.json['email']
    cur.execute('''insert into users_datas (name, phone_number, email) values (%s, %s, %s)''',
                (name, phone_number, email))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'User inserted successfully!!'})


if __name__ == '__main__':
    app.run(debug=True)
