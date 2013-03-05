from boto.s3.connection import S3Connection, Bucket, Key
import hashlib

def upload_screenshot(path, remote_path):
  conn = S3Connection('AKIAIZXASMHAKITV3X3Q', 'uhZLAKaSn2n/35cB3ZhgK7ow6rO0LALzybIiHFOg')
  b = Bucket(conn, 'watchtower-screenshots')
  k = Key(b)
  k.key = remote_path
  k.set_metadata("Content-Type", 'image/png')
  k.set_contents_from_file(open(path, 'rb'))
  k.set_acl("public-read")

  print 'uploaded to https://s3.amazonaws.com/watchtower-screenshots/' + remote_path
  return True
