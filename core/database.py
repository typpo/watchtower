"""
The database
"""
import sys
import os
import socket
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

def is_production():
  return socket.gethostname().endswith('gowatchtower.com')

def is_scan():
  return socket.gethostname().endswith('watchtower-scan')

db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = 'not a secret key'
if is_production():
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:jackathon@localhost/watchtower'
elif is_scan():
  #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:jackathon@75.101.157.206/watchtower'
  # TODO assumes static private ip
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:jackathon@10.73.181.115/watchtower'
else:
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/watchtower/watchtower.db'
db.init_app(app)
