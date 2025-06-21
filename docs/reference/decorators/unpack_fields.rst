=======================
unpack_fields
=======================
This decorator works on a function that outputs a tuple and unpacks its elements to make them individually available for consumption. Essentially, it expands the original function into n separate functions, each of which takes the original output tuple and, in return, outputs a specific field based on the index supplied to the ``unpack_fields`` decorator.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import unpack_fields

    @unpack_fields('X_train', 'X_test', 'y_train', 'y_test')
    def train_test_split_func(
        feature_matrix: np.ndarray,
        target: np.ndarray,
        test_size_fraction: float,
        shuffle_train_test_split: bool,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        ...  # Calculate the train-test split
        return X_train, X_test, y_train, y_test


The arguments to the decorator not only represent the names of the resulting fields but also determine their position in the output tuple. This means you can choose to unpack a subset of the fields or declare an indeterminate number of fields — as long as the number of requested fields does not exceed the number of elements in the output tuple.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import unpack_fields

    @unpack_fields('X_train', 'X_test', 'y_train', 'y_test')
    def train_test_split_func(
        feature_matrix: np.ndarray,
        target: np.ndarray,
        test_size_fraction: float,
        shuffle_train_test_split: bool,
    ) -> Tuple[np.ndarray, ...]:  # indeterminate number of fields
        ...  # Calculate the train-test split
        return X_train, X_test, y_train, y_test

----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.unpack_fields
   :special-members: __init__
