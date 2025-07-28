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

import pathlib
from typing import Type

import numpy as np
import pytest
import sklearn.calibration as calib
import sklearn.inspection as inspection
import sklearn.metrics as metrics
import sklearn.model_selection as model_selection
from sklearn.datasets import load_diabetes, load_iris, make_classification, make_friedman1
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from hamilton.io.utils import FILE_METADATA
from hamilton.plugins.sklearn_plot_extensions import SklearnPlotSaver

if hasattr(metrics, "PredictionErrorDisplay"):
    PredictionErrorDisplay = metrics.PredictionErrorDisplay
else:
    PredictionErrorDisplay = Type

if hasattr(inspection, "DecisionBoundaryDisplay"):
    DecisionBoundaryDisplay = inspection.DecisionBoundaryDisplay
else:
    DecisionBoundaryDisplay = Type

if hasattr(inspection, "PartialDependenceDisplay"):
    PartialDependenceDisplay = inspection.PartialDependenceDisplay
else:
    PartialDependenceDisplay = Type

if hasattr(inspection, "partial_dependence"):
    partial_dependence = inspection.partial_dependence
else:
    partial_dependence = Type

if hasattr(model_selection, "LearningCurveDisplay"):
    LearningCurveDisplay = model_selection.LearningCurveDisplay
else:
    LearningCurveDisplay = Type

if hasattr(model_selection, "ValidationCurveDisplay"):
    ValidationCurveDisplay = model_selection.ValidationCurveDisplay
else:
    ValidationCurveDisplay = Type


@pytest.fixture
def confusion_matrix_display() -> metrics.ConfusionMatrixDisplay:
    X, y = make_classification(random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
    clf = SVC(random_state=0)
    clf.fit(X_train, y_train)
    predictions = clf.predict(X_test)
    cm = metrics.confusion_matrix(y_test, predictions, labels=clf.classes_)
    cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=clf.classes_)
    return cm_display


@pytest.fixture
def det_curve_display() -> metrics.DetCurveDisplay:
    X, y = make_classification(n_samples=1000, random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=0)
    clf = SVC(random_state=0).fit(X_train, y_train)
    y_pred = clf.decision_function(X_test)
    fpr, fnr, _ = metrics.det_curve(y_test, y_pred)
    detcurve = metrics.DetCurveDisplay(fpr=fpr, fnr=fnr, estimator_name="SVC")
    return detcurve


@pytest.fixture
def precision_recall_display() -> metrics.PrecisionRecallDisplay:
    X, y = make_classification(n_samples=1000, random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=0)
    clf = SVC(random_state=0).fit(X_train, y_train)
    clf.fit(X_train, y_train)
    predictions = clf.predict(X_test)
    precision, recall, _ = metrics.precision_recall_curve(y_test, predictions)
    precision_recall = metrics.PrecisionRecallDisplay(precision=precision, recall=recall)
    return precision_recall


@pytest.fixture
def prediction_error_display() -> PredictionErrorDisplay:
    X, y = load_diabetes(return_X_y=True)
    ridge = Ridge().fit(X, y)
    y_pred = ridge.predict(X)
    pred_error = PredictionErrorDisplay.from_predictions(y_true=y, y_pred=y_pred)
    return pred_error


@pytest.fixture
def roc_curve_display() -> metrics.RocCurveDisplay:
    y = np.array([0, 0, 1, 1])
    pred = np.array([0.1, 0.4, 0.35, 0.8])
    fpr, tpr, threshold = metrics.roc_curve(y, pred)
    roc_auc = metrics.auc(fpr, tpr)
    roccurve = metrics.RocCurveDisplay(
        fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name="example estimator"
    )
    return roccurve


@pytest.fixture
def calibration_display() -> calib.CalibrationDisplay:
    X, y = make_classification(random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
    clf = LogisticRegression(random_state=0)
    clf.fit(X_train, y_train)
    LogisticRegression(random_state=0)
    y_prob = clf.predict_proba(X_test)[:, 1]
    prob_true, prob_pred = calib.calibration_curve(y_test, y_prob, n_bins=10)
    disp = calib.CalibrationDisplay(prob_true, prob_pred, y_prob)
    return disp


@pytest.fixture
def decision_boundary_display() -> DecisionBoundaryDisplay:
    iris = load_iris()
    feature_1, feature_2 = np.meshgrid(
        np.linspace(iris.data[:, 0].min(), iris.data[:, 0].max()),
        np.linspace(iris.data[:, 1].min(), iris.data[:, 1].max()),
    )
    grid = np.vstack([feature_1.ravel(), feature_2.ravel()]).T
    tree = DecisionTreeClassifier().fit(iris.data[:, :2], iris.target)
    y_pred = np.reshape(tree.predict(grid), feature_1.shape)
    decision_curve = inspection.DecisionBoundaryDisplay(
        xx0=feature_1, xx1=feature_2, response=y_pred
    )
    return decision_curve


@pytest.fixture
def partial_dependence_display() -> PartialDependenceDisplay:
    X, y = make_friedman1()
    clf = GradientBoostingRegressor(n_estimators=10).fit(X, y)
    features, feature_names = [(0,)], [f"Features #{i}" for i in range(X.shape[1])]
    deciles = {0: np.linspace(0, 1, num=5)}
    pd_results = partial_dependence(clf, X, features=0, kind="average", grid_resolution=5)
    partial_dep_disp = PartialDependenceDisplay(
        [pd_results],
        features=features,
        feature_names=feature_names,
        target_idx=0,
        deciles=deciles,
    )
    return partial_dep_disp


@pytest.fixture
def learning_curve_display() -> LearningCurveDisplay:
    X, y = load_iris(return_X_y=True)
    tree = DecisionTreeClassifier(random_state=0)
    train_sizes, train_scores, test_scores = model_selection.learning_curve(tree, X, y)
    learn_curve_disp = LearningCurveDisplay(
        train_sizes=train_sizes,
        train_scores=train_scores,
        test_scores=test_scores,
        score_name="Score",
    )
    return learn_curve_disp


@pytest.fixture
def validation_curve_display() -> ValidationCurveDisplay:
    X, y = make_classification(n_samples=1_000, random_state=0)
    logistic_regression = LogisticRegression()
    param_name, param_range = "C", np.logspace(-8, 3, 10)
    train_scores, test_scores = model_selection.validation_curve(
        logistic_regression, X, y, param_name=param_name, param_range=param_range
    )
    valid_curve_disp = ValidationCurveDisplay(
        param_name=param_name,
        param_range=param_range,
        train_scores=train_scores,
        test_scores=test_scores,
        score_name="Score",
    )
    return valid_curve_disp


def test_cm_plot_saver(
    confusion_matrix_display: metrics.ConfusionMatrixDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "cm_plot.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(confusion_matrix_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_det_curve_display(
    det_curve_display: metrics.DetCurveDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "det_curve_plot.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(det_curve_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_precision_recall_display(
    precision_recall_display: metrics.PrecisionRecallDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "precision_recall.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(precision_recall_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_prediction_error_display(
    prediction_error_display: PredictionErrorDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "prediction_error_plot.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(prediction_error_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_roc_curve_display(
    roc_curve_display: metrics.RocCurveDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "roc_curve.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(roc_curve_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_calibration_display(
    calibration_display: calib.CalibrationDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "calibration_curve.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(calibration_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_decision_boundary_display(
    decision_boundary_display: DecisionBoundaryDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "dbd.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(decision_boundary_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_partial_dependence_display(
    partial_dependence_display: PartialDependenceDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "pdd.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(partial_dependence_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_learning_curve_display(
    learning_curve_display: LearningCurveDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "lcd.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(learning_curve_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)


def test_validation_curve_display(
    validation_curve_display: ValidationCurveDisplay, tmp_path: pathlib.Path
) -> None:
    plot_path = tmp_path / "vcd.png"
    writer = SklearnPlotSaver(path=plot_path)

    metadata = writer.save_data(validation_curve_display)

    assert plot_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(plot_path)
