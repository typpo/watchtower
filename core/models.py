"""
Models
"""
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from database import db
from datetime import datetime

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)

class Page(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  url = db.Column(db.String(1024))
  elements = db.relationship('Element',
                             backref='page', lazy='dynamic')

  frequency = db.Column(db.Integer, default=60)   # minutes
  next_check = db.Column(db.DateTime, default=datetime.now())

  def __init__(self, name, url):
    self.name = name
    self.url = url

  def __repr__(self):
    return '<Page %r>' % self.url

class Version(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  finger = db.Column(db.Text)
  diff = db.Column(db.Text)
  when = db.Column(db.DateTime, key='when')
  element_id = db.Column(db.Integer, db.ForeignKey('element.id'))

  def __init__(self, fingerprint, diff, when, element):
    self.fingerprint = fingerprint
    self.diff = diff
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

