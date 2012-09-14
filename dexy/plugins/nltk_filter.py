from dexy.filter import DexyFilter
import json

try:
    import nltk
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class NltkFilter(DexyFilter):
    """
    Base class for NLTK text processing filters. Returns a JSON object with
    various metadata about the input text. Just a demo of what's possible
    rather than useful for now. See http://dexy.it/gallery/examples/nltk/

    """
    ALIASES = ["nltk"]
    INPUT_EXTENSIONS = [".txt"]
    OUTPUT_EXTENSIONS = [".json"]

    @classmethod
    def is_active(klass):
        return AVAILABLE

    def process_text(self, input_text):
        data = {}
        tokens = nltk.word_tokenize(input_text)

        data['wc'] = len(tokens)

        bigram_measures = nltk.collocations.BigramAssocMeasures()
        finder = nltk.collocations.BigramCollocationFinder.from_words(tokens)
        data['collocations'] = finder.nbest(bigram_measures.pmi, 10)

        nltk.download("maxent_treebank_pos_tagger")
        data['pos-tags'] = nltk.pos_tag(tokens)

        return json.dumps(data)
