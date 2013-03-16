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
    selectors = [element.selector for element in elements]
    old_fingerprints = [json.loads(max(element.versions, key=attrgetter('when')).fingerprint) for element in elements]
    new_fingerprints, screenshot_url, screenshot_local = get_fingerprints(page.url, selectors)

    if len(old_fingerprints) < 1:
      # it's new
      print 'new screenshot', screenshot_url
      if screenshot_url:
        screenshots.upload_screenshot(screenshot_local, screenshot_url)

    else:
      for element, old, new in zip(elements, old_fingerprints, new_fingerprints):
        diffs = diff_fingerprints(old, new)
        if diffs and new not in [version.fingerprint for version in element.versions]: # check against all previous fingerprints for this element
          # new version found
          version = Version(fingerprint=json.dumps(new), diff=json.dumps(diffs), when=now, element=element, screenshot=screenshot_url)

          # Upload new screenshot
          if screenshot_url:
            screenshots.upload_screenshot(screenshot_local, screenshot_url)

          db.session.add(version)

    if os.path.exists(screenshot_local):
      os.remove(screenshot_local)  #clean up local screenshot

    page.next_check = page.next_check + timedelta(minutes=page.frequency)
    db.session.add(page)

  db.session.commit()
