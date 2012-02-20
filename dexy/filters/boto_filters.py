from boto.s3.key import Key
from dexy.dexy_filter import DexyFilter
import boto
import getpass

class BotoUploadFilter(DexyFilter):
    """
    Uses boto library to upload content to S3, returns the URL.

    You can set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY variables in your
    system environment (the environment that runs the dexy command) or you can
    set defaults in your ~/.dexyapis file (these will override the environment):

    "AWS" : {
        "AWS_ACCESS_KEY_ID" : "AKIA...",
        "AWS_SECRET_ACCESS_KEY" : "hY6cw...",
        "bucket-name" : "my-unique-bucket-name"
    }

    You can also set these in your project's .dexy file:

    TODO example...

    If you do not set bucket-name, it will default to a name based on your
    username. This may not be unique across all S3 buckets so it may be
    necessary for you to specify a name. You can use an existing S3 bucket,
    a new bucket will be created if your bucket does not already exist.
    """
    ALIASES = ['boto', 'botoup']
    OUTPUT_EXTENSIONS = [".txt"]

    def bucket_name(self):
        """Calculate S3 bucket name, create it if it doesn't exist."""
        if self.artifact.args.has_key('bucket-name'):
            bucket_name = self.artifact.args['bucket-name']
        else:
            try:
                username = getpass.getuser()
                bucket_name = "dexy-%s" % username
                return bucket_name
            except Exception as e:
                print "Can't automatically determine username. Please specify bucket-name for upload to S3."
                raise e

    def boto_connection(self):
        return boto.connect_s3()

    def get_bucket(self):
        conn = self.boto_connection()
        return conn.create_bucket(self.bucket_name())

    def process_text(self, input_text):
        b = self.get_bucket()
        k = Key(b)
        k.key = self.artifact.previous_websafe_key
        k.set_contents_from_filename(self.artifact.previous_artifact_filepath)
        k.set_acl('public-read')
        return "https://s3.amazonaws.com/%s/%s" % (self.bucket_name(), k.key)
