"""
Models
"""

from database import db

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)

class Page(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  url = db.Column(db.String(1024))
  elements = db.relationship('Element',
                             backref='page', lazy='dynamic')
  
  def __init__(self, name, url):
    self.name = name
    self.url = url

  def __repr__(self):
    return '<Page %r>' % self.url

class Version(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  blob = db.Column(db.Text)
  when = db.Column(db.DateTime, key='when')
  element_id = db.Column(db.Integer, db.ForeignKey('element.id'))

  def __init__(self, blob, when, element):
    self.blob = blob
    self.when = when
    self.element = element

  def __repr__(self):
    return '<Version %r at %r>' % (self.page_id, self.when)

class Element(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  selector = db.Column(db.String(255))
  versions = db.relationship('Version',
                             backref='element', lazy='dynamic')
  page_id = db.Column(db.Integer, db.ForeignKey('page.id'))

  def __init__(self, name, selector, page):
    self.name = name
    self.selector = selector
    self.page = page

  def __repr__(self):
    return '<Element %r>' % self.selector
