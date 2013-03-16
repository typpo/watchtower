import sys
import os
import pytz
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.models import Element, Version, Twitter, Page, User

def filter_element_from_version(version):
  return Element.query.filter_by(id=version.element_id).first()

def filter_page_from_element(element):
  return Page.query.filter_by(id=element.page_id).first()

def filter_page_from_version(version):
  # better way?
  return filter_page_from_element(filter_element_from_version(version))

def filter_to_local_datetime(dt):
  return format_datetime(dt)

def fn_localize_with_tz(date, tz_str):
  if not tz_str:  # necessary for backwards compatibility 3/11 some accounts don't have this set; alembic migration apparently isn't setting default?
    tz_str = 'America/Los_Angeles'
  ret = pytz.utc.localize(date).astimezone(pytz.timezone(tz_str))
  print ret.isoformat()
  return ret

