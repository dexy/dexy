from dexy.filters.api_filters import ApiFilter
import codecs
import datetime
import json
import requests
import re
import os

class TenderappFilter(ApiFilter):
    """
    Post content to a knowledge base page or a discussion in Tenderapp.

    Specify your API key and the base url for YOUR tenderapp site in a
    ~/.dexyapis JSON file under the key tenderapp, for example:

    {
        "tenderapp" : {
            "api-key" : "abd123....",
            "url" : "http://api.tenderapp.com/dexy"
        }
    }

    You can also specify api-key and url on a per-project basis, just add a
    local file named .dexyapis to the dexy project root and this will override
    your main settings for that directory.

    You will need to create a configuration file for each document you want to
    upload. By default this file should be named tenderapp.json but you can
    change this in your .dexy configuration by setting the
    "tenderapp-config-file" attribute to the filename you wish to use. This is
    necessary if you wish to have more than 1 config document in a directory.

    ######################
    Knowledge Base Articles
    ######################

    In the tenderapp.json file for the document you wish to upload, specify at
    least 'title' and 'section', for example:

    {
        "title" : "My Article Title",
        "section" : "the-section-permalink"
    }

    The section can be either the section permalink or the section name. The
    filter will look up the corresponding section ID for you.

    You can also provide "permalink" and "keywords" arguments, see the
    tenderapp docs: http://help.tenderapp.com/kb/api/kb-articles

    By default, this will create a new, draft document. The first time you
    upload a document, tenderapp will generate a unique URL for your new
    document and the filter will update your tenderapp.json file with this URL.

    To indicate that you are ready to publish a document rather than save it as
    a draft, set the 'publish' key to true.

    {
        "title" : "My Article Title",
        "section" : "the-section-permalink",
        "publish" : true,
        "href" : "http://api.tenderapp.com/dexy/faqs/12345"
    }

    ########################
    Discussions and Comments
    ########################

    You can create a new discussion, or comment on an existing discussion.



    """
    ALIASES = ['tenderapp']
    API_KEY_NAME = 'tenderapp'
    INPUT_EXTENSIONS = [".md", ".markdown", ".html"]
    OUTPUT_EXTENSIONS = [".json"] # we output the json response from the API, maybe better to output orig content for chaining
    DOCUMENT_API_CONFIG_FILE = "tenderapp.json"
    DOCUMENT_API_CONFIG_FILE_KEY = "tenderapp-config-file"

    @classmethod
    def load_if_valid_json(klass, text):
        """
        Make error message more useful when tenderapp does not return JSON.
        """
        try:
            return json.loads(text)
        except ValueError:
            raise Exception("tenderapp API returned non-JSON content, an error has occurred: %s" % text)

    @classmethod
    def comments_from_href(klass, comments_href):
        headers = klass.default_headers()
        result = requests.get(comments_href, headers=headers)
        result_json = klass.load_if_valid_json(result.text)
        if result_json.has_key('comments'):
            return result_json['comments']
        else:
            return []

    def process_text(self, input_text):
        document_config = self.read_document_config()
        document_config['via'] = 'dexy'

        if document_config.has_key('section'):
            # this is a knowledge base article
            result = self.upload_kbase_article(document_config, input_text)
        elif document_config.has_key('href') and "/faqs/" in document_config['href']:
            # this is an existing knowledge base article
            result = self.upload_kbase_article(document_config, input_text)
        elif document_config.has_key('category'):
            # this is a new discussion
            result = self.start_new_discussion(document_config, input_text)
        elif document_config.has_key('discussion'):
            # this is an existing discussion
            result = self.comment_on_discussion(document_config, input_text)
        else:
            raise Exception("not enough information to upload %s to tenderapp" % self.artifact.key)

        return result

    def upload_kbase_article(self, document_config, input_text):
        headers = self.default_headers(json=True)

        # Make a copy since we are going to add/remove some items for passing to API
        payload = document_config.copy()

        if payload.has_key('publish'):
            publish = payload['publish']
            del payload['publish']
            if publish and not payload.has_key('published_at'):
                timestamp = datetime.datetime.now().isoformat()
                payload['published_at'] = timestamp
                document_config['published_at'] = timestamp

        if payload.has_key('section'):
            del payload['section']
        payload['body'] = input_text

        if payload.has_key('href'):
            # This kb article already exists, we want to modify it.
            article_href = payload['href']
            del payload['href']
            result = requests.put(article_href, data=json.dumps(payload), headers=headers)
            self.load_if_valid_json(result.text) # make sure we got valid response
        else:
            # This is a new kb article.
            # Determine section href from permalink
            section_permalink = document_config['section']
            section_href = self.section_href(section_permalink)
            if not section_href:
                raise Exception("Can't find knowledge base section matching '%s'." % section_permalink)

            # Use section href to construct url
            url = "%s/faqs" % section_href

            if not document_config.has_key('title'):
                raise Exception("You must provide a title.")

            result = requests.post(url, data=json.dumps(payload), headers=headers)
            result_json = self.load_if_valid_json(result.text)

            # Save href and permalink for next time
            del document_config['section']
            document_config['href'] = result_json['href']
            document_config['permalink'] = result_json['permalink']

        del document_config['via']
        self.save_document_config(document_config)
        return result.text

    def start_new_discussion(self, document_config, input_text):
        if document_config.has_key('href'):
            raise Exception("Discussion %s has already been uploaded. Please disable this document." % document_config['title'])

        category_permalink = document_config['category']
        category_href = self.category_href(category_permalink)
        if not category_href:
            raise Exception("Can't find section matching '%s'." % category_permalink)

        url = "%s/discussions" % self.category_href(category_permalink)
        headers = self.default_headers(json=True)

        payload = document_config.copy()
        payload['body'] = input_text
        result = requests.post(url, data=json.dumps(payload), headers=headers)
        result_json = self.load_if_valid_json(result.text)

        print "You can view your new discussion at", result_json['html_href']
        print "To comment on this discussion, add \"discussion\" : \"%s\" to your .dexy config for comments" % result_json['href']

        document_config['href'] = result_json['href']
        del document_config['via']
        self.save_document_config(document_config)
        return result.text

    def comment_on_discussion(self, document_config, input_text):
        if document_config.has_key('href'):
            raise Exception("This comment has already been uploaded. Please disable this document.")
        url = "%s/comments" % document_config['discussion']
        headers = self.default_headers(json=True)

        payload = document_config.copy()
        payload['body'] = input_text
        del payload['discussion']

        result = requests.post(url, data=json.dumps(payload), headers=headers)
        result_json = self.load_if_valid_json(result.text)
        print "You can view your new comment at", result_json['html_href']+"#comment_%s" % result_json['last_comment_id']
        document_config['href'] = result_json['href']
        del document_config['via']
        self.save_document_config(document_config)
        return result.text

    @classmethod
    def docmd_categories(klass):
        """
        Return available categories for discussions.
        """
        categories = klass.categories()
        if len(categories) == 0:
            print "No categories found for %s" % klass.read_url()
        else:
            headers = ["permalink", "summary"]
            print "Categories found for %s" % klass.read_url()
            print "\t".join(headers)
            for category in categories:
                print "\t".join(category.setdefault(h, "") for h in headers)

    @classmethod
    def docmd_sections(klass):
        """
        Return available sections for kb articles.
        """
        sections = klass.sections()
        if len(sections) == 0:
            print "No sections found for %s" % klass.read_url()
        else:
            headers = ["permalink", "title"]
            print "Sections found for %s" % klass.read_url()
            print "\t".join(headers)
            for section in sections:
                print "\t".join(section.setdefault(h, "") for h in headers)

    @classmethod
    def docmd_delete_discussion(klass, discussionid):
        """
        Permanently deletes a discussion from the remote server.
        """
        if str(discussionid).startswith("http"):
            url = discussionid
        else:
            url = "%s/discussions/%s" % (klass.read_url(), discussionid)
        result = requests.delete(url, headers=klass.default_headers())
        if re.match("^\s*$", result.text):
            print "discussion %s deleted" % url
        else:
            print result.text

    @classmethod
    def docmd_delete_article(klass, articleid):
        """
        Permanently deletes a kb article from the remote server.
        """
        # TODO ask "are you sure"
        url = "%s/faqs/%s" % (klass.read_url(), articleid)
        result = requests.delete(url, headers=klass.default_headers())
        print result.text

    @classmethod
    def docmd_discussions(klass):
        """
        Returns list of hrefs of discussions for the current user.
        """
        discussions = klass.discussions_for_current_user()
        if len(discussions) == 0:
            print "No discussions found for current user at", klass.read_url()
        else:
            print "Discussions found for current user at", klass.read_url()
            print "\n".join("%s [%s] (%s)" % (d['href'], d['html_href'], d['title']) for d in discussions)

    @classmethod
    def docmd_articles(klass):
        """
        Returns list of kb articles
        """
        articles = klass.articles()
        if len(articles) == 0:
            print "No articles found at", klass.read_url()
        else:
            headers = ["href", "title", "html_href"]
            print "Articles found at", klass.read_url()
            print "\t".join(headers)
            for article in articles:
                print "\t".join(article.setdefault(h, "") for h in headers)

    @classmethod
    def docmd_populate(klass):
        """
        Populates a directory with entries for each discussion found for the user.
        """
        categories = klass.categories()
        category_permalinks = "\n".join(c['permalink'] for c in categories)

        create_discussion_dir = "create-discussion-example"
        if not os.path.exists(create_discussion_dir):
            os.mkdir(create_discussion_dir)
            print "created directory", create_discussion_dir
            os.chdir(create_discussion_dir)

            with codecs.open("discuss-example.md", "w", encoding="utf-8") as f:
                f.write("This is an example of a markdown file you can use to create a new discussion.")

            with codecs.open(".dexy", "w", encoding="utf-8") as f:
                config = {
                        "discuss-*.md|tenderapp" : { "disabled" : True, "inputs" : ["tenderapp.json"] },
                        "discuss-*.md|markdown" : {}
                        }
                json.dump(config, f, sort_keys=True, indent=4)

            with codecs.open("tenderapp.json", "w", encoding="utf-8") as f:
                config = {
                        "category" : "TODO",
                        "title" : "TODO"
                        }
                json.dump(config, f, sort_keys=True, indent=4)

            with codecs.open("README", "w", encoding="utf-8") as f:
                f.write("""This directory is all set up so you can create a new discussion.

Just set disabled to False or remove that line from the .dexy file to enable.

Choose the category which your discussion should go into. Available options are

%s

Remember that discussions can only be posted once.
""" % category_permalinks)

            os.chdir("..")

        create_article_dir = "create-kb-article-example"
        if not os.path.exists(create_article_dir):
            os.mkdir(create_article_dir)
            print "created directory", create_article_dir
            os.chdir(create_article_dir)

            with codecs.open("kb-example.md", "w", encoding="utf-8") as f:
                f.write("This is an example of a markdown file you can use to create a new knowledgebase article.")

            with codecs.open(".dexy", "w", encoding="utf-8") as f:
                config = {
                        "kb-*.md|tenderapp" : { "disabled" : True, "inputs" : ["tenderapp.json"] },
                        "kb-*.md|markdown" : {}
                        }
                json.dump(config, f, sort_keys=True, indent=4)

            with codecs.open("tenderapp.json", "w", encoding="utf-8") as f:
                config = {
                        "section" : "TODO",
                        "title" : "TODO",
                        "keywords" : "",
                        "publish" : False
                        }
                json.dump(config, f, sort_keys=True, indent=4)

            os.chdir("..")

        for article in klass.articles():
            article_dir = "kb-article-%s" % article['permalink']
            if not os.path.exists(article_dir):
                os.mkdir(article_dir)
                print "created directory", article_dir
                os.chdir(article_dir)

                with codecs.open("info.json", "w", encoding="utf-8") as f:
                    json.dump(article, f, sort_keys=True, indent=4)

                with codecs.open("kb-article.md", "w", encoding="utf-8") as f:
                    f.write(article['body'])

                with codecs.open(".dexy", "w", encoding="utf-8") as f:
                    config = {
                            "kb-*.md|tenderapp" : {
                                "disabled" : True,
                                "inputs" : ["tenderapp.json"]
                            },
                            "kb-*.md|markdown" : {}
                        }
                    json.dump(config, f, sort_keys=True, indent=4)

                with codecs.open("tenderapp.json", "w", encoding="utf-8") as f:
                    config = {
                            "title" : article['title'],
                            "permalink" : article['permalink'],
                            "keywords" : article['keywords'],
                            "href" : article['href'],
                            }
                    if article['published_at'][0:4] == "2028":
                        config['publish'] = False
                    else:
                        config['published_at'] = article['published_at']

                    json.dump(config, f, sort_keys=True, indent=4)

                os.chdir("..")

        for discussion in klass.discussions_for_current_user():
            discussion_dir = "%06d-%s" % (discussion['number'], discussion['permalink'][0:50])
            if len(discussion['permalink']) > 50:
                discussion_dir += "..."

            new_dir = False
            if not os.path.exists(discussion_dir):
                new_dir = True
                os.mkdir(discussion_dir)
                print "created directory", discussion_dir

            os.chdir(discussion_dir)

            if new_dir:
                # Store the API info for the discussion for future reference
                with codecs.open("info.json", "w", encoding="utf-8") as f:
                    json.dump(discussion, f, sort_keys=True, indent=4)

                with codecs.open(".dexy", "w", encoding="utf-8") as f:
                    config = {
                            "comment-*.md|tenderapp" : {
                                "disabled" : True,
                                "discussion" : discussion['href'],
                                "inputs" : ["tenderapp.json"]
                            },
                            "comment-*.md|markdown" : {}
                        }
                    json.dump(config, f, sort_keys=True, indent=4)

                with codecs.open("comment-example.md", "w") as f:
                    f.write("""
This is content for a new comment. If you enable the comment-*.md pattern, this
comment will be posted to the discussion %s
""" % discussion['html_href'])
            os.chdir("..")

    @classmethod
    def sections(klass):
        """
        Retrieve a dict with information about knowledge base sections defined in tenderapp
        """
        headers = klass.default_headers()
        url = "%s/sections" % klass.read_url()
        result = requests.get(url, headers=headers)
        return klass.load_if_valid_json(result.text)['sections']

    @classmethod
    def categories(klass):
        """
        Retrieve a dict with information about discussion categories defined in tenderapp
        """
        headers = klass.default_headers()
        url = "%s/categories" % klass.read_url()
        result = requests.get(url, headers=headers)
        return klass.load_if_valid_json(result.text)['categories']

    @classmethod
    def articles(klass):
        """
        Retrieves list of knowledge base articles
        """
        headers = klass.default_headers()
        url = "%s/faqs" % klass.read_url()
        result = requests.get(url, headers=headers)
        return klass.load_if_valid_json(result.text)['faqs']

    @classmethod
    def discussions_for_current_user(klass):
        headers = klass.default_headers()
        url = "%s/discussions?user_current=1" % klass.read_url()
        result = requests.get(url, headers=headers)
        return json.loads(result.text)['discussions']

    def section_href(self, section_name):
        """
        Fetch the href (including the section id) corresponding to a section name or permanlink
        """
        sections = self.sections()
        href = None
        for section in sections:
            if section['title'] == section_name or section['permalink'] == section_name:
                href = section['href']
            if href:
                break
        return href

    def category_href(self, category_name):
        """
        Fetch the href (including the category id) corresponding to a category name or permanlink
        """
        categories = self.categories()
        href = None
        for category in categories:
            if category['name'] == category_name or category['permalink'] == category_name:
                href = category['href']
            if href:
                break
        return href

    @classmethod
    def default_headers(klass, json=False):
        headers = {
                "Accept" : "application/vnd.tender-v1+json",
                "X-Tender-Auth" :  klass.read_api_key()
                }
        if json:
            headers['Content-Type'] = "application/json"
        return headers
