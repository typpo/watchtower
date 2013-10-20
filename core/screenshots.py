from boto.s3.connection import S3Connection, Bucket, Key
import hashlib
import os

def upload_screenshot(path, remote_path, delete_local_file=False):
  # delete local file if applicable
  if not os.path.exists(path):
    print 'error: %s does not exist; could not upload to %s' % (path, remote_path)
    return

  conn = S3Connection('AKIAIZXASMHAKITV3X3Q', 'uhZLAKaSn2n/35cB3ZhgK7ow6rO0LALzybIiHFOg')
  b = Bucket(conn, 'watchtower-screenshots')
  k = Key(b)
  k.key = remote_path
  k.set_metadata("Content-Type", 'image/png')
  k.set_contents_from_file(open(path, 'rb'))
  k.set_acl("public-read")

  print 'uploaded to https://s3.amazonaws.com/watchtower-screenshots/' + remote_path

  if delete_local_file:
    os.remove(path)

  return True
