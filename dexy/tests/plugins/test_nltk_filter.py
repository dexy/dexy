from dexy.tests.utils import runfilter
import json

BEOWULF = """BEOWULF

PRELUDE OF THE FOUNDER OF THE DANISH HOUSE

LO, praise of the prowess of people-kings
of spear-armed Danes, in days long sped,
we have heard, and what honor the athelings won!
Oft Scyld the Scefing from squadroned foes,
"""

def test_nltk_filter():
    with runfilter("nltk", BEOWULF) as doc:
        output = json.loads(doc.output().as_text())

        assert "wc" in output.keys()
        assert "collocations" in output.keys()
        assert "pos-tags" in output.keys()

        assert output['wc'] == 45
        assert ["DANISH", "HOUSE"] in output['collocations']
