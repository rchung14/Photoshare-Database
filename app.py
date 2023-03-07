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
app.config['MYSQL_DATABASE_PASSWORD'] = 'Wjddnwls2002!' #'Wjddnwls2002!'
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

def getTagIds(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT tag_id FROM Tagged WHERE photo_id = %s", (photo_id,))
    tag_ids = [row[0] for row in cursor.fetchall()]
    return tag_ids

def getPhotoTag(photo_id):
    cursor = conn.cursor()
    cursor.execute('''SELECT Tags.tag_name FROM Tags JOIN Tagged ON Tags.tag_id = Tagged.tag_id WHERE \
		Tagged.photo_id = %s ''', (photo_id,))
    return [row[0] for row in cursor.fetchall()]

def getPhotoComments(photo_id):
    cursor = conn.cursor()
    cursor.execute('''SELECT Comments.text, Users.email, Comments.date FROM Comments JOIN Users ON \
		Comments.user_id = Users.user_id WHERE Comments.picture_id = %s ORDER BY Comments.date DESC''', (photo_id,))
    return cursor.fetchall()

def getAllUsers():
    cursor = conn.cursor()
    cursor.execute('''SELECT DISTINCT user_id FROM Users''')
    user_ids = [row[0] for row in cursor.fetchall()]
    return user_ids

def getUserFromAlbumId(album_id):
	cursor = conn.cursor() 
	cursor.execute("SELECT user_id FROM Albums WHERE album_id = '{0}'".format(album_id,))
	return cursor.fetchone()[0]

def getEmailFromId(uid):
	cursor = conn.cursor() 
	cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(uid,))
	return cursor.fetchone()[0]

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

# to do:
# - implement guests being able to like/unlike/comment/etc
# - visitors and users leave comments (registered + 1 contribution score) 

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/contribution', methods=['GET'])
def contribution():
	contribution = {}
	allusers = getAllUsers()
	for user in allusers: 
		fname, lname = getUsersName(user)
		cursor = conn.cursor()
		# count uploaded photos
		cursor.execute('''SELECT COUNT(*) FROM Pictures WHERE user_id = %s''', (user,))
		photocount = cursor.fetchone()[0]
		cursor.execute('''SELECT COUNT(*) FROM Comments c JOIN Pictures p ON c.picture_id = p.picture_id WHERE c.user_id = %s AND p.user_id <> %s''', (user, user,))
		commentcount = cursor.fetchone()[0]
		contribution[f"{fname} {lname}"] = photocount + commentcount
	sorted_contribution = dict(sorted(contribution.items(), key=lambda x: x[1], reverse=True)[:10])
	return render_template('contribution.html', sorted_contribution=sorted_contribution)

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
		tags = request.form.get('tags')
		tags_list = tagFormat(tags)
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (user_id, caption, imgdata, album_id) VALUES (%s, %s, %s, %s)''', (uid, caption, photo_data, album_id))
		conn.commit()
		picture_id = cursor.lastrowid
		for tag in tags_list: 
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Tags (tag_name) VALUES (%s)''', (tag,))
			cursor.execute('''SELECT tag_id FROM Tags WHERE tag_name=%s''', (tag,))
			tag_id = cursor.fetchone()[0]
			cursor.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''', (picture_id, tag_id))
			conn.commit()
		return redirect(url_for('albumphoto', album_id=album_id))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		albums = getUsersAlbums(uid)
		return render_template('upload.html', albums=albums)

#putting into album/viewing album
@app.route('/album', methods=['GET'])
@flask_login.login_required
def album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums = getUsersAlbums(uid)
	return render_template('album.html', albums=albums)

@app.route('/albumphoto', methods=['GET'])
@flask_login.login_required
def albumphoto():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	album_id = request.args.get('album_id')
	album_name = getAlbumName(album_id)
	photos = getUsersPhotos(uid, album_id)
	photo_ids = getPhotoId(album_id)
	tags = {}
	likes = {}
	comments = {} 
	for photo in range(len(photo_ids)): 
		tags[photo_ids[photo]] = getPhotoTag(photo_ids[photo])
		likes[photo_ids[photo]] = getPictureLikes(photo_ids[photo])
		comments[photo_ids[photo]] = getPhotoComments(photo_ids[photo])
	return render_template('albumphoto.html', album_name=album_name, \
					album_id=album_id, photos=photos, comments=comments, \
						  tags=tags, likes=likes, base64=base64)
    
@app.route('/visitoralbumphoto', methods=['GET'])
def visitoralbumphoto(): 
	album_id = request.args.get('album_id')
	uid = getUserFromAlbumId(album_id)
	fname, lname = getUsersName(uid)
	username = f"{fname} {lname}"
	album_name = getAlbumName(album_id)
	photos = getUsersPhotos(uid, album_id)
	photo_ids = getPhotoId(album_id)
	tags = {}
	likes = {}
	comments = {} 
	for photo in range(len(photo_ids)): 
		tags[photo_ids[photo]] = getPhotoTag(photo_ids[photo])
		likes[photo_ids[photo]] = getPictureLikes(photo_ids[photo])
		comments[photo_ids[photo]] = getPhotoComments(photo_ids[photo])
	return render_template('visitoralbumphoto.html', album_name=album_name, \
					album_id=album_id, photos=photos, comments=comments, \
						  tags=tags, username=username, likes=likes, base64=base64)

@app.route('/like', methods=['POST'])
def like():
	photo_id = request.form.get('photo_id')
	if flask_login.current_user.is_authenticated:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	else:
		uid = -1
	# Check if user has liked this photo before
	cursor = conn.cursor()
	cursor.execute('''SELECT * FROM Likes WHERE user_id = %s AND picture_id = %s''', (uid, photo_id))
	if cursor.fetchone() is not None:
		return redirect(request.referrer)
	# Add user and photo_id to Likes table
	cursor.execute('''INSERT INTO Likes (user_id, picture_id) VALUES (%s, %s)''', (uid, photo_id))
	conn.commit()
	return redirect(request.referrer)

@app.route('/unlike', methods=['POST'])
def unlike(): 
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
	likers = getWhoLiked(photo_id)
	photolikers = {}
	for likes in range(len(likers)):
		fname, lname = getUsersName(likers[likes])
		photolikers[likers[likes]] = f"{fname} {lname}" 
	return render_template('viewlikes.html', likers=likers, photo_id=photo_id, photolikers=photolikers)

@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
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
@flask_login.login_required
def deletealbum(): 
    album_id = request.form.get('album_id') 
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM Tags WHERE tag_id IN (
                        SELECT DISTINCT tag_id FROM Tagged
                        WHERE photo_id IN (
                            SELECT picture_id FROM Pictures
                            WHERE album_id = %s
                        )
                    )''', (album_id,))
    cursor.execute('''DELETE FROM Albums WHERE album_id = %s''', (album_id,))
    conn.commit()
    return redirect(url_for('album'))

@app.route('/allalbums', methods=['GET'])
def allalbums():
    cursor = conn.cursor() 
    if flask_login.current_user.is_authenticated:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor.execute('''SELECT album_id, name FROM Albums WHERE user_id <> %s''', (uid,))
    else:
        cursor.execute('''SELECT album_id, name FROM Albums''')
    albums = cursor.fetchall()
    return render_template('allalbums.html', albums=albums)

@app.route('/deletephoto', methods=['POST'])
@flask_login.login_required
def deletephoto(): 
    photo_id = request.form.get('photo_id')
    cursor = conn.cursor()
    cursor.execute('''SELECT tag_id FROM Tagged WHERE photo_id = %s''', (photo_id,))
    tag_ids = cursor.fetchall()
    cursor.execute('''DELETE FROM Pictures WHERE picture_id = %s''', (photo_id,))
    cursor.execute('''DELETE FROM Tagged WHERE photo_id = %s''', (photo_id,))
    for tag_id in tag_ids:
        cursor.execute('''DELETE FROM Tags WHERE tag_id = %s''', (tag_id[0],))
    conn.commit()
    return redirect(request.referrer)
	
@app.route('/addfriend', methods=['POST'])
@flask_login.login_required
def addfriend():
	if not isEmailUnique(request.form.get('friendemail')):
		uid = getUserIdFromEmail(flask_login.current_user.id)
		uid2 = getUserIdFromEmail(request.form.get('friendemail'))
		cursor = conn.cursor() 
		cursor.execute('''INSERT INTO Friendship (UID1, UID2) VALUES (%s, %s)''', (uid, uid2))
		cursor.execute('''INSERT INTO Friendship (UID1, UID2) VALUES (%s, %s)''', (uid2, uid))
		conn.commit()
		return redirect(url_for('friendslist'))
	return render_template('friendslist.html',message="User does not exist!")

@app.route('/removefriend', methods=['POST'])
@flask_login.login_required
def removefriend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	friend_id = request.form.get('friend_id')
	cursor = conn.cursor()
	cursor.execute('''DELETE FROM Friendship WHERE UID1 = %s AND UID2 = %s''', (uid, friend_id))
	cursor.execute('''DELETE FROM Friendship WHERE UID1 = %s AND UID2 = %s''', (friend_id, uid))
	conn.commit()
	return redirect(url_for('friendslist'))
	
@app.route('/friendslist', methods=['GET'])
@flask_login.login_required
def friendslist(): 
	uid = getUserIdFromEmail(flask_login.current_user.id) 
	friendids = getUsersFriends(uid)
	friendname = {} 
	recommended_ids = {} 
	recommended_friends ={} 
	for friend in range(len(friendids)): 
		recommended_ids[friendids[friend]] = getUsersFriends(friendids[friend])
		fname, lname = getUsersName(friendids[friend])
		friendname[friendids[friend]] = f"{fname} {lname}"
	for friendid in recommended_ids.values(): 
		for recfriend in friendid:
			if recfriend == uid or recfriend in friendname:
				continue
			fname, lname = getUsersName(recfriend)
			email = getEmailFromId(recfriend)
			recommended_friends[recfriend] = f"{fname} {lname} ({email})"
	return render_template('friendslist.html', friendname=friendname, recommended_friends=recommended_friends)

@app.route('/comment', methods=['POST'])
def comment(): 
    comment_text = request.form.get('comment')
    photo_id = request.form.get('photo_id')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    commentdate = datetime.now()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO Comments (text, date, user_id, picture_id) VALUES (%s, %s, %s, %s)''', (comment_text, commentdate, uid, photo_id))
    conn.commit()
    return redirect(request.referrer)

@app.route('/search', methods=['GET', 'POST'])
def search():
	if request.method == 'POST':
		search_type = request.form['search_type']
		query = request.form['search']
		if search_type == 'tag':
			# Get all photos with tags
			cursor = conn.cursor()
			cursor.execute('SELECT p.*, u.user_id FROM Pictures p JOIN Tagged t ON p.picture_id = t.photo_id JOIN Tags tg ON tg.tag_id = t.tag_id JOIN Users u ON p.user_id = u.user_id WHERE tg.tag_name IN %s', ([tag.strip().lower() for tag in query.split(',')],))
			rows = cursor.fetchall()
			photos_dict = {}
			for row in rows:
				photo_id = row[0]
				if photo_id not in photos_dict:
					photos_dict[photo_id] = row
			photos = list(photos_dict.values())
		elif search_type == 'tag_user':
			# Get photos of current user with tags
			cursor = conn.cursor()
			cursor.execute('SELECT p.*, u.user_id FROM Pictures p JOIN Tagged t ON p.picture_id = t.photo_id JOIN Tags tg ON tg.tag_id = t.tag_id JOIN Users u ON p.user_id = u.user_id WHERE tg.tag_name IN %s AND p.user_id = %s', ([tag.strip().lower() for tag in query.split(',')], getUserIdFromEmail(flask_login.current_user.id)))
			rows = cursor.fetchall()
			photos_dict = {}
			for row in rows:
				photo_id = row[0]
				if photo_id not in photos_dict:
					photos_dict[photo_id] = row
			photos = list(photos_dict.values())
		elif search_type == 'comments':
			# Get all photos with matching comments
			cursor = conn.cursor()
			cursor.execute('SELECT p.*, u.user_id FROM Pictures p JOIN Comments c ON p.picture_id = c.picture_id JOIN Users u ON p.user_id = u.user_id WHERE c.text LIKE %s', ('%' + query + '%',))
			photos = cursor.fetchall()
		tags = {}
		likes = {}
		comments = {} 
		if len(photos) >= 1: 
			for photo in photos:
				photo_id = photo[0] 
				tags[photo_id] = getPhotoTag(photo_id)
				likes[photo_id] = getPictureLikes(photo_id)
				comments[photo_id] = getPhotoComments(photo_id)
		return render_template('search.html', photos=photos, tags=tags, comments=comments, likes=likes, base64=base64)
	else:
		return render_template('search.html')
	
@app.route('/popular_tags', methods=['GET'])
def PopularTags():
		return render_template('top_tags.html', tags = GrabTags())
	
def GrabTags():
	cursor = conn.cursor()
	cursor.execute("SELECT tag_name, COUNT(tag_name) FROM Tags, Tagged WHERE Tags.tag_id = Tagged.tag_id GROUP BY tag_name ORDER BY COUNT(tag_name) DESC LIMIT 3")
	tags = cursor.fetchall()
	return tags

@app.route('/youmaylike', methods=['GET'])
@flask_login.login_required
def youmaylike():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    # Retrieve the current user's top 3 tags
    cursor.execute(
        '''SELECT tg.tag_name
           FROM Pictures p
           JOIN Tagged t ON p.picture_id = t.photo_id
           JOIN Tags tg ON tg.tag_id = t.tag_id
           WHERE p.user_id = %s
           GROUP BY tg.tag_name
           ORDER BY COUNT(*) DESC
           LIMIT 3''', (uid,))
    top_tags = [row[0] for row in cursor.fetchall()]
    # If the user has no top tags, display an error message
    if not top_tags:
        return render_template('youmaylike.html', message="Post a photo with tags!")
    else:
        # Retrieve all photos in the database that have at least one of the user's top tags
        cursor.execute(
            '''SELECT p.*
               FROM Pictures p
               JOIN Tagged t ON p.picture_id = t.photo_id
               JOIN Tags tg ON tg.tag_id = t.tag_id
               WHERE tg.tag_name IN %s
                 AND p.user_id != %s
               GROUP BY p.picture_id
               ORDER BY COUNT(*) DESC;''', (tuple(top_tags), uid))
        photos = cursor.fetchall()
        tags = {}
        likes = {}
        comments = {} 
        if len(photos) >= 1: 
            for photo in photos:
                photo_id = photo[0] 
                tags[photo_id] = getPhotoTag(photo_id)
                likes[photo_id] = getPictureLikes(photo_id)
                comments[photo_id] = getPhotoComments(photo_id)
        # Render the result set on the web page
        return render_template('youmaylike.html', photos=photos, comments=comments, likes=likes, tags=tags, base64=base64)

@app.route('/search_comment', methods=['GET', 'POST'])
def SearchComments():
	if request.method == 'POST':
		comment = request.form.get('comment')
		cursor = conn.cursor()
		cursor.execute("SELECT fname, lname, COUNT(*) AS users_found FROM Users, Comments WHERE Users.user_id = Comments.user_id AND text = '{0}' GROUP BY Users.user_id ORDER BY users_found DESC".format(comment))
		comments = cursor.fetchall()

		return render_template('comment_search.html', message="User's found that match this specific comment", comments = comments)
	else:
		return render_template('comment_search.html')

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
