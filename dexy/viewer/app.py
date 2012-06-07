from dexy.constants import Constants
import dexy.introspect
import web
import os

ARTIFACT_CLASS = dexy.utils.artifact_class()

urls = (
        '/doc/(.*)', 'document',
        '/raw/(.*)', 'raw',
        '/snip/(.*)/(.*)', 'snippet',
        '/(.*)/(.*)', 'grep',
        '/(.*)', 'grep'
        )

render = web.template.render(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates'))

def wrap_content(content, ext):
    # Add other extensions here with special handling needs. Default is wrapped in <pre> tags.
    if ext == ".html":
        return content
    else:
        return "<pre>\n%s\n</pre>" % content

class raw:
    def GET(self, doc_websafe_key):
        db = dexy.utils.get_db(Constants.DEFAULT_DBCLASS)
        doc_key = doc_websafe_key.replace("--", "/")
        row = db.query_unique_key(doc_key)[0]
        artifact = ARTIFACT_CLASS.retrieve(row['hashstring'])

        if artifact.binary_output:
            return artifact.binary_data
        else:
            return artifact.output_text()

class document:
    def GET(self, doc_websafe_key):
        db = dexy.utils.get_db(Constants.DEFAULT_DBCLASS)
        doc_key = doc_websafe_key.replace("--", "/")
        row = db.query_unique_key(doc_key)[0]
        artifact = ARTIFACT_CLASS.retrieve(row['hashstring'])

        if artifact.ext in (".png", ".jpg"): # Add any other image formats here.
            return """<img title="%s" src="/raw/%s" />""" % (artifact.key, doc_websafe_key)
        elif artifact.binary_output:
            return """<a href="/raw/%s">download</a>""" % doc_websafe_key
        else:
            return wrap_content(artifact.output_text(), artifact.ext)

class snippet:
    def GET(self, doc_websafe_key, snippet_key):
        db = dexy.utils.get_db(Constants.DEFAULT_DBCLASS)
        doc_key = doc_websafe_key.replace("--", "/")
        row = db.query_unique_key(doc_key)[0]
        artifact = ARTIFACT_CLASS.retrieve(row['hashstring'])
        return wrap_content(artifact[snippet_key], artifact.ext)

class grep:
    def GET(self, expr, keyexpr=None):
        db = dexy.utils.get_db(Constants.DEFAULT_DBCLASS)
        if not expr:
            # Show first 20 records
            rows = db.all(20)
        else:
            # Show whatever matches the query text using sql like %expr% matching
            rows = db.query_like("%%%s%%" % expr)

        artifacts = []
        for row in rows:
            artifact = ARTIFACT_CLASS.retrieve(row['hashstring'])
            artifact.batch_id = row['batch_id']
            artifacts.append(artifact)

        return render.grep(artifacts, expr, keyexpr)

app = web.application(urls, globals())

if __name__ == "__main__":
    app.run()

import dexy.utils
