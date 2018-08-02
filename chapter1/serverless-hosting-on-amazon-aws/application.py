from flask import Flask

# EB looks for an 'application' callable by default.
application = Flask(__name__)

@application.route("/", methods=["GET"])
def hello():
    return "Hello World!"
 
if __name__ == "__main__":
    application.run()