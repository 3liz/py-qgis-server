
from pyqgisserver.utils.lru import lrucache


def test_lru_ordering():
    """ Test lru cache
    """
    c = lrucache(3)

    c['k1'] = 'foo'
    c['k2'] = 'bar'
    c['k3'] = 'baz'

    assert tuple(c.keys()) == ('k3','k2','k1')

    # Access key and test reordering
    k = c['k1']
    assert tuple(c.keys()) == ('k1','k3','k2')

    # Test size keeping
    c['k4'] = 'foo'

    assert len(c) == 3
    assert tuple(c.keys()) == ('k4','k1','k3')



