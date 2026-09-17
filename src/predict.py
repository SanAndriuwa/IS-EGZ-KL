"""Predict unseen CSV sessions using a locally trained model."""
import argparse
from pathlib import Path
import joblib
import pandas as pd
from .data import prepare_features


def predict(input_path, model_path, output_path):
    # Load only trusted, locally produced joblib files (pickle format).
    artifact = joblib.load(model_path)
    frame = pd.read_csv(input_path)
    features = prepare_features(frame, artifact['include_page_values'])
    probability = artifact['model'].predict_proba(features)[:, 1]
    result = pd.DataFrame({'row': range(len(frame)), 'purchase_probability': probability,
                           'prediction': (probability >= artifact['threshold']).astype(int)})
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--model', default='models/random_forest.joblib')
    parser.add_argument('--output', default='results/unseen_predictions.csv')
    args = parser.parse_args()
    print(predict(args.input, args.model, args.output).to_string(index=False))
