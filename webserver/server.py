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

message = ""
@app.route('/')
def home():
    global message
    if not session.get('logged_in'):
        context = dict(warning_message = message)
        return render_template('login.html', **context)
    else:
        return another()


@app.route('/login', methods=['POST'])
def do_admin_login():
    global message
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
        message = ""
    else:
        flash('wrong password!')
        message ='wrong password or email!'
    return redirect('/')

@app.route("/create_account", methods=['POST'])
def create_account():
    return render_template('create_account.html')

@app.route("/logout", methods=['POST'])
def logout():
    session['logged_in'] = False
    return redirect('/')


@app.route('/another')
def another():
  return render_template("anotherfile.html")


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
