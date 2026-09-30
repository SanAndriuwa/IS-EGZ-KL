"""Contracts for temporal tuning; intentionally cheap to run."""
import inspect
import json
from pathlib import Path
import unittest

import numpy as np

from src.data import load_and_split, prepare_features
from src.tuning import (COUNTS, _classifier, _encoded_folds, candidate_grids,
                        choose_overall, choose_stable_family, temporal_folds)

ROOT = Path(__file__).resolve().parents[1]


class TuningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
        _, cls.parts = load_and_split(ROOT / 'data/online_shoppers_intention.csv', config)

    def test_expanding_folds_are_chronological_disjoint_and_two_class(self):
        order = {'Feb': 2, 'Mar': 3, 'May': 5, 'June': 6, 'Jul': 7, 'Aug': 8}
        folds = temporal_folds(self.parts['train'])
        self.assertEqual(len(folds), 4)
        self.assertEqual([valid.Month.iloc[0] for _, valid in folds],
                         ['May', 'June', 'Jul', 'Aug'])
        for fit, valid in folds:
            self.assertLess(fit.Month.map(order).max(), valid.Month.map(order).min())
            self.assertTrue(set(fit.index).isdisjoint(valid.index))
            self.assertEqual(fit.Revenue.nunique(), 2)
            self.assertEqual(valid.Revenue.nunique(), 2)

    def test_fold_preprocessing_uses_only_earlier_months(self):
        original = self.parts['train']
        changed = original.copy()
        changed.loc[changed.Month == 'May', 'Administrative'] = 1000000
        first_original = _encoded_folds(original)[0]
        first_changed = _encoded_folds(changed)[0]
        np.testing.assert_allclose(first_original[0], first_changed[0])
        self.assertFalse(np.allclose(first_original[2], first_changed[2]))

    def test_tuning_features_exclude_future_month_and_suspect_values(self):
        columns = set(prepare_features(self.parts['train']).columns)
        self.assertTrue({'Revenue', 'Month', 'PageValues'}.isdisjoint(columns))

    def test_grid_counts_uniqueness_and_seed_reproducibility(self):
        first = candidate_grids(42)
        self.assertEqual(first, candidate_grids(42))
        self.assertEqual({name: len(grid) for name, grid in first.items()}, COUNTS)
        self.assertEqual(sum(map(len, first.values())), 722)
        for grid in first.values():
            self.assertEqual(len(grid), len({json.dumps(p, sort_keys=True)
                                             for p in grid}))
        pairs = {(p['learning_rate'], p['max_iter'])
                 for p in first['gradient_boosting']}
        self.assertEqual(len(pairs), 20)
        self.assertNotEqual(first['xgboost'], candidate_grids(43)['xgboost'])

    def test_xgboost_ratio_is_computed_from_each_fold_train(self):
        y = np.array([0, 0, 0, 0, 1])
        model = _classifier('xgboost', {'n_estimators': 100,
                                       'scale_pos_weight': 'sqrt_train_ratio'}, 42, y)
        self.assertEqual(model.get_params()['scale_pos_weight'], 2.0)

    def test_family_and_overall_selection_never_consult_test(self):
        rows = [{'family': 'logistic', 'parameters': json.dumps({'C': 1,
                  'class_weight': None}), 'stability_mean_ap': 0.30,
                 'stability_std_ap': 0.03},
                {'family': 'logistic', 'parameters': json.dumps({'C': 3,
                  'class_weight': None}), 'stability_mean_ap': 0.3005,
                 'stability_std_ap': 0.01}]
        self.assertEqual(choose_stable_family('logistic', rows), rows[1])
        family_rows = [{'family': 'logistic', 'validation_ap': 0.31,
                        'test_ap': 0.99},
                       {'family': 'random_forest', 'validation_ap': 0.32,
                        'test_ap': 0.01}]
        self.assertEqual(choose_overall(family_rows)['family'], 'random_forest')
        family_rows[0]['test_ap'], family_rows[1]['test_ap'] = 0.0, 1.0
        self.assertEqual(choose_overall(family_rows)['family'], 'random_forest')
        self.assertNotIn('test', inspect.signature(choose_overall).parameters)
        self.assertNotIn('test', inspect.signature(choose_stable_family).parameters)


if __name__ == '__main__':
    unittest.main()
