import functions

from hamilton import driver


def build_driver():
    """Build the Hamilton driver using our extraction functions."""

    return driver.Builder().with_modules(functions).build()


if __name__ == "__main__":
    dr = build_driver()

    review = (
        "The battery life of the Samsung Galaxy S24 is excellent, "
        "but the phone gets hot while gaming. "
        "Overall, I am happy with the purchase."
    )

    result = dr.execute(
        ["validated_feedback"],
        inputs={"review_text": review},
    )

    print("\nExtracted Product Feedback:")
    print(result["validated_feedback"].model_dump_json(indent=2))
