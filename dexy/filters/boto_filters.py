from boto.s3.key import Key
from dexy.dexy_filter import DexyFilter
import boto

class BotoUploadFilter(DexyFilter):
    """Uses boto library to upload content to S3."""
    ALIASES = ['botoup']

    # set your bucket name, env should have keys as per boto docs
    BUCKET_NAME = None

    def process_text(self, input_text):
        conn = boto.connect_s3()
        b = conn.get_bucket(self.BUCKET_NAME)
        k = Key(b)
        fn = self.artifact.filename(False)
        k.key = fn
        k.set_contents_from_filename(self.artifact.previous_artifact_filename)
        k.set_acl('public-read')
        return "https://s3.amazonaws.com/%s/%s" % (self.BUCKET_NAME, fn)
