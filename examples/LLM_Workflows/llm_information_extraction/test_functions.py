import pytest
from pydantic import ValidationError

from .functions import ProductFeedback, validated_feedback


def test_valid_positive_feedback():
    response = """
    {
        "product": "Samsung Galaxy S24",
        "sentiment": "positive",
        "key_points": ["Excellent battery life"]
    }
    """

    result = validated_feedback(response)

    assert isinstance(result, ProductFeedback)
    assert result.product == "Samsung Galaxy S24"
    assert result.sentiment == "positive"


def test_valid_negative_feedback():
    response = """
    {
        "product": "Samsung Galaxy S24",
        "sentiment": "negative",
        "key_points": ["Poor battery life"]
    }
    """

    result = validated_feedback(response)

    assert result.sentiment == "negative"


def test_valid_neutral_feedback():
    response = """
    {
        "product": "Samsung Galaxy S24",
        "sentiment": "neutral",
        "key_points": ["Average performance"]
    }
    """

    result = validated_feedback(response)

    assert result.sentiment == "neutral"


def test_invalid_sentiment():
    response = """
    {
        "product": "Samsung Galaxy S24",
        "sentiment": "excellent",
        "key_points": ["Good battery"]
    }
    """

    with pytest.raises(ValidationError):
        validated_feedback(response)


def test_malformed_json():
    response = '{"product": "Samsung Galaxy S24",'

    with pytest.raises(ValidationError):
        validated_feedback(response)


def test_missing_required_field():
    response = """
    {
        "product": "Samsung Galaxy S24",
        "sentiment": "positive"
    }
    """

    with pytest.raises(ValidationError):
        validated_feedback(response)
