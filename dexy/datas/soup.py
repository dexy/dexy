from dexy.data import Generic
try:
    from bs4 import BeautifulSoup
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

class BeautifulSoupData(Generic):
    """
    Allow querying HTML using BeautifulSoup.
    """
    aliases = ['bs4']

    def soup(self):
        """
        Returns a BeautifulSoup object initialized with contents.
        """
        if not hasattr(self, '_soup'):
            self._soup = BeautifulSoup(self.data())
        return self._soup

    def select(self, query):
        """
        Returns a list of results from a CSS query.
        """
        return self.soup().select(query) 

    def select_one(self, query):
        """
        Returns a single result from a CSS query. Result must be unique.
        """
        selects = self.select(query)
        if not len(selects) == 1:
            raise Exception("Select on '%s' was not unique.")
        return selects[0]

    def __getitem__(self, key):
        return self.select_one(key)
