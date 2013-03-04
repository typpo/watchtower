# manage.py

from flask.ext.script import Manager
from flask.ext.evolution import Evolution

from app import app

manager = Manager(app)
evolution = Evolution(app)

@manager.command
def hello():
    print "hello"

@manager.command
def migrate(action):
  evolution.manager(action)

if __name__ == "__main__":
    manager.run()
