from dexy.topsort import topsort
from dexy.topsort import CycleError

def test_topological_sort_valid():
    assert topsort([(1,2),(1,3),(3,2)]) == [1,3,2]
    assert topsort([(2,1),(2,1)]) == [2,1]
    assert topsort([(1,0),(1,2),(1,3),(3,2)]) == [1,0,3,2]

def test_topological_sort_circular_references():
    try:
        topsort([(1,2),(2,1)])
        assert False
    except CycleError as e:
        print e
        assert True

    try:
        topsort([(0,1),(1,2),(2,1)])
        assert False
    except CycleError as e:
        print e
        assert True
