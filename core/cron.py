"""
Go through and check all pages that need to be updated
"""

from datetime import datetime, timedelta
import sys
import os
from operator import attrgetter
from datetime import datetime
from flask import json

from models import Page, Version
from database import db
from fingerprint import get_fingerprints, diff_fingerprints
import screenshots

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.app import create_app

app = create_app()
app.test_request_context().push()

if __name__ == '__main__':
  #pages = list(Page.query.filter(Page.next_check < datetime.utcnow()))
  pages = list(Page.query.all())
  print len(pages), 'pages due for checking'

  now = datetime.utcnow()

  for page in pages:
    elements = page.elements
    if len(list(elements)) < 1:
      continue
    print '** Werking', page.url
    selectors = [element.selector for element in elements]
    old_fingerprints = []
    for element in elements:
      if len(list(element.versions)) < 1:
        print '** No old versions'
        old_print = None
      else:
        print '** Found some old versions'
        old_print = json.loads(max(element.versions, key=attrgetter('when')).fingerprint)
      old_fingerprints.append(old_print)
    try:
      new_fingerprints, screenshot_url, screenshot_local = get_fingerprints(page.url, selectors)
    except:
      print 'ERROR'
      continue

    if len(old_fingerprints) < 1:
      # it's new
      print '** This is the FIRST version'
      if screenshot_url:
        screenshots.upload_screenshot(screenshot_local, screenshot_url)

      for element, new in zip(elements, new_fingerprints):
        version = Version(fingerprint=json.dumps(new), diff=json.dumps([]), when=now, element=element, screenshot=screenshot_url)
        db.session.add(version)

    else:
      print '** Diffing against previous version'
      for element, old, new in zip(elements, old_fingerprints, new_fingerprints):
        print old, new
        diffs = diff_fingerprints(old, new)
        past_fingerprints = [version.fingerprint for version in element.versions]
        if diffs is None or \
            (diffs and new not in past_fingerprints): # check against all previous fingerprints for this element
          print '** New version found'
          print '** diffs:', diffs
          print '** storing version:', new
          # new version found
          if diffs is None:
            diffs = []
          version = Version(fingerprint=json.dumps(new), diff=json.dumps(diffs), when=now, element=element, screenshot=screenshot_url)

          # Upload new screenshot
          if screenshot_url:
            screenshots.upload_screenshot(screenshot_local, screenshot_url)

          db.session.add(version)
        else:
          print '** Not a new version'

    if os.path.exists(screenshot_local):
      os.remove(screenshot_local)  #clean up local screenshot

    page.next_check = page.next_check + timedelta(minutes=page.frequency)
    db.session.add(page)

  db.session.commit()
