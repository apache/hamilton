# Comparing to LangChain

*Rhetorical question*: which code would you rather maintain, change, and update?

For a side by side comparison see [our docs](https://hamilton.apache.org/code-comparisons/langchain/).

In this directory you'll find a set of equivalent examples.
Most of the files are self-contained, and are prefixed with what
they have inside them.

Files prefixed with `lcel_` are LangChain examples.
Files prefixed with `vanilla_` are what you would write in vanilla Python.
Files prefixed with `hamilton_` are the Apache Hamilton equivalent of the examples.

As you browse the files you'll see that:

1. LangChain's focus is on hiding details and making code terse.
2. Apache Hamilton's focus instead is on making code more readable, maintainable, and importantly customizeable.

## Implications
Don't be surprised that Apache Hamilton's code is "longer" - that's by design. There is
also little abstraction between you, and the underlying libraries with Apache Hamilton.
With LangChain they're abstracted away, so you can't really see easily what's going on
underneath.
