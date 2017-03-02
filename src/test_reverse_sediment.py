import pytest
import numpy as np
import gdalnumeric

def compare(output, expected, atol=0.05):
    return np.allclose(np.transpose(output)[0], expected, atol=atol, equal_nan=True)

def test_all_ones(test_na):
    if test_na == None:
        raise TypeError('must specify --na')
    output = gdalnumeric.LoadFile(test_na)
    assert(compare(output, [1.0,1.0,1.0,1.0,np.nan]))

def test_first_measurement_is_zero(test_mg):
    if test_mg == None:
        raise TypeError('must specify --mg')
    output = gdalnumeric.LoadFile(test_mg)
    assert(compare(output, [0.0,0.0,1.0,1.0,np.nan]))

def test_no_increase(test_al):
    if test_al == None:
        raise TypeError('must specify --al')
    output = gdalnumeric.LoadFile(test_al)
    assert(compare(output, [1.0,1.0,0.0,0.0,np.nan]))

def test_one_nan(test_si):
    if test_si == None:
        raise TypeError('must specify --si')
    output = gdalnumeric.LoadFile(test_si)
    assert(compare(output, [1.0,1.0,1.0,1.0,np.nan]))

def test_all_zeros(test_p2):
    if test_p2 == None:
        raise TypeError('must specify --p2')
    output = gdalnumeric.LoadFile(test_p2)
    assert(compare(output, [0.0,0.0,0.0,0.0,np.nan]))

def test_all_nan(test_s):
    if test_s == None:
        raise TypeError('must specify --s_')
    output = gdalnumeric.LoadFile(test_s)
    assert(compare(output, [np.nan,np.nan,np.nan,np.nan,np.nan]))
