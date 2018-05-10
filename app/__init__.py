from flask import Flask
from flask.ext.mail import Message
from flask_mail import Mail
import boto3
import os


webapp = Flask(__name__)
webapp.config.from_pyfile('email_config.cfg')

mail = Mail(webapp)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGE_STORE = "ece1779fall2017a3"
TMP_FOLDER = os.path.join('/', 'tmp')

print(IMAGE_STORE)
S3_ADDR = "https://s3.amazonaws.com/" + IMAGE_STORE + '/'
import Lab3
dynamo = boto3.resource('dynamodb')
webapp.secret_key = 'ECE1779Winter2017BestTeam'
