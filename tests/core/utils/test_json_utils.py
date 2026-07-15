import pytest
from core.utils.json_utils import extract_and_validate_json, extract_json
from pydantic import BaseModel


class DummySchema(BaseModel):
    name: str
    val: int


def test_extract_json_dict_input():
    d = {"name": "test"}
    assert extract_json(d) == d


def test_extract_json_empty_text():
    assert extract_json("") == {}
    assert extract_json(None) == {}


def test_extract_json_raw_valid():
    assert extract_json('{"name": "hello", "val": 1}') == {"name": "hello", "val": 1}


def test_extract_json_markdown():
    text = 'Here is the result:\n```json\n{\n  "name": "hello",\n  "val": 1\n}\n```\nHope it helps!'
    assert extract_json(text) == {"name": "hello", "val": 1}


def test_extract_json_braces():
    text = 'Some random text {"name": "hello", "val": 1} more random text'
    assert extract_json(text) == {"name": "hello", "val": 1}


def test_extract_json_invalid():
    assert extract_json("No json here") == {}
    assert extract_json("{broken json") == {}


def test_extract_and_validate_json():
    # Valid
    res = extract_and_validate_json('{"name": "hello", "val": 1}', DummySchema)
    assert res.name == "hello"
    assert res.val == 1

    # Invalid JSON
    with pytest.raises(Exception):
        extract_and_validate_json("no json", DummySchema)
