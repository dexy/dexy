from tests.utils import assert_output

def test_bleach_filter():
    assert_output("bleach", "an <script>evil()</script> example", 'an &lt;script&gt;evil()&lt;/script&gt; example')
    assert_output("bleach", "an <script>evil()</script> example", 'an &lt;script&gt;evil()&lt;/script&gt; example', ext=".html")
