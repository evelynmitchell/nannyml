#  License: Apache Software License 2.0
#  Author:   Niels Nuyttens  <niels@nannyml.com>


"""Unit tests for performance metrics."""
from typing import Tuple

import numpy as np
import pandas as pd
import pytest
from logging import getLogger

from nannyml import PerformanceCalculator
from nannyml._typing import ProblemType
from nannyml.chunk import DefaultChunker
from nannyml.datasets import load_synthetic_multiclass_classification_dataset
from nannyml.performance_calculation.metrics.base import MetricFactory
from nannyml.performance_calculation.metrics.multiclass_classification import (
    MulticlassClassificationAccuracy,
    MulticlassClassificationAUROC,
    MulticlassClassificationConfusionMatrix,
    MulticlassClassificationF1,
    MulticlassClassificationPrecision,
    MulticlassClassificationRecall,
    MulticlassClassificationSpecificity,
    MulticlassClassificationAP,
    MulticlassClassificationBusinessValue
)
from nannyml.thresholds import ConstantThreshold, StandardDeviationThreshold

LOGGER = getLogger(__name__)


@pytest.fixture(scope='module')
def multiclass_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:  # noqa: D103
    ref_df, ana_df, tgt_df = load_synthetic_multiclass_classification_dataset()

    return ref_df, ana_df, tgt_df


@pytest.fixture(scope='module')
def performance_calculator() -> PerformanceCalculator:  # noqa: D103
    business_value_matrix = np.array([
        [1, 0, -1],
        [0, 1, 0],
        [-1, 0, 1]
    ])
    return PerformanceCalculator(
        timestamp_column_name='timestamp',
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
        },
        y_pred='y_pred',
        y_true='y_true',
        metrics=[
            'roc_auc',
            'f1',
            'precision',
            'recall',
            'specificity',
            'accuracy',
            'confusion_matrix',
            'average_precision',
            'business_value'
        ],
        problem_type='classification_multiclass',
        business_value_matrix=business_value_matrix,
        normalize_business_value='per_prediction'
    )


@pytest.fixture(scope='module')
def realized_performance_metrics(multiclass_data) -> pd.DataFrame:  # noqa: D103
    business_value_matrix = np.array([
        [1, 0, -1],
        [0, 1, 0],
        [-1, 0, 1]
    ])
    performance_calculator = PerformanceCalculator(
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
        },
        y_pred='y_pred',
        y_true='y_true',
        metrics=[
            'roc_auc',
            'f1',
            'precision',
            'recall',
            'specificity',
            'accuracy',
            'confusion_matrix',
            'average_precision',
            'business_value'
        ],
        problem_type='classification_multiclass',
        business_value_matrix=business_value_matrix,
        normalize_business_value='per_prediction'
    ).fit(multiclass_data[0])
    results = performance_calculator.calculate(
        multiclass_data[1].merge(multiclass_data[2], on='id', how='left')
    ).filter(period='analysis')
    return results.to_df()


@pytest.fixture(scope='module')
def no_timestamp_metrics(performance_calculator, multiclass_data) -> pd.DataFrame:  # noqa: D103
    performance_calculator.fit(multiclass_data[0])
    results = performance_calculator.calculate(
        multiclass_data[1].merge(multiclass_data[2], left_index=True, right_index=True)
    ).filter(period='analysis')
    return results.data


@pytest.mark.parametrize(
    'key,problem_type,metric',
    [
        ('roc_auc', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationAUROC),
        ('f1', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationF1),
        ('precision', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationPrecision),
        ('recall', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationRecall),
        ('specificity', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationSpecificity),
        ('accuracy', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationAccuracy),
        ('confusion_matrix', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationConfusionMatrix),
        ('average_precision', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationAP),
        ('business_value', ProblemType.CLASSIFICATION_MULTICLASS, MulticlassClassificationBusinessValue),
    ],
)
def test_metric_factory_returns_correct_metric_given_key_and_problem_type(key, problem_type, metric):  # noqa: D103
    y_pred_proba = {
        'prepaid_card': 'y_pred_proba_prepaid_card',
        'highstreet_card': 'y_pred_proba_highstreet_card',
        'upmarket_card': 'y_pred_proba_upmarket_card',
    }
    business_value_matrix = np.array([
        [1, 0, -1],
        [0, 1, 0],
        [-1, 0, 1]
    ])
    sut = MetricFactory.create(
        key,
        problem_type,
        y_true='y_true',
        y_pred='y_pred',
        y_pred_proba=y_pred_proba,
        threshold=StandardDeviationThreshold(),
        business_value_matrix=business_value_matrix
    )
    assert sut == metric(
        y_true='y_true',
        y_pred='y_pred',
        y_pred_proba=y_pred_proba,
        threshold=StandardDeviationThreshold,
        business_value_matrix=business_value_matrix
    )


@pytest.mark.parametrize(
    'metric, expected',
    [
        ('roc_auc', [0.90759, 0.91053, 0.90941, 0.91158, 0.90753, 0.74859, 0.75114, 0.7564, 0.75856, 0.75394]),
        ('f1', [0.7511, 0.76305, 0.75849, 0.75894, 0.75796, 0.55711, 0.55915, 0.56506, 0.5639, 0.56164]),
        ('precision', [0.75127, 0.76313, 0.7585, 0.75897, 0.75795, 0.5597, 0.56291, 0.56907, 0.56667, 0.56513]),
        ('recall', [0.75103, 0.76315, 0.75848, 0.75899, 0.75798, 0.55783, 0.56017, 0.56594, 0.56472, 0.56277]),
        ('specificity', [0.87555, 0.88151, 0.87937, 0.87963, 0.87899, 0.77991, 0.78068, 0.78422, 0.78342, 0.78243]),
        ('accuracy', [0.75117, 0.763, 0.75867, 0.75917, 0.758, 0.56083, 0.56233, 0.56983, 0.56783, 0.566]),
        ('true_upmarket_card_pred_upmarket_card', [1490, 1524, 1544, 1528, 1567, 1165, 1120, 1147, 1166, 1173]),
        ('true_upmarket_card_pred_prepaid_card', [245, 234, 224, 201, 229, 372, 382, 382, 377, 371]),
        ('true_upmarket_card_pred_highstreet_card', [245, 252, 251, 262, 242, 525, 508, 535, 513, 513]),
        ('true_prepaid_card_pred_upmarket_card', [204, 201, 200, 246, 194, 448, 419, 416, 440, 436]),
        ('true_prepaid_card_pred_prepaid_card', [1560, 1518, 1557, 1577, 1493, 878, 908, 875, 888, 869]),
        ('true_prepaid_card_pred_highstreet_card', [274, 237, 264, 237, 270, 539, 595, 550, 539, 568]),
        ('true_highstreet_card_pred_upmarket_card', [250, 237, 259, 251, 277, 330, 318, 302, 312, 326]),
        ('true_highstreet_card_pred_prepaid_card', [275, 261, 250, 248, 240, 421, 404, 396, 412, 390]),
        ('true_highstreet_card_pred_highstreet_card', [1457, 1536, 1451, 1450, 1488, 1322, 1346, 1397, 1353, 1354]),
        ('average_precision', [0.83891, 0.8424, 0.84207, 0.844, 0.8364, 0.59673, 0.60133, 0.60421, 0.60751, 0.6052]),
        ('business_value', [2.00122, 2.04414, 2.01853, 2.01854, 2.01693, 1.28921, 1.31007, 1.32972, 1.32404, 1.31623])
    ],
)
def test_metric_values_are_calculated_correctly(realized_performance_metrics, metric, expected):  # noqa: D103
    metric_values = realized_performance_metrics.loc[:, (metric, 'value')]
    assert (round(metric_values, 5) == expected).all()


@pytest.mark.parametrize(
    'metric, expected',
    [
        ('roc_auc', [0.90759, 0.91053, 0.90941, 0.91158, 0.90753, 0.74859, 0.75114, 0.7564, 0.75856, 0.75394]),
        ('f1', [0.7511, 0.76305, 0.75849, 0.75894, 0.75796, 0.55711, 0.55915, 0.56506, 0.5639, 0.56164]),
        ('precision', [0.75127, 0.76313, 0.7585, 0.75897, 0.75795, 0.5597, 0.56291, 0.56907, 0.56667, 0.56513]),
        ('recall', [0.75103, 0.76315, 0.75848, 0.75899, 0.75798, 0.55783, 0.56017, 0.56594, 0.56472, 0.56277]),
        ('specificity', [0.87555, 0.88151, 0.87937, 0.87963, 0.87899, 0.77991, 0.78068, 0.78422, 0.78342, 0.78243]),
        ('accuracy', [0.75117, 0.763, 0.75867, 0.75917, 0.758, 0.56083, 0.56233, 0.56983, 0.56783, 0.566]),
        ('true_upmarket_card_pred_upmarket_card', [1490, 1524, 1544, 1528, 1567, 1165, 1120, 1147, 1166, 1173]),
        ('true_upmarket_card_pred_prepaid_card', [245, 234, 224, 201, 229, 372, 382, 382, 377, 371]),
        ('true_upmarket_card_pred_highstreet_card', [245, 252, 251, 262, 242, 525, 508, 535, 513, 513]),
        ('true_prepaid_card_pred_upmarket_card', [204, 201, 200, 246, 194, 448, 419, 416, 440, 436]),
        ('true_prepaid_card_pred_prepaid_card', [1560, 1518, 1557, 1577, 1493, 878, 908, 875, 888, 869]),
        ('true_prepaid_card_pred_highstreet_card', [274, 237, 264, 237, 270, 539, 595, 550, 539, 568]),
        ('true_highstreet_card_pred_upmarket_card', [250, 237, 259, 251, 277, 330, 318, 302, 312, 326]),
        ('true_highstreet_card_pred_prepaid_card', [275, 261, 250, 248, 240, 421, 404, 396, 412, 390]),
        ('true_highstreet_card_pred_highstreet_card', [1457, 1536, 1451, 1450, 1488, 1322, 1346, 1397, 1353, 1354]),
        ('average_precision', [0.83891, 0.8424, 0.84207, 0.844, 0.8364, 0.59673, 0.60133, 0.60421, 0.60751, 0.6052]),
        ('business_value', [2.00122, 2.04414, 2.01853, 2.01854, 2.01693, 1.28921, 1.31007, 1.32972, 1.32404, 1.31623])
    ],
)
def test_metric_values_without_timestamps_are_calculated_correctly(  # noqa: D103
    no_timestamp_metrics, metric, expected
):
    metric_values = no_timestamp_metrics.loc[:, (metric, 'value')]
    assert (round(metric_values, 5) == expected).all()


@pytest.mark.parametrize(
    'metric_cls',
    [
        MulticlassClassificationAUROC,
        MulticlassClassificationF1,
        MulticlassClassificationPrecision,
        MulticlassClassificationRecall,
        MulticlassClassificationSpecificity,
        MulticlassClassificationAccuracy,
    ],
)
def test_metric_logs_warning_when_lower_threshold_is_overridden_by_metric_limits(  # noqa: D103
    caplog, metric_cls, multiclass_data
):
    reference = multiclass_data[0]
    metric = metric_cls(
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
        },
        y_pred='y_pred',
        y_true='y_true',
        threshold=ConstantThreshold(lower=-1),
    )
    metric.fit(reference, chunker=DefaultChunker())

    assert (
        f'{metric.display_name} lower threshold value -1 overridden by '
        f'lower threshold value limit {metric.lower_threshold_value_limit}' in caplog.messages
    )


@pytest.mark.parametrize(
    'metric_cls',
    [
        MulticlassClassificationAUROC,
        MulticlassClassificationF1,
        MulticlassClassificationPrecision,
        MulticlassClassificationRecall,
        MulticlassClassificationSpecificity,
        MulticlassClassificationAccuracy,
    ],
)
def test_metric_logs_warning_when_upper_threshold_is_overridden_by_metric_limits(  # noqa: D103
    caplog, metric_cls, multiclass_data
):
    reference = multiclass_data[0]
    metric = metric_cls(
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
        },
        y_pred='y_pred',
        y_true='y_true',
        threshold=ConstantThreshold(upper=2),
    )
    metric.fit(reference, chunker=DefaultChunker())

    assert (
        f'{metric.display_name} upper threshold value 2 overridden by '
        f'upper threshold value limit {metric.upper_threshold_value_limit}' in caplog.messages
    )


def test_auroc_errors_out_when_not_all_classes_are_represented_reference(multiclass_data, caplog):
    LOGGER.info("testing test_auroc_errors_out_when_not_all_classes_are_represented_reference")
    reference, _, _ = multiclass_data
    reference['y_pred_proba_clazz'] = reference['y_pred_proba_upmarket_card']
    performance_calculator = PerformanceCalculator(
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
            'clazz': 'y_pred_proba_clazz'
        },
        y_pred='y_pred',
        y_true='y_true',
        metrics=['roc_auc'],
        problem_type='classification_multiclass',
    )
    performance_calculator.fit(reference)
    expected_exc_test = "y_pred_proba class and class probabilities dictionary does not match reference data."
    assert expected_exc_test in caplog.text


def test_auroc_errors_out_when_not_all_classes_are_represented_chunk(multiclass_data, caplog):
    LOGGER.info("testing test_auroc_errors_out_when_not_all_classes_are_represented_chunk")
    reference, monitored, targets = multiclass_data
    monitored = monitored.merge(targets)
    reference['y_pred_proba_clazz'] = reference['y_pred_proba_upmarket_card']
    monitored['y_pred_proba_clazz'] = monitored['y_pred_proba_upmarket_card']
    reference['y_true'].iloc[-1000:] = 'clazz'
    performance_calculator = PerformanceCalculator(
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
            'clazz': 'y_pred_proba_clazz'
        },
        y_pred='y_pred',
        y_true='y_true',
        metrics=['roc_auc'],
        problem_type='classification_multiclass',
    )
    performance_calculator.fit(reference)
    _ = performance_calculator.calculate(monitored)
    expected_exc_test = "does not contain all reported classes, cannot calculate"
    assert expected_exc_test in caplog.text


def test_business_value_getting_classes_from_y_pred_proba(multiclass_data):
    reference, monitored, targets = multiclass_data
    reference['y_true'] = 'prepaid_card'
    monitored = monitored.merge(targets, on='id', how='left')
    business_value_matrix = np.array([
        [1, 0, -1],
        [0, 1, 0],
        [-1, 0, 1]
    ])
    calc = PerformanceCalculator(
        y_pred_proba={
            'prepaid_card': 'y_pred_proba_prepaid_card',
            'highstreet_card': 'y_pred_proba_highstreet_card',
            'upmarket_card': 'y_pred_proba_upmarket_card',
        },
        y_pred='y_pred',
        y_true='y_true',
        metrics=['business_value'],
        problem_type='classification_multiclass',
        business_value_matrix=business_value_matrix,
        normalize_business_value='per_prediction'
    ).fit(reference)
    results = calc.calculate(monitored)
    assert [
        2.00122, 2.04414, 2.01853, 2.01854, 2.01693, 1.28921, 1.31007, 1.32972, 1.32404, 1.31623
    ] == list(
        results.filter(period='analysis').to_df().round(5).loc[:, ('business_value', 'value')]
    )


# TODO: At the moment the test below is invalid because y_pred_proba is mandatory. Uncomment when it is not.
# def test_business_value_getting_classes_without_y_pred_proba(multiclass_data):
#     reference, monitored, targets = multiclass_data
#     monitored = monitored.merge(targets, on='id', how='left')
#     business_value_matrix = np.array([
#         [1, 0, -1],
#         [0, 1, 0],
#         [-1, 0, 1]
#     ])
#     calc = PerformanceCalculator(
#         y_pred='y_pred',
#         y_true='y_true',
#         metrics=['business_value'],
#         problem_type='classification_multiclass',
#         business_value_matrix=business_value_matrix,
#         normalize_business_value='per_prediction'
#     ).fit(reference)
#     results = calc.calculate(monitored)
#     assert [
#         2.00122, 2.04414, 2.01853, 2.01854, 2.01693, 1.28921, 1.31007, 1.32972, 1.32404, 1.31623
#     ] == list(
#         results.filter(period='analysis').to_df().round(5).loc[:, ('business_value', 'value')]
#     )
