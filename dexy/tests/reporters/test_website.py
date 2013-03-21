from dexy.reporters.website.classes import Navigation
from dexy.reporters.website.classes import Node

def test_navigation():
   nav = Navigation()
   assert nav.nodes["/"] == nav.root

def test_iter():
    nav = Navigation()
    n2 = Node("/foo", nav.root, [])
    n3 = Node("/foo/bar", n2, [])

    for n in [n2, n3]:
        nav.add_node(n)
