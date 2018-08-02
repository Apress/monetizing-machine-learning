from flask import Flask
from flask_httpauth import HTTPDigestAuth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret key here'
auth = HTTPDigestAuth()

@auth.get_password
def get_pw(username):
	for user in open("users-file.txt","r").readlines():
		if username in user:
			user={user.split(':')[0]:user.split(':')[1].rstrip()}
			return user.get(username)
	return None

@app.route('/')
@auth.login_required
def index():
    return "Hello, %s!" % auth.username()

@app.route('/paywall')
@auth.login_required
def paywall():
    return "%s, you are on page 2!" % auth.username()

if __name__ == '__main__':
    app.run()