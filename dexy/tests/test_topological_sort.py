from dexy.topological_sort import topological_sort

def test_basic():
    assert topological_sort([1,2,3], [(1,2),(1,3),(3,2)]) == [1,3,2]
    assert topological_sort([1,2], [(2,1),(2,1)]) == [2,1]
    assert topological_sort([0,1,2,3], [(1,0),(1,2),(1,3),(3,2)]) == [1,3,2,0]

    assert not topological_sort([1,2], [(1,2),(2,1)])
    assert not topological_sort([0,1,2], [(0,1),(1,2),(2,1)])
