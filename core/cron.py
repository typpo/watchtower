"""
Go through and check all pages that need to be updated
"""

from datetime import datetime, timedelta

pages = Page.query.filter(Page.next_check < datetime.now())

print len(pages), 'pages due for checking'

for page in pages:

  # TODO check page

  page.next_check = datetime.now() + timedelta(minutes=page.frequency)
  page.save()
