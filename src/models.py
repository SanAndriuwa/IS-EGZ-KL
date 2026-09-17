"""Small model grids with preprocessing fitted only on training rows."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .data import CATEGORICAL, NUMERIC


def build_model(name, seed, params=None, include_page_values=False):
    numeric = NUMERIC + (['PageValues'] if include_page_values else [])
    preprocessing = ColumnTransformer([
        ('numeric', Pipeline([('imputer', SimpleImputer(strategy='median')),
                              ('scaler', StandardScaler())]), numeric),
        ('category', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                               ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), CATEGORICAL)
    ])
    estimators = {
        'purchase_rate': DummyClassifier(strategy='prior'),
        'logistic': LogisticRegression(max_iter=2000, random_state=seed),
        'random_forest': RandomForestClassifier(n_estimators=200, max_features='sqrt',
                                                n_jobs=1, random_state=seed),
        'gradient_boosting': HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05,
                                                            early_stopping=False, random_state=seed)
    }
    estimator = estimators[name].set_params(**(params or {}))
    return Pipeline([('preprocessing', preprocessing), ('classifier', estimator)])


def candidates(name):
    return {
        'purchase_rate': [{}],
        'logistic': [{'C': 0.1}, {'C': 1.0}],
        'random_forest': [{'min_samples_leaf': 5}, {'min_samples_leaf': 20}],
        'gradient_boosting': [{'max_leaf_nodes': 7}, {'max_leaf_nodes': 15}]
    }[name]


def forest_probability_by_formula(model, features):
    """Equation: p(x) = (1 / B) * sum_b p_b(y=1 | leaf_b(x))."""
    encoded = model.named_steps['preprocessing'].transform(features)
    trees = model.named_steps['classifier'].estimators_
    # Each tree returns the positive-class frequency in the reached leaf.
    return np.mean([tree.predict_proba(encoded)[:, 1] for tree in trees], axis=0)
