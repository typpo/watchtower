"""
Models
"""
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from database import db

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)

class Element(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  selector = db.Column(db.String(255), unique=True)
  page_id = db.Column(db.Integer, db.ForeignKey('page.id'))
  page = db.relationship('Page',
                         backref=db.backref('elements', lazy='dynamic'))

  def __init__(self, selector, page):
    self.selector = selector
    self.page = page

  def __repr__(self):
    return '<Element %r>' % self.selector

class Page(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  url = db.Column(db.String(1024))
  blob = db.Column(db.Text)

  def __init__(self, url, blob):
    self.url = url
    self.blob = blob

  def __repr__(self):
    return '<Page %r>' % self.url
