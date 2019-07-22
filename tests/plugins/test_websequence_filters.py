from tests.utils import assert_output_matches
from mock import patch, call
from io import StringIO


## See http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch for
## why this mock applies to dexy.filters.websequence not urllib2
#@patch("dexy.filters.websequence.urlopen",
#       side_effect=[StringIO("?png=whereToGo"), StringIO("mock_result")])
#def test_websequence_svg(mocked_urlopen):
#    assert_output_matches("wsd", "Sender->Receiver", "mock_result", ext=".wsd")
#    print(mocked_urlopen.call_args_list)
#    assert mocked_urlopen.call_args_list[0] == call(
#        "http://www.websequencediagrams.com/index.php",
#        'message=Sender-%3EReceiver&style=default&apiVersion=1')
#    assert mocked_urlopen.call_args_list[1] == call(
#        "http://www.websequencediagrams.com/?png=whereToGo")
