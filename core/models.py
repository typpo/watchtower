"""
Models
"""
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from database import db
from datetime import datetime
import json

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  email = db.Column(db.String(255))
  openid = db.Column(db.String(255))
  pages = db.relationship('Page',
                          backref='user', lazy='dynamic')

  def __init__(self, name, email, openid):
    self.openid = openid
    self.name = name
    self.email = email

  def __repr__ (self):
    return '<User %r>' % self.name

class Page(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  url = db.Column(db.String(1024))
  elements = db.relationship('Element',
                             backref='page', lazy='dynamic')

  frequency = db.Column(db.Integer, default=60)   # minutes
  next_check = db.Column(db.DateTime)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

  def __init__(self, name, url, user_id=None, next_check=datetime.utcnow(), frequency=None):
    self.name = name
    self.url = url
    self.next_check = next_check
    if frequency:
      self.frequency = frequency
    self.user_id = user_id

  def __repr__(self):
    return '<Page %r>' % self.name

  def elementsJSON(self):
    return [e.toJSON() for e in self.elements]

class Version(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  fingerprint = db.Column(db.Text)
  diff = db.Column(db.Text)
  when = db.Column(db.DateTime, key='when')
  element_id = db.Column(db.Integer, db.ForeignKey('element.id'))
  screenshot = db.Column(db.String(255), default='')

  def __init__(self, fingerprint, diff, element, when=datetime.utcnow()):
    self.fingerprint = fingerprint
    self.diff = diff
    self.when = when
    self.element = element
    self.screenshot = screenshot

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
    return '<Element %r>' % self.name

  def toJSON(self):
    return {
      'id': self.id, \
      'name': self.name,  \
      'selector': self.selector, \
    }

