######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
from datetime import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'hello'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Wjddnwls2002!'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''
#used to login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		
		return '''
			<br>
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
#register new user 
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		gender=request.form.get('gender')
		password=request.form.get('password')
		dob=request.form.get('dob')
		hometown=request.form.get('hometown')
		fname=request.form.get('fname')
		lname=request.form.get('lname')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, gender, password, dob, hometown, fname, lname) VALUES ('{0}', '{1}', \
		       '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, gender, password, dob, hometown, fname, lname)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=fname, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid, album_id):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = %s AND album_id = %s", (uid, album_id))
    return cursor.fetchall()

def getUsersAlbums(uid): 
    cursor = conn.cursor() 
    cursor.execute("SELECT Name, album_id, date_of_creation FROM Albums WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUsersFriends(uid): 
	cursor = conn.cursor() 
	cursor.execute("SELECT UID2 FROM Friendship WHERE UID1 = '{0}'".format(uid))
	results = cursor.fetchall() 
	return [row[0] for row in results]

def getUsersName(uid): 
    cursor = conn.cursor() 
    cursor.execute("SELECT fname, lname FROM Users WHERE user_id = '{0}'".format(uid))
    name = cursor.fetchone()
    return name[0], name[1]

def getPictureLikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id = '{0}'".format(photo_id)) 
	return cursor.fetchone()[0]

def getWhoLiked(photo_id): 
	cursor = conn.cursor() 
	cursor.execute("SELECT user_id FROM Likes WHERE picture_id = '{0}'".format(photo_id))
	results = cursor.fetchall() 
	return [row[0] for row in results]

def getAlbumName(album_id): 
	cursor = conn.cursor() 
	cursor.execute("SELECT Name FROM Albums WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchone()[0]

def getPhotoId(album_id): 
	cursor = conn.cursor() 
	cursor.execute("SELECT picture_id FROM Pictures WHERE album_id = '{0}'".format(album_id))
	results = cursor.fetchall()
	return [row[0] for row in results]

def tagFormat(tags): 
	tags_list = [tag.strip().lower() for tag in tags.split(',')]
	return tags_list

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#uploading a photo
@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		caption = request.form.get('caption')
		album_id = request.form.get('album_id')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		photo_data = imgfile.read()
		#DO TAGS!!!!
		tags = request.form.get('tags')
		tags_list = tagFormat(tags)
		for tag in tags_list: 
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Tags (tag_name) VALUES (%s)''', (tag,))
			conn.commit()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (user_id, caption, imgdata, album_id) VALUES (%s, %s, %s, %s)''', (uid, caption, photo_data, album_id))
		conn.commit()
		return redirect(url_for('albumphoto', album_id=album_id))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		albums = getUsersAlbums(uid)
		return render_template('upload.html', albums=albums)

#putting into album/viewing album
@app.route('/album', methods=['GET', 'POST'])
@flask_login.login_required
def album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('album.html', albums=getUsersAlbums(uid))

@app.route('/albumphoto', methods=['GET', 'POST'])
def albumphoto():
    if request.method == 'POST': 
        album_id = request.args.get('album_id')
        photo_id = request.form.get('photo_id')
        uid = getUserIdFromEmail(flask_login.current_user.id)
        # Check if user has liked this photo before
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM Likes WHERE user_id = %s AND picture_id = %s''', (uid, photo_id))
        if cursor.fetchone() is not None:
            return redirect(request.referrer)
        # Add user and photo_id to Likes table
        cursor.execute('''INSERT INTO Likes (user_id, picture_id) VALUES (%s, %s)''', (uid, photo_id))
        conn.commit()
        return redirect(request.referrer)
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        album_id = request.args.get('album_id')
        album_name = getAlbumName(album_id)
        photos = getUsersPhotos(uid, album_id)
        photo_ids = getPhotoId(album_id)
		# FINISH LIKES!!!!
        likes = {}
        for photo in range(len(photo_ids)): 
            likes[photo_ids[photo]] = getPictureLikes(photo_ids[photo])
        return render_template('albumphoto.html', album_name=album_name, \
                               album_id=album_id, photos=photos, likes=likes, base64=base64)
    
@app.route('/unlike', methods=['POST'])
def unlike(): 
	album_id = request.form.get('album_id')
	photo_id = request.form.get('photo_id')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	# Check if user has liked this photo before
	cursor = conn.cursor()
	cursor.execute('''SELECT * FROM Likes WHERE user_id = %s AND picture_id = %s''', (uid, photo_id))
	if cursor.fetchone() is not None:
		cursor.execute('''DELETE FROM Likes WHERE user_id = %s AND picture_id = %s''', (uid, photo_id))
		conn.commit()
		return redirect(request.referrer)
	else: 
		return redirect(request.referrer)

@app.route('/viewlikes', methods=['GET'])
def viewlikes(): 
	photo_id = request.args.get('photo_id')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	likers = getWhoLiked(photo_id)
	photolikers = {}
	for likes in range(len(likers)):
		fname, lname = getUsersName(likers[likes])
		photolikers[likers[likes]] = f"{fname} {lname}"
	return render_template('viewlikes.html', likers=likers, uid=uid, photo_id=photo_id, photolikers=photolikers)

@app.route('/createalbum', methods=['GET', 'POST'])
def createalbum(): 
	if request.method == 'POST': 
		uid = getUserIdFromEmail(flask_login.current_user.id)
		creationdate = datetime.now()
		album_name = request.form.get('album_name')
		cursor = conn.cursor() 
		cursor.execute('''INSERT INTO Albums (Name, date_of_creation, user_id) VALUES (%s, %s, %s)''', (album_name, creationdate, uid)) 
		conn.commit() 
		return redirect(url_for('album'))
	#otherwise GET 
	else: 
		uid = getUserIdFromEmail(flask_login.current_user.id)
		albums = getUsersAlbums(uid)
		return render_template('createalbum.html', albums=albums)
	
@app.route('/deletealbum', methods=['POST'])
def deletealbum(): 
    album_id = request.form.get('album_id') 
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM Albums WHERE album_id = %s''', (album_id,))
    conn.commit()
    return redirect(url_for('album'))
    
@app.route('/deletephoto', methods=['GET', 'POST'])
def deletephoto(): 
	if request.method == 'POST': 
		album_id = request.form.get('album_id')
		photo_id = request.form.get('photo_id')
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM Pictures WHERE picture_id = %s''', (photo_id,))
		conn.commit()
		return redirect(url_for('albumphoto', album_id=album_id))
	else: 
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_id = request.args.get('album_id')
		return render_template('deletephoto.html', album_id=album_id, photos=getUsersPhotos(uid, album_id), base64=base64)
	
@app.route('/addfriend', methods=['POST'])
def addfriend():
	if not isEmailUnique(request.form.get('friendemail')):
		uid = request.form.get('uid')
		uid2 = getUserIdFromEmail(request.form.get('friendemail'))
		cursor = conn.cursor() 
		cursor.execute('''INSERT INTO Friendship (UID1, UID2) VALUES (%s, %s)''', (uid, uid2))
		conn.commit()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Friendship (UID1, UID2) VALUES (%s, %s)''', (uid2, uid))
		conn.commit()
		return redirect(url_for('friendslist'))
	return render_template('friendslist.html',message="User does not exist!")

@app.route('/removefriend', methods=['POST'])
def removefriend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friend_id = request.form.get('friend_id')
	cursor = conn.cursor()
	cursor.execute('''DELETE FROM Friendship WHERE UID1 = %s OR UID2 = %s''', (uid, friend_id))
	conn.commit()
	cursor = conn.cursor()
	cursor.execute('''DELETE FROM Friendship WHERE UID1 = %s OR UID2 = %s''', (friend_id, uid))
	conn.commit()
	return redirect(url_for('friendslist'))
	
@app.route('/friendslist')
@flask_login.login_required
def friendslist(): 
	uid = getUserIdFromEmail(flask_login.current_user.id) 
	friendids = getUsersFriends(uid)
	friendname = {} 
	for friend in range(len(friendids)): 
		fname, lname = getUsersName(friendids[friend])
		friendname[friendids[friend]] = f"{fname} {lname}"
	return render_template('friendslist.html', friendname=friendname, uid=uid)

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
