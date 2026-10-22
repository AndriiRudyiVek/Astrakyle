"""Predict seven-day access using a locally trained, trusted model file."""
import argparse
import json
from pathlib import Path

import joblib

from .train_coverage import features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=Path('outputs/coverage_model_42/models.joblib'))
    parser.add_argument('--raan-deg', type=float, required=True)
    parser.add_argument('--initial-angle-deg', type=float, required=True)
    parser.add_argument('--latitude-deg', type=float, required=True)
    args = parser.parse_args()
    try:
        x = features([[args.raan_deg, args.initial_angle_deg, args.latitude_deg]])
    except ValueError as exc:
        parser.error(str(exc))
    bundle = joblib.load(args.model)
    result = {name: float(model.predict(x)[0]) for name, model in bundle['models'].items()}
    result['fixed_settings'] = bundle['fixed']
    result['note'] = 'Raw surrogate estimates; verify design decisions with the simulator.'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
