from dexy.reporter import Reporter
from boto.s3.key import Key
import boto
import datetime
import os
import tarfile
import uuid

class UploadSourceTgzS3Reporter(Reporter):
    """
    Upload original source content so it's easy to replicate.
    """
    def get_bucket(self, bucket_name):
        conn = boto.connect_s3()
        return conn.create_bucket(bucket_name)

    def run(self):
        batch_uuid = uuid.uuid4()
        report_filename = os.path.join(self.logsdir, "source-%s.tgz" % batch_uuid)
        tar = tarfile.open(report_filename, mode="w:gz")

        self.load_batch_artifacts()
        for key, artifact in self.artifacts.iteritems():
            if artifact.is_last and not artifact.virtual:
                tar.add(artifact.name)

        # TODO add all config files
        tar.add(".dexy")
        tar.close()
        bucket_name = "dexy-upload-source-reporter"
        bucket = self.get_bucket(bucket_name)

        k = Key(bucket)
        k.key = "sources.tgz"
        k.set_contents_from_filename(report_filename)
        k.set_acl('public-read')

        return "https://s3.amazonaws.com/%s/%s" % (bucket_name, k.key)
