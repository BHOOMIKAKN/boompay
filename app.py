from flask import Flask, redirect, render_template, request, url_for, flash, jsonify
from db21 import register, is_registered, get_user

app = Flask(__name__)
app.secret_key = "your_secret_key"


@app.route("/")
def hi():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def hello():
    if request.method == "POST":
        name = request.form["name"]
        phone_number = request.form["phone_number"]
        email = request.form["email"]

        # Ensure phone_number is stored as the password
        if is_registered(email):  # Check if email is already registered
            flash("Email already registered!", "danger")
            return redirect(url_for('hello'))

        add_new = register(name, phone_number, email)  # Store phone_number as password
        print(add_new)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('hi'))

    return render_template('register21.html')


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    if not is_registered(email):  # Check if email is registered
        flash("Email not found! Please register.", "danger")
        return redirect(url_for("hello"))

    # Fetch user details (ensure this function returns correct details)
    user = get_user(email)

    if user and user["phone_number"] == password:  # Check if password matches phone number
        return redirect(url_for('paying_page'))

    flash("Invalid email or password!", "danger")
    return redirect(url_for("hi"))


@app.route("/paying")
def paying_page():
    return render_template("paying.html")


if __name__ == "__main__":
    app.run(debug=True)
