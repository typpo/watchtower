"""
Go through and check all pages that need to be updated
"""

from datetime import datetime, timedelta
import sys
import os
from operator import attrgetter
from datetime import datetime

from models import Page
from database import db
from fingerprint import get_fingerprints

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.app import create_app

app = create_app()
app.test_request_context().push()

if __name__ == '__main__':
  pages = list(Page.query.filter(Page.next_check < datetime.utcnow()))
  print len(pages), 'pages due for checking'
  
  now = datetime.utcnow()

  for page in pages:    
    elements = page.elements
    selectors = [element.selector for element in elements]
    old_fingerprints = [max(element.versions, key=attrgetter('when')).fingerprint for element in elements]
    new_fingerprints = get_fingerprints(page.url, selectors)

    for element, old, new in zip(elements, old_fingerprints, new_fingerprints):
      diffs = diff_fingerpints(old, new)
      if diffs:
        version = Version(fingerprint=new, diff=diffs, when=now, element=element)
        db.session.add(version)
    
    page.next_check = now + timedelta(minutes=page.frequency)
    db.session.add(page)

  db.session.commit()
