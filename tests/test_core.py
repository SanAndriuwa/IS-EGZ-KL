"""Tests target leakage, inference edge cases and the mathematical contract."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from src.data import load_and_split, prepare_features, NUMERIC, CATEGORICAL
from src.evaluation import metrics, select_threshold
from src.models import build_model, forest_probability_by_formula

ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = json.loads((ROOT / 'config.json').read_text())
        cls.frame, cls.parts = load_and_split(ROOT / 'data/online_shoppers_intention.csv', config)

    def test_chronological_disjoint_split(self):
        order = {'Feb': 2, 'Mar': 3, 'May': 5, 'June': 6, 'Jul': 7, 'Aug': 8,
                 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        train, valid, test = [self.parts[x] for x in ['train', 'validation', 'test']]
        self.assertLess(train.Month.map(order).max(), valid.Month.map(order).min())
        self.assertLess(valid.Month.map(order).max(), test.Month.map(order).min())
        self.assertEqual(len(set(train.index) | set(valid.index) | set(test.index)), len(self.frame))

    def test_no_target_or_suspect_feature_in_primary_input(self):
        features = prepare_features(self.frame)
        self.assertEqual(set(features.columns), set(NUMERIC + CATEGORICAL))
        self.assertTrue({'Month', 'Revenue', 'PageValues'}.isdisjoint(features.columns))

    def test_imputer_is_fit_on_training_only(self):
        train = prepare_features(self.parts['train'])
        model = build_model('logistic', 42)
        model.fit(train, self.parts['train'].Revenue)
        imputer = model.named_steps['preprocessing'].named_transformers_['numeric'].named_steps['imputer']
        np.testing.assert_allclose(imputer.statistics_, train[NUMERIC].median().to_numpy())
        before = imputer.statistics_.copy()
        model.predict_proba(prepare_features(self.parts['test']))
        np.testing.assert_array_equal(before, imputer.statistics_)

    def test_forest_equation_and_unseen_categories(self):
        train = prepare_features(self.parts['train'])
        model = build_model('random_forest', 42, {'n_estimators': 10, 'min_samples_leaf': 5})
        model.fit(train, self.parts['train'].Revenue)
        unseen = prepare_features(self.parts['test'].head(5))
        unseen['VisitorType'] = 'Unseen_Visitor'
        unseen['ProductRelated_Duration'] = np.nan
        actual = model.predict_proba(unseen)[:, 1]
        self.assertTrue(np.isfinite(actual).all())
        self.assertTrue(((actual >= 0) & (actual <= 1)).all())
        np.testing.assert_allclose(forest_probability_by_formula(model, unseen), actual, atol=1e-12)

    def test_constant_score_ap_equals_prevalence(self):
        y = np.array([0, 0, 0, 1])
        result = metrics(y, np.full(4, 0.1), 0.5)
        self.assertEqual(result['average_precision'], 0.25)
        self.assertEqual(result['precision'], 0)
        self.assertEqual(result['recall'], 0)

    def test_threshold_uses_supplied_validation_labels(self):
        self.assertEqual(select_threshold(np.array([0, 1]), np.array([0.1, 0.9])), 0.11)

    def test_invalid_schema_and_values_are_rejected(self):
        with self.assertRaises(ValueError):
            prepare_features(self.frame.drop(columns=['Browser']))
        invalid = self.frame.head(2).copy()
        invalid.loc[invalid.index[0], 'BounceRates'] = 2.0
        with self.assertRaises(ValueError):
            prepare_features(invalid)


if __name__ == '__main__':
    unittest.main()
