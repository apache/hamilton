# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import numpy as np
import scipy.stats as stats
from sklearn.metrics import get_scorer

from hamilton.function_modifiers import config


def val_score(scorer_name: str, y_validation: np.ndarray, val_pred: np.ndarray) -> float:
    """Compute the metric `scorer_name` from scikit-learn for the validation predictions"""
    scorer = get_scorer(scorer_name)
    score = np.abs(scorer._score_func(y_validation, val_pred))
    return score


def bootstrap_metric_sample(
    scorer_name: str, y_validation: np.ndarray, bootstrap_iter: int = 1000
) -> np.ndarray:
    """Bootstrap the `scorer_name` metric for a number of `bootstrap_iter` iterations
    based on the empirical label distribution of `y_validation`
    """
    scorer = get_scorer(scorer_name)

    n_examples = y_validation.shape[0]
    unique_val, count_val = np.unique(y_validation, return_counts=True)

    scores = []
    for _ in range(bootstrap_iter):
        random_draw = np.random.choice(unique_val, n_examples, p=count_val / count_val.sum())

        score = np.abs(scorer._score_func(y_validation, random_draw))
        scores.append(score)

    return np.asarray(scores)


def statistical_ttest_one_sample(
    bootstrap_metric_sample: np.ndarray,
    val_score: float,
    higher_is_better: bool = True,
) -> dict:
    """Since we are dealing with scores, the model metric is always 'higher is better'"""

    if higher_is_better:
        sample_hypothesis = "less"
    else:
        sample_hypothesis = "greater"

    statistic, pvalue = stats.ttest_1samp(
        bootstrap_metric_sample, val_score, alternative=sample_hypothesis
    )
    return dict(test="one_sample_ttest", stat=statistic, pvalue=pvalue)


@config.when_in(task=["continuous_regression", "binary_classification"])
def statistical_association__pearsonr(y_validation: np.ndarray, val_pred: np.ndarray) -> dict:
    """measure the statistical association between true labels and predicted labels"""

    # for the binary case, Cramer's V is equivalent to Pearson's R (phi coefficient estimation)
    # ref: https://blog.zenggyu.com/en/posts/2019-06-11-a-brief-introduction-to-various-correlation-coefficients-and-when-to-use-which/index.html
    statistic, pvalue = stats.pearsonr(y_validation, val_pred)

    return dict(
        test="pearsonr",
        stat=statistic,
        pvalue=pvalue,
    )


@config.when(task="ordinal_regression")
def statistical_association__kendalltau(y_validation: np.ndarray, val_pred: np.ndarray):
    """measure the statistical association between true labels and predicted labels"""

    statistic, pvalue = stats.kendalltau(y_validation, val_pred)

    return dict(
        test="kendalltau",
        stat=statistic,
        pvalue=pvalue,
    )


def model_results(
    task: str,
    label: str,
    scorer_name: str,
    bootstrap_iter: int,
    val_score: float,
    statistical_ttest_one_sample: dict,
    statistical_association: dict,
) -> dict:
    """Collect key metrics and results into a single JSON serializable file"""
    return {
        "task": task,
        "label": label,
        "scorer_name": scorer_name,
        "validation_score": val_score,
        "significance": statistical_ttest_one_sample,
        "association": statistical_association,
        "bootstrap_iter": bootstrap_iter,
    }
