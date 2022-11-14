from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
from flask import Flask, request, render_template, g, redirect, Response, url_for
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool

app = Flask(__name__)
######### connect database #################
DB_USER = "jw4173"
DB_PASSWORD = "1216"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"
engine = create_engine(DATABASEURI)
######################################################

warning_message = ""
@app.route('/')
def home():
    global warning_message
    if not session.get('logged_in'):
        context = dict(warning_message = warning_message)
        return render_template('login.html', **context)
    else:
        return another()


@app.route('/login', methods=['POST'])
def do_admin_login():
    global warning_message
    username = request.form['username']
    password = request.form['password']
    print(username, password)
    
    cmd = 'SELECT * FROM Users WHERE email=(:username) AND password=(:password)'
    cursor = g.conn.execute(text(cmd), username=username, password=password)
    count = 0
    for i in cursor:
        count += 1
    
    if count == 1:
        session['logged_in'] = True
        warning_message = ""
    else:
        flash('wrong password!')
        warning_message ='wrong password or email!'
    return redirect('/')

@app.route("/create_account", methods=['POST'])
def create_account():
    return render_template('create_account.html')


@app.route("/sign_up", methods=['POST'])
def sign_up():
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']
    zipcode = request.form['zipcode']
    description = request.form['description']
    # get max id
    cmd = 'SELECT MAX(user_id) FROM Users'
    cursor = g.conn.execute(text(cmd))
    max_id = next(cursor)[0]
    print(max_id)
    # check whether email exist
    cmd = 'SELECT COUNT(*) FROM Users WHERE email=(:email)'
    cursor = g.conn.execute(text(cmd), email=email)
    count = next(cursor)[0]
    if email and username and password and zipcode and description and count==0:
        print(email, username, password, zipcode, description)
        cmd = 'INSERT INTO Users VALUES ((:max_id), (:zipcode), (:email), (:username), (:password), (:description))'
        g.conn.execute(text(cmd), max_id=max_id+1, zipcode=int(zipcode), email=email, username=username, password=password, description=description)
        session['logged_in'] = True
        return redirect('/')
    else:
        context = dict(warning_message = 'already used email or missing information')
        return render_template('create_account.html', **context)


@app.route("/logout", methods=['POST'])
def logout():
    session['logged_in'] = False
    return redirect('/')


@app.route('/add_app', methods=['POST'])
def add_app():
    return render_template("add_app.html")

@app.route('/find_app', methods=['POST'])
def find_app():
    return render_template("find_app.html")

@app.route('/find_roommate', methods=['POST'])
def find_roommate():
    return render_template("find_roommate.html")

@app.route('/message', methods=['POST'])
def message():
    return render_template("message.html")

@app.route('/basic_info', methods=['POST'])
def another():
    return render_template("home-page.html")


@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print('uh oh, problem connecting to database')
        import traceback; traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=8111)
