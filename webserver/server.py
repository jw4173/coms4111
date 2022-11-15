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
        userid = i['user_id']
        print(userid)
        count += 1
    
    if count == 1:
        session['logged_in'] = True
        session['userid'] = userid
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
        session['userid'] = max_id+1
        return redirect('/')
    else:
        context = dict(warning_message = 'already used email or missing information')
        return render_template('create_account.html', **context)


@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session['logged_in'] = False
    session['userid'] = 0
    return redirect('/')


@app.route('/add_app', methods=['POST', 'GET'])
def add_app():
    if not session.get('logged_in'):
        return redirect('/')
    if session.get('userid'):
        context = dict(userid=session.get('userid'))
    return render_template("add_app.html", **context)


@app.route('/confirm', methods=['POST'])
def confirm_add_app():
   global warning_message1
   zipcode = request.form['zipcode']
   cmd = 'SELECT * FROM Location WHERE zip_code=(:zipcode)'
   cursor = g.conn.execute(text(cmd), zipcode=zipcode)
   count = 0
   for j in cursor:
       count += 1
   if zipcode and count == 0:
       country = request.form['country']
       state = request.form['state']
       city = request.form['city']
       apartment = request.form['apartment_name']
       if country and state and city and apartment:
           cmd = 'INSERT INTO Location VALUES ((:zip_code), (:country), (:state), (:city))'
           g.conn.execute(text(cmd), zip_code=int(zipcode), country=country, state=state, city=city)
           cmd = 'SELECT MAX(apartment_id) FROM Apartment_in'
           cursor = g.conn.execute(text(cmd))
           max_id = next(cursor)[0]
           cmd = 'INSERT INTO Apartment_in VALUES ((:max_id), (:zip_code), (:name))'
           g.conn.execute(text(cmd), max_id=max_id + 1, zip_code=int(zipcode), name=apartment)
           return render_template("add_app.html")
   else:
       apartment = request.form['apartment_name']
       cmd = 'SELECT * FROM Apartment_in WHERE name=(:apartment) AND zip_code=(:zip_code)'
       cursor = g.conn.execute(text(cmd), apartment=apartment, zip_code=zipcode)
       count = 0
       for i in cursor:
           count += 1
       if apartment and count == 1:
           context = dict(warning_message1='apartment already exists')
           return render_template("add_app.html", **context)
       else:
           cmd = 'SELECT MAX(apartment_id) FROM Apartment_in'
           cursor = g.conn.execute(text(cmd))
           max_id = next(cursor)[0]
           cmd = 'INSERT INTO Apartment_in VALUES ((:max_id), (:zip_code), (:name))'
           g.conn.execute(text(cmd), max_id=max_id + 1, zip_code=int(zipcode), name=apartment)
           return render_template("add_app.html")


@app.route('/find_app', methods=['POST', 'GET'])
def find_app():
    if not session.get('logged_in'):
        return redirect('/')
    cmd = 'SELECT * FROM Location'
    cursor = g.conn.execute(text(cmd))
    array = []
    for i in cursor:
        zipcode = str(i['zip_code'])
        country = i['country']
        state = i['state']
        city = i['city']
        array.append(country + ", " + state + ", " + city + ", " + zipcode)
    array.sort()
    cursor.close()
    
    array2 = []
    if session.get('apt_zipcode'):
        zipcode_tmp = session.get('apt_zipcode')
        cmd = 'SELECT * FROM Apartment_in WHERE zip_code=(:zipcode)'
        cursor = g.conn.execute(text(cmd), zipcode=zipcode_tmp)
        for i in cursor:
            apartment_id = str(i['apartment_id'])
            zip_code = str(i['zip_code'])
            name = i['name']
            array2.append(apartment_id + ", " + zip_code + ", " + name)
        array2.sort()
        cursor.close()
    if session.get('userid'):
        context = dict(data = array, data2 = array2, userid=session.get('userid'))
    else:
        context = dict(data = array, data2 = array2)
    print(array)
    return render_template("find_app.html", **context)


@app.route('/find_app_zipcode', methods=['POST', 'GET'])
def find_app_zipcode():
    if request.form['zipcode']:
        session['apt_zipcode'] = request.form['zipcode']
    return redirect('/find_app')


@app.route('/interest_app', methods=['POST', 'GET'])
def interest_app():
    if request.form['apartment_id'] and session.get('userid') and session.get('apt_zipcode'):
        cmd = 'INSERT INTO interest VALUES ((:user_id), (:apartment_id));'
        g.conn.execute(text(cmd), user_id=session.get('userid'), apartment_id = request.form['apartment_id'])
    return redirect('/find_app')


@app.route('/find_roommate', methods=['POST', 'GET'])
def find_roommate():
    if not session.get('logged_in'):
        return redirect('/')
    userid = session.get('userid')
    # show apartment
    cmd = 'SELECT * FROM interest WHERE user_id=(:user_id)'
    cursor = g.conn.execute(text(cmd), user_id=userid)
    array = []
    for i in cursor:
        array.append(i['apartment_id'])
    cursor.close()
    array.sort()
    name = []
    for i in array:
        cmd = 'SELECT name FROM Apartment_in WHERE apartment_id=(:apartment_id)'
        cursor = g.conn.execute(text(cmd), apartment_id=i)
        name.append(str(i) + ": " + next(cursor)[0])
        cursor.close()
    
    # show user
    array2 = []
    name2 = []
    if session.get('apartment_id_user'):
        cmd = 'SELECT * FROM interest WHERE apartment_id=(:apartment_id)'
        cursor = g.conn.execute(text(cmd), apartment_id=session.get('apartment_id_user'))
        for i in cursor:
            if i['user_id'] != userid:
                array2.append(i['user_id'])
        cursor.close()
        array2.sort()
        
        for i in array2:
            cmd = 'SELECT * FROM Users WHERE user_id=(:user_id)'
            cursor = g.conn.execute(text(cmd), user_id=i)
            for i in cursor:
                name2.append(str(i['user_id']) + " " + i['email'] + ": " + i['personal_info'])
    if session.get('apartment_id_user'):
        context = dict(data = name, data2 = name2)
    else:
        context = dict(data = name)
    if session.get('userid'):
        context['userid']=session.get('userid') 
    return render_template("find_roommate.html", **context)


@app.route('/show_user', methods=['POST', 'GET'])
def show_user():
    if request.form['apartment_id']:
        session['apartment_id_user'] = request.form['apartment_id']
    return redirect('/find_roommate')


@app.route('/send_message_user', methods=['POST', 'GET'])
def send_message_user():
    if request.form['message'] and session.get('userid') and request.form['user_id']:
        # find max message id
        cmd = 'SELECT MAX(message_id) FROM Message_Send_Receive'
        cursor = g.conn.execute(text(cmd))
        max_message_id = next(cursor)[0]+1
        cursor.close()
        cmd = 'INSERT INTO Message_Send_Receive VALUES ((:message_id), (:user_id), (:to_id), (:context));'
        g.conn.execute(text(cmd), message_id=max_message_id, user_id = session.get('userid'), to_id=request.form['user_id'], context=request.form['message'])
    return redirect('/find_roommate')


@app.route('/post_comment', methods=['POST', 'GET'])
def post_comment():
    if not session.get('logged_in'):
        return redirect('/')
    userid = session.get('userid')
    # show apartment
    cmd = 'SELECT * FROM interest WHERE user_id=(:user_id)'
    cursor = g.conn.execute(text(cmd), user_id=userid)
    array = []
    for i in cursor:
        array.append(i['apartment_id'])
    cursor.close()
    array.sort()
    name = []
    for i in array:
        cmd = 'SELECT name FROM Apartment_in WHERE apartment_id=(:apartment_id)'
        cursor = g.conn.execute(text(cmd), apartment_id=i)
        name.append(str(i) + ": " + next(cursor)[0])
        cursor.close()
    # show post
    array2 = []
    name2 = []
    if session.get('apartment_id_post'):
        cmd = 'SELECT * FROM Post_u_a WHERE apartment_id=(:apartment_id)'
        cursor = g.conn.execute(text(cmd), apartment_id=session.get('apartment_id_post'))
        for i in cursor:
            array2.append((i['post_id'], i['user_id'], i['context']))
        cursor.close()
        array2.sort(key=lambda a: a[0])
        
        for i in array2:
            name2.append(str(i[0]) + ". " + str(i[1]) + ": " + i[2])
            
    # show comment
    array3 = []
    name3 = []
    if session.get('apartment_id_post') and session.get('post_id_post'):
        cmd = 'SELECT * FROM Comment_u_p WHERE apartment_id_post=(:apartment_id_post) AND post_id=(:post_id)'
        cursor = g.conn.execute(text(cmd), apartment_id_post=session.get('apartment_id_post'), post_id=session.get('post_id_post'))
        for i in cursor:
            array3.append((i['comment_id'], i['user_id'], i['description']))
        cursor.close()
        array3.sort(key=lambda a: a[0])
        
        for i in array3:
            name3.append(str(i[0]) + ". " + str(i[1]) + ": " + i[2])
     
    if session.get('apartment_id_post') and session.get('post_id_post'):
        context = dict(data = name, data2 = name2, data3 = name3)        
    elif session.get('apartment_id_post'):
        context = dict(data = name, data2 = name2)
    else:
        context = dict(data = name)
    if session.get('userid'):
        context['userid']=session.get('userid') 
    return render_template("post_comment.html", **context)


@app.route('/send_post', methods=['POST', 'GET'])
def send_post():
    if request.form['message'] and session.get('userid') and session.get('apartment_id_post'):
        # find max message id
        cmd = 'SELECT MAX(post_id) FROM Post_u_a'
        cursor = g.conn.execute(text(cmd))
        max_message_id = next(cursor)[0]+1
        cursor.close()
        cmd = 'INSERT INTO Post_u_a VALUES ((:post_id), (:context), (:user_id), (:apartment_id));'
        g.conn.execute(text(cmd), post_id=max_message_id, context = request.form['message'], user_id=session.get('userid'), apartment_id=session.get('apartment_id_post'))
    return redirect('/post_comment')


@app.route('/send_comment', methods=['POST', 'GET'])
def send_comment():
    if request.form['message'] and session.get('userid') and session.get('apartment_id_post') and session.get('post_id_post'):
        # find max message id
        cmd = 'SELECT MAX(comment_id) FROM Comment_u_p'
        cursor = g.conn.execute(text(cmd))
        max_message_id = next(cursor)[0]+1
        cursor.close()
        
        # get user_id
        cmd = 'SELECT user_id FROM Post_u_a WHERE post_id=(:post_id)'
        cursor = g.conn.execute(text(cmd), post_id=session.get('post_id_post'))
        user_id_post = next(cursor)[0]
        cursor.close()
        
        cmd = 'INSERT INTO Comment_u_p VALUES ((:comment_id), (:description), (:user_id), (:post_id), (:user_id_post), (:apartment_id_post));'
        g.conn.execute(text(cmd), comment_id=max_message_id, description = request.form['message'], user_id=session.get('userid'), post_id=session.get('post_id_post'), user_id_post=user_id_post, apartment_id_post=session.get('apartment_id_post'))
    return redirect('/post_comment')


@app.route('/show_post', methods=['POST', 'GET'])
def show_post():
    if request.form['apartment_id']:
        session['post_id_post'] = 0
        session['apartment_id_post'] = request.form['apartment_id']
    return redirect('/post_comment')


@app.route('/show_comment', methods=['POST', 'GET'])
def show_comment():
    if request.form['post_id'] and session.get('apartment_id_post'):
        session['post_id_post'] = request.form['post_id']
    return redirect('/post_comment')


@app.route('/message', methods=['POST', 'GET'])
def message():
    if not session.get('logged_in'):
        return redirect('/')
    array = set()
    if session.get('userid'):
        cmd = 'SELECT DISTINCT to_id FROM Message_Send_Receive WHERE user_id=(:user_id)'
        cursor = g.conn.execute(text(cmd), user_id=session.get('userid'))
        for i in cursor:
            array.add(i['to_id'])
        cursor.close()
        
        cmd = 'SELECT DISTINCT user_id FROM Message_Send_Receive WHERE to_id=(:to_id)'
        cursor = g.conn.execute(text(cmd), to_id = session.get('userid'))
        for i in cursor:
            array.add(i['user_id'])
        cursor.close()
    array = list(array)
    array.sort()
    # add username according to userid
    name = []
    for i in array:
        cmd = 'SELECT email FROM Users WHERE user_id=(:user_id)'
        cursor = g.conn.execute(text(cmd), user_id = i)
        for j in cursor:
            name.append(str(i) + ", " + j['email'])
        cursor.close()
    
    # show message
    array2 = []
    name2 = []
    if session.get('user_id_message'):
        other_id = session.get('user_id_message')
        cmd = 'SELECT * FROM Message_Send_Receive WHERE user_id=(:user_id) AND to_id=(:to_id)'
        cursor = g.conn.execute(text(cmd), user_id=session.get('userid'), to_id=other_id)
        for i in cursor:
            array2.append((i['message_id'], i['user_id'], i['context']))
        cursor.close()
        
        cmd = 'SELECT * FROM Message_Send_Receive WHERE user_id=(:user_id) AND to_id=(:to_id)'
        cursor = g.conn.execute(text(cmd), user_id=other_id, to_id=session.get('userid'))
        for i in cursor:
            array2.append((i['message_id'], i['user_id'], i['context']))
        cursor.close()
        array2.sort(key=lambda a: a[0])
        
        for i in array2:
            name2.append(str(i[1]) + ": " + i[2])
        
    if session.get('userid'):
        context = dict(data = name, data2 = name2, userid=session.get('userid'))
    else:
        context = dict(data = name, data2 = name2)
        
    return render_template("message.html", **context)


@app.route('/show_message', methods=['POST', 'GET'])
def show_message():
    if request.form['user_id']:
        session['user_id_message'] = request.form['user_id']
    return redirect('/message')


@app.route('/send_message', methods=['POST', 'GET'])
def send_message():
    if request.form['message'] and session.get('userid') and session.get('user_id_message'):
        # find max message id
        cmd = 'SELECT MAX(message_id) FROM Message_Send_Receive'
        cursor = g.conn.execute(text(cmd))
        max_message_id = next(cursor)[0]+1
        cursor.close()
        cmd = 'INSERT INTO Message_Send_Receive VALUES ((:message_id), (:user_id), (:to_id), (:context));'
        g.conn.execute(text(cmd), message_id=max_message_id, user_id = session.get('userid'), to_id=session.get('user_id_message'), context=request.form['message'])
    return redirect('/message')

@app.route('/basic_info', methods=['POST', 'GET'])
def another():
    if not session.get('logged_in'):
        return redirect('/')
    userid = 0
    if session.get('userid'):
        userid = session.get('userid')
    cmd = 'SELECT * FROM Users WHERE user_id=(:userid)'
    cursor = g.conn.execute(text(cmd), userid=userid)
    
    element = next(cursor)
    zip_code = element[1]
    email = element[2]
    username = element[3]
    password = element[4]
    description = element[5]
    print(zip_code, email, username, password, description)
    context = dict(userid = userid, zip_code = zip_code, email = email, username=username, password=password, description=description)

    return render_template("home-page.html", **context)


@app.route('/update_info', methods=['POST'])
def update_info():
    username = request.form['username']
    password = request.form['password']
    zipcode = request.form['zipcode']
    description = request.form['description']
    userid = session.get('userid')
    if username:
        cmd = 'UPDATE Users SET username=(:username) WHERE user_id=(:userid)'
        g.conn.execute(text(cmd), username=username, userid=userid)
    if password:
        cmd = 'UPDATE Users SET password=(:password) WHERE user_id=(:userid)'
        g.conn.execute(text(cmd), password=password, userid=userid)
    if zipcode:
        cmd = 'UPDATE Users SET zip_code=(:zip_code) WHERE user_id=(:userid)'
        g.conn.execute(text(cmd), zip_code=zipcode, userid=userid)
    if description:
        cmd = 'UPDATE Users SET personal_info=(:description) WHERE user_id=(:userid)'
        g.conn.execute(text(cmd), description=description, userid=userid)
    print(userid, username, password, zipcode, description)
    return redirect('/basic_info')


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
