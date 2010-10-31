try:
    from ansi2html import Ansi2HTMLConverter
    from pynliner import Pynliner
    from BeautifulSoup import BeautifulSoup
    def ansi_output_to_html(ansi_text):
        converter = Ansi2HTMLConverter()
        html = converter.convert(ansi_text)

        p = Pynliner()
        p.from_string(html)
        html_with_css_inline = p.run()
    
        # Ansi2HTMLConverter returns a complete HTML document, we just want body
        doc = BeautifulSoup(html_with_css_inline)
        return doc.body.renderContents()

except ImportError as e:
   print e
   print "ansi_output_to_html not available"

