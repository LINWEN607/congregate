from congregate.helpers.jsondiff import Comparator

engine = Comparator()

def test_list_comparison():
    list_one = [{"Hello": "World"}, 2, 3, 4, 5]
    list_two = [5, 4, 3, 2, {"Hello": "World"}, 0]
    # list_two = [1, 2, 3, 4, 5]
    
    # expected = {0: {'+++': 5, '---': 1}, 1:...4}, 4: {'+++': 1, '---': 5}}
    expected = {0: {u'+++': 0}}
    actual = engine._compare_arrays(list_one, list_two)

    assert expected == actual

def test_list_comparison_long_list():
    list_one = [{"Hello": "World"}, 2, 3, 4, 5]
    list_two = [5, 4, 3, 2, {"Hello": "World"}, 0, 10, 15]
    # list_two = [1, 2, 3, 4, 5]
    
    # expected = {0: {'+++': 5, '---': 1}, 1:...4}, 4: {'+++': 1, '---': 5}}
    expected = {0: {u'+++': 0}, 5: {u'+++': 10}, 6: {u'+++': 15}}
    actual = engine._compare_arrays(list_one, list_two)

    assert expected == actual
