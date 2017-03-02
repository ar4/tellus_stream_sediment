import pytest
import numpy as np

def test_find_upstream(test_upstream):
    if test_upstream == None:
        raise TypeError('must specify --upstream')
    output = np.load(test_upstream)
    assert(output[0] == [(1,0), (0,0)])
    assert(output[1] == [(3,0), (2,0), (1,0), (0,0)])
