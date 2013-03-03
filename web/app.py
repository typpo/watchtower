#!/usr/bin/env python
from flask import Flask, request, redirect, session, url_for, render_template, Response, Markup
import urllib
import urlparse
import json

app = Flask(__name__)
app.secret_key = 'not a secret key'

@app.route("/")
def index():
  return render_template('index.html')

@app.route('/placeholder')
def placeholder():
  query = request.args.get('query')
  json_resp = json.dumps({'foo': 'bar'})
  return Response(json_resp, mimetype='application/json')

@app.route('/proxy')
def proxy():
  data = request.data
  google = 'www.google.com'
  response = urllib.urlopen('http://' + google)
  html = Markup(response.read())
  return render_template('proxy.html', html=html)
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', use_reloader=True)
