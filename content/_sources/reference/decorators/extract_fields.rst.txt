=======================
extract_fields
=======================
This works on a function that outputs a dictionary, that we want to extract the fields from and make them individually
available for consumption. So it expands a single function into `n functions`, each of which take in the output
dictionary and output a specific field as named in the ``extract_fields`` decorator.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import extract_columns

    @function_modifiers.extract_fields(
        {'X_train': np.ndarray, 'X_test': np.ndarray, 'y_train': np.ndarray, 'y_test': np.ndarray})
    def train_test_split_func(feature_matrix: np.ndarray,
                              target: np.ndarray,
                              test_size_fraction: float,
                              shuffle_train_test_split: bool) -> Dict[str, np.ndarray]:
        ...
        return {'X_train': ... }


The input to the decorator is a dictionary of ``field_name`` to ``field_type`` -- this information is used for static
compilation to ensure downstream uses are expecting the right type.


----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.extract_fields
   :special-members: __init__
