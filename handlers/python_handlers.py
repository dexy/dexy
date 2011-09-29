from dexy.dexy_filter import DexyFilter
from dexy.utils import print_string_diff
from ordereddict import OrderedDict
import json
import os
import re
import shutil
import tarfile
import uuid
import zipfile

class ArchiveHandler(DexyFilter):
    """The archive handler creates .tgz archives of processed files. Create an
    empty/dummy file in the location you wish to have the archive."""
    OUTPUT_EXTENSIONS = [".tgz"]
    ALIASES = ['archive', 'tgz']
    BINARY = True
    FINAL = True

    def process(self):
        if self.artifact.args.has_key('use-short-names'):
            use_short_names = self.artifact.args['use-short-names']
        else:
            use_short_names = False
        af = self.artifact.filepath()
        tar = tarfile.open(af, mode="w:gz")
        for k, a in self.artifact.inputs().items():
            fn = a.filepath()
            if not os.path.exists(fn):
                raise Exception("File %s does not exist!" % fn)
            if use_short_names:
                arcname = a.canonical_filename()
            else:
                arcname = a.long_canonical_filename()
            self.artifact.log.debug("Adding file %s to archive %s." % (fn, af))
            tar.add(fn, arcname=arcname)
        tar.close()

class ZipArchiveHandler(DexyFilter):
    """The archive handler creates .zip archives of the input files. Create an
    empty file in the location you wish to have the archive."""
    OUTPUT_EXTENSIONS = [".zip"]
    ALIASES = ['zip']
    BINARY = True
    FINAL = True

    def process(self):
        if self.artifact.args.has_key('use-short-names'):
            use_short_names = self.artifact.args['use-short-names']
        else:
            use_short_names = False
        af = self.artifact.filepath()
        zf = zipfile.ZipFile(af, mode="w")
        for k, a in self.artifact.inputs().items():
            fn = a.filepath()
            if not os.path.exists(fn):
                raise Exception("File %s does not exist!" % fn)
            if use_short_names:
                arcname = a.canonical_filename()
            else:
                arcname = a.long_canonical_filename()
            self.artifact.log.debug("Adding file %s to archive %s." % (fn, af))
            zf.write(fn, arcname=arcname)
        zf.close()


class TestHandler(DexyFilter):
    """The test handler raises an error if output is not as expected. Handy for
    testing your custom filters or for ensuring that examples in your
    documentation stay correct."""

    ALIASES = ['test']

    def process(self):
        if not self.artifact.controller_args.run_tests:
            print "tests disabled, not running test", self.artifact.key
            self.artifact.data_dict = self.artifact.input_data_dict
            return False

        print "testing", self.artifact.key, "...",
        if not self.artifact.args.has_key('expects'):
            raise "You need to pass 'expects' to the test filter."

        expects = self.artifact.args['expects']
        if expects.startswith("@"):
            expects_file = open(expects.lstrip("@"), "r")
            expects_content = expects_file.read()
            expects_file.close()
        else:
            expects_content = expects
        expects = expects_content

        # TODO handle different types of expectation, e.g. when don't know exact
        # output but can look for type of data returned
        if hasattr(expects, 'items'):
            for k, v in self.artifact.input_data_dict.items():
                msg = print_string_diff(expects[k], v)
                msg += "\nexpected output '%s' (section %s) does not match actual '%s'" % (expects[k], k, v)
                assert expects[k] == v, msg
        else:
            inp = self.artifact.input_text()
            msg = print_string_diff(expects, inp)
            msg += "\nexpected output '%s' does not match actual '%s'" % (expects, inp)
            assert expects == inp, msg

        comment = ""
        if self.artifact.args.has_key("comment"):
           comment = "[%s]" % self.artifact.args['comment']
        print "ok", comment

        # Don't change the output so we can use end result still...
        self.artifact.data_dict = self.artifact.input_data_dict

class CopyHandler(DexyFilter):
    """
    Like 'dexy' filter for binary files. Copies the file without trying to read
    the contents. Hacky!
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['cp']
    BINARY = True
    FINAL = True

    def process(self):
        shutil.copyfile(self.artifact.name, self.artifact.filepath())

class JoinHandler(DexyFilter):
    """
    Takes sectioned code and joins it into a single section. Some filters which
    don't preserve sections will raise an error if they receive multiple
    sections as input, so this forces acknowledgement that sections will be
    lost.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['join']

    def process_dict(self, input_dict):
        return {'1' : self.artifact.input_text()}

class FooterHandler(DexyFilter):
    """
    Adds a footer to file. Looks for a file named _footer.ext where ext is the
    same extension as the file this is being applied to. So _footer.html for a
    file named index.html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['ft', 'footer']

    def process_text(self, input_text):
        footer_key = "_footer%s" % self.artifact.ext
        footer_keys = []
        for k in self.artifact.inputs().keys():
            contains_footer = k.find(footer_key) > -1
            contains_pyg = k.find('|pyg') > 0
            if contains_footer and not contains_pyg:
                footer_keys.append(k)

        if self.artifact.args.has_key('footer'):
            requested_footer = self.artifact.args['footer']
            if not requested_footer in footer_keys:
                raise Exception("requested footer %s not found in %s" %
                                (requested_footer, ", ".join(footer_keys)))
            footer_keys = [requested_footer]

        if len(footer_keys) > 0:
            footer_key = sorted(footer_keys)[-1]
            self.artifact.log.debug("using %s as footer for %s" % (footer_key, self.artifact.key))
            footer_artifact = self.artifact.inputs()[footer_key]
            footer_text = footer_artifact.output_text()
        else:
            print self.artifact.inputs().keys()
            raise Exception("No file matching %s was found to work as a footer." % footer_key)

        return "%s\n%s" % (input_text, footer_text)

class HeaderHandler(DexyFilter):
    """
    Adds a header to file. Looks for a file named _header.ext where ext is the
    same extension as the file this is being applied to. So _header.html for a
    file named index.html.
    """
    INPUT_EXTENSIONS = [".*"]
    OUTPUT_EXTENSIONS = [".*"]
    ALIASES = ['hd', 'header']

    def process_text(self, input_text):
        header_key = "_header%s" % self.artifact.ext
        header_keys = []
        for k in self.artifact.inputs().keys():
            contains_header = k.find(header_key) > -1
            contains_pyg = k.find('|pyg') > 0
            if contains_header and not contains_pyg:
                header_keys.append(k)

        if self.artifact.args.has_key('header'):
            requested_header = self.artifact.args['header']
            if not requested_header in header_keys:
                raise Exception("requested header %s not found in %s" %
                                (requested_header, ", ".join(header_keys)))
            header_keys = [requested_header]

        if len(header_keys) > 0:
            header_key = sorted(header_keys)[-1]
            self.artifact.log.debug("using %s as header for %s" % (header_key, self.artifact.key))
            header_artifact = self.artifact.inputs()[header_key]
            header_text = header_artifact.output_text()
        else:
            raise Exception("No file matching %s was found to work as a header for %s." % (header_key, self.artifact.key))

        return "%s\n%s" % (header_text, input_text)

# TODO implement combined header/footer handler as a shortcut

class HeadHandler(DexyFilter):
    """
    Returns just the first 10 lines of input.
    """
    ALIASES = ['head']
    def process_text(self, input_text):
        return "\n".join(input_text.split("\n")[0:10]) + "\n"

class WordWrapHandler(DexyFilter):
    """
    Wraps text after 79 characters (tries to preserve existing line breaks and
    spaces).
    """
    ALIASES = ['ww', 'wrap']

    #http://code.activestate.com/recipes/148061-one-liner-word-wrap-function/
    def wrap_text(self, text, width):
        """
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        """
        return reduce(lambda line, word, width=width: '%s%s%s' %
                 (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )

    def process_text(self, input_text):
        return self.wrap_text(input_text, 79)

class SplitHtmlHandler(DexyFilter):
    """Splits a HTML page into multiple HTML pages. The original page becomes an
    index page."""
    ALIASES = ['split', 'splithtml']
    INPUT_EXTENSIONS = [".html"]
    OUTPUT_EXTENSIONS = [".html"]
    FINAL = True

    def process(self):
        parent_dir = os.path.dirname(self.artifact.canonical_filename())
        input_text = self.artifact.input_text()

        if input_text.find("<!-- endsplit -->") > 0:
            body, footer = re.split("<!-- endsplit -->", input_text, maxsplit=1)
            sections = re.split("<!-- split \"(.+)\" -->\n", body)
            header = sections[0]

            pages = OrderedDict()
            index_content = None
            for i in range(1, len(sections), 2):
                if sections[i] == 'index':
                    index_content = sections[i+1]
                else:
                    section_name = sections[i]
                    # TODO proper url/filename escaping
                    section_url = section_name.replace(" ","-")

                    filename = "%s.html" % section_url
                    filepath = os.path.join(parent_dir, filename)
                    pages[section_name] = filename

                    artifact = self.artifact.add_additional_artifact(filepath, 'html')
                    artifact.set_data(header + sections[i+1] + footer)
                    artifact.save()

                    self.artifact.log.debug("added key %s to artifact %s ; links to file %s" %
                              (filepath, self.artifact.key, artifact.filename()))

            index_items = []
            for k in sorted(pages.keys()):
                index_items.append("""<li><a href="%s">%s</a></li>""" %
                                   (pages[k], k))

            output_dict = OrderedDict()
            output_dict['header'] = header
            if index_content:
                output_dict['index-page-content'] = index_content
            output_dict['index'] = "<ul>\n%s\n</ul>" % "\n".join(index_items)
            output_dict['footer'] = footer
        else:
            # No endsplit found, do nothing.
            output_dict = self.artifact.input_data_dict
        self.artifact.data_dict = output_dict

class SplitLatexHandler(DexyFilter):
    """Splits a latex doc into multiple latex docs."""
    ALIASES = ['splitlatex']
    INPUT_EXTENSIONS = [".tex"]
    OUTPUT_EXTENSIONS = [".tex"]
    FINAL = True

    def process(self):
        parent_dir = os.path.dirname(self.artifact.canonical_filename())
        input_text = self.artifact.input_text()

        if input_text.find("%% endsplit\n") > 0:
            body, footer = re.split("%% endsplit\n", input_text, maxsplit=1)
            sections = re.split("%% split \"(.+)\"\n", body)
            header = sections[0]

            pages = OrderedDict()
            for i in range(1, len(sections), 2):
                section_name = sections[i]
                # TODO proper url/filename escaping
                section_url = section_name.replace(" ","-")
                source = header + sections[i+1] + footer

                ext = '.tex'

                filename = "%s%s" % (section_url, ext)
                filepath = os.path.join(parent_dir, filename)
                pages[section_name] = filename

                artifact = self.artifact.__class__(filepath)
                artifact.ext = ext
                artifact.binary = False
                artifact.final = True
                artifact.artifacts_dir = self.artifact.artifacts_dir
                artifact.hashstring = str(uuid.uuid4())
                artifact.set_data(source)
                artifact.save()

                self.artifact.inputs()[filepath] = artifact
                self.artifact.log.debug("added key %s to artifact %s ; links to file %s" %
                          (filepath, self.artifact.key, artifact.filename()))

            index_items = []
            for k in sorted(pages.keys()):
                index_items.append("""<li><a href="%s">%s</a></li>""" %
                                   (pages[k], k))

        output_dict = self.artifact.input_data_dict
        self.artifact.data_dict = output_dict

class PrettyPrintJsonFilter(DexyFilter):
    ALIASES = ['ppjson']
    OUTPUT_EXTENSIONS = ['.json']

    def process_text(self, input_text):
        json_content = json.loads(input_text)
        return json.dumps(json_content, sort_keys=True, indent=4)

class SillyHandler(DexyFilter):
    ALIASES =['silly']

    def process_text(self, input_text):
        return "you said: '%s'\n that's silly!\n" % input_text
