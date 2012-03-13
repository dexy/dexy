import boto
from boto.s3.key import Key
from dexy.filters.api_filters import ApiFilter
import getpass
import os

class BotoUploadFilter(ApiFilter):
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
    API_KEY_NAME = 'AWS'
    API_KEY_KEYS = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_BUCKET_NAME']

    def bucket_name(self):
        """
        Figure out which S3 bucket name to use and create the bucket if it doesn't exist.
        """
        bucket_name = self.read_param('AWS_BUCKET_NAME')
        if not bucket_name:
            try:
                username = getpass.getuser()
                bucket_name = "dexy-%s" % username
                return bucket_name
            except Exception as e:
                print "Can't automatically determine username. Please specify AWS_BUCKET_NAME for upload to S3."
                raise e
        self.log.debug("S3 bucket name is %s" % bucket_name)
        return bucket_name

    def boto_connection(self):
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            # use values defined in env
            return boto.connect_s3()
        else:
            # use values specified in .dexyapis
            aws_access_key_id = self.read_param('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = self.read_param('AWS_SECRET_ACCESS_KEY')
            return boto.connect_s3(aws_access_key_id, aws_secret_access_key)

    def get_bucket(self):
        conn = self.boto_connection()
        return conn.create_bucket(self.bucket_name())

    def process_text(self, input_text):
        b = self.get_bucket()
        k = Key(b)
        k.key = self.artifact.previous_websafe_key
        self.log.debug("Uploading contents of %s" % self.artifact.previous_artifact_filepath)
        k.set_contents_from_filename(self.artifact.previous_artifact_filepath)
        k.set_acl('public-read')
        return "https://s3.amazonaws.com/%s/%s" % (self.bucket_name(), k.key)
