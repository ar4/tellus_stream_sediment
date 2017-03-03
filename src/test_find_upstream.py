import pytest
import numpy as np

def test_find_upstream(test_upstream):
    if test_upstream == None:
        raise TypeError('must specify --upstream')
    output = np.load(test_upstream)
    assert(output[0] == [(2,1), (1,1)])
    assert(output[1] == [(4,1), (3,1), (2,1), (1,1)])
