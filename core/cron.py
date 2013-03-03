"""
Go through and check all pages that need to be updated
"""

from datetime import datetime, timedelta
import sys
import os

from models import Page
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ..web.app import create_app

app = create_app()

if __name__ == '__main__':

  pages = Page.query.filter(Page.next_check < datetime.utcnow())

  print len(pages), 'pages due for checking'
  
  for page in pages:
    
    # TODO check page
    
    page.next_check = datetime.now() + timedelta(minutes=page.frequency)
    page.save()
