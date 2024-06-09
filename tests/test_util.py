from dipin.util import is_class_type


def test_class_detection():
    assert is_class_type(str) is False
    assert is_class_type(int) is False
    assert is_class_type(list) is False
    assert is_class_type(tuple) is False
    assert is_class_type(dict) is False
    assert is_class_type(set) is False
    assert is_class_type(bool) is False
    assert is_class_type(float) is False
    assert is_class_type(type(None)) is False

    class A: ...

    assert is_class_type(A) is True
