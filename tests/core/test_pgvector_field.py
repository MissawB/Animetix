from animetix.models import PGVectorField


def test_pgvector_field_serialization():
    field = PGVectorField()
    # Test to_python/from_db_value parsing
    assert field.to_python("[0.1, 0.2, 0.3]") == [0.1, 0.2, 0.3]
    assert field.from_db_value("[0.5, 0.6]", None, None) == [0.5, 0.6]

    # Test get_prep_value formatting (which converts list to string representation)
    assert field.get_prep_value([0.1, 0.2]) == "[0.1,0.2]"
