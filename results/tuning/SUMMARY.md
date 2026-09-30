# EXTENDED HYPERPARAMETER STUDY

Post-test exploratory: Nov-Dec was inspected in earlier project stages, although no Nov-Dec result selected these parameters, thresholds or model family.

Tested configurations: logistic 22, random_forest 250, gradient_boosting 200, xgboost 250
Total unique configurations: 722; total model fits: 3372.
Temporal folds: Feb-Mar → May; Feb-Mar-May → June; +June → Jul; +Jul → Aug.

| Family | Parameters | Temporal AP mean ± std | Sep-Oct AP | Nov-Dec AP |
|---|---|---:|---:|---:|
| logistic | `{"C": 0.3, "class_weight": null}` | 0.2397 ± 0.0623 | 0.2464 | 0.3360 |
| random_forest | `{"class_weight": null, "criterion": "entropy", "max_depth": null, "max_features": "sqrt", "min_samples_leaf": 2, "min_samples_split": 20, "n_estimators": 200}` | 0.2852 ± 0.0326 | 0.3052 | 0.3325 |
| gradient_boosting | `{"l2_regularization": 10, "learning_rate": 0.05, "max_iter": 400, "max_leaf_nodes": 5, "min_samples_leaf": 40}` | 0.2876 ± 0.0216 | 0.2920 | 0.3380 |
| xgboost | `{"colsample_bytree": 0.7, "learning_rate": 0.05, "max_depth": 4, "min_child_weight": 10, "n_estimators": 200, "reg_alpha": 1, "reg_lambda": 3, "scale_pos_weight": "train_ratio", "subsample": 1.0}` | 0.2892 ± 0.0149 | 0.2863 | 0.3407 |

Comparison with the original Sep-Oct validation AP:
- logistic: original 0.2487, tuned 0.2464, delta -0.0022.
- random_forest: original 0.3070, tuned 0.3052, delta -0.0018.
- gradient_boosting: original 0.2892, tuned 0.2920, delta +0.0028.

Overall Sep-Oct validation winner: **random_forest**; threshold 0.01; Sep-Oct AP 0.3052.
Exploratory Nov-Dec: AP 0.3325, Brier 0.1563, precision 0.2303, recall 0.9908, F2 0.5967.
Original Nov-Dec AP: baseline 0.2066, LR 0.3336, RF 0.3411, HGB 0.3392.
Delta versus original RF: -0.0087.
Broad tuning did not reveal a hidden performance reserve; features/data may be a larger limitation.

Hyperparameters and family were chosen without Nov-Dec results; because that period was already inspected, this is not independent confirmation.
