def invoke_chain_with_fallback(topic: str) -> str:
    """Invoke a chain with a fallback to Anthropic chain.

    Attempts to invoke a chain using `invoke_chain` and falls back to
    `invoke_anthropic_chain` if any exception is raised.

    Args:
        topic: The topic to pass to the chain invocation.

    Returns:
        The result from the successful chain invocation.
    """
    try:
        return invoke_chain(topic)  # noqa: F821
    except Exception:
        return invoke_anthropic_chain(topic)  # noqa: F821

if __name__ == '__main__':
    print(invoke_chain_with_fallback("ice cream"))
