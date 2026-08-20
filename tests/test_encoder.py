from app.encoder import encode


def test_encode_zero():
    assert encode(0) == "0"


def test_encode_single_digit():
    assert encode(1) == "1"


def test_encode_base_boundary():
    assert encode(61) == "z"


def test_encode_next_base():
    assert encode(62) == "10"


def test_encode_large_number():
    assert encode(125) == "21"
