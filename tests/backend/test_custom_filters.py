import pytest
from animetix.templatetags.custom_filters import cdn_url, blur_cdn_url, mul, sub, modulo

def test_mul_filter():
    assert mul(10, 2) == 20
    assert mul("a", 2) == 0

def test_sub_filter():
    assert sub(10, 2) == 8
    assert sub("a", 2) == 0

def test_modulo_filter():
    assert modulo(10, 3) == 1
    assert modulo(10, 0) == 0

def test_cdn_url_filter():
    res = cdn_url("http://test.com/img.jpg")
    assert "/cdn-proxy/" in res
    assert cdn_url(None) == ""

def test_blur_cdn_url_filter():
    res = blur_cdn_url("http://test.com/img.jpg")
    assert "/cdn-proxy/" in res
    assert blur_cdn_url(None) == ""
