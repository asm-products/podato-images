import urllib

from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.api import blobstore

import webapp2
import cloudstorage
import urllib

GCS_BUCKET = app_identity.get_default_gcs_bucket_name()

def create_file(filename, contents, mime_type):
  filename = "/" + GCS_BUCKET + "/" + filename
  # Create a GCS file with GCS client.
  with cloudstorage.open(filename, 'w', content_type=mime_type) as f:
    f.write(contents.read())

  # Blobstore API requires extra /gs to distinguish against blobstore files.
  blobstore_filename = '/gs' + filename
  # This blob_key works with blobstore APIs that do not expect a
  # corresponding BlobInfo in datastore.
  return blobstore.create_gs_key(blobstore_filename)


def fetch_and_store(url):
    res = urllib.urlopen(url)
    mime = res.headers.get("content-type")
    if not mime or mime.lower() not in ["image/jpeg", "image/png", "image/gif"]:
        raise ValueError("Unsupported image type: %s" % (mime))
    filename = urllib.quote_plus(url)
    return create_file(filename, res, mime)

class MainHandler(webapp2.RequestHandler):
    def get(self, size):
        url = self.request.get("url")
        key = memcache.get(url)
        if not key:
            key = fetch_and_store(url)
            memcache.set(url, key)
        try:
            img_url = images.get_serving_url(key, secure_url=True, size=int(size))
        except images.ObjectNotFoundError:
            key = fetch_and_store(url)
            memcache.set(url, key)
            img_url = images.get_serving_url(key, secure_url=True)
        self.redirect(img_url, permanent=True)

app = webapp2.WSGIApplication([
    webapp2.Route("/<size>", MainHandler)
], debug=True)
