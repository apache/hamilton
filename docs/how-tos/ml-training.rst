===============================
Model training
===============================

As Apache Hamilton is a generic library for representing dataflows in pandas, it can be used for a wide array of tasks.
One of the more common applications is using hamilton for training, testing, and executing machine learning models,
all the way from feature-engineering through training and inference.

The following two examples show how to use Apache Hamilton to model an entire ML pipeline:

1. A `classification pipeline <https://github.com/apache/hamilton/tree/main/examples/model_examples/scikit-learn>`_ for the iris dataset using scikit-learn
2. An `implementation <https://github.com/apache/hamilton/tree/main/examples/model_examples/time-series>`_ of the m5 kaggle competition to do time-series forecasting on unit sales for using Walmart data.

The goal of these is to get you comfortable with building out ML pipelines using hamilton, potentially giving you inspiration/templates from which you can get started.
