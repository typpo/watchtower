"""
The database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
#from core.utils import is_production
def is_production():
  # I'm so bad why doesn't this work??
  import socket
  return socket.gethostname().endswith('gowatchtower.com')

db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = 'not a secret key'
if is_production():
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:jackathon@localhost/watchtower'
else:
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/watchtower/watchtower.db'
db.init_app(app)
