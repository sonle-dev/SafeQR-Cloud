import os
import joblib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_model = None

def get_ml_pipeline():
    global _model
    if _model is not None:
        return _model

    # Candidate paths for local and Docker container
    candidate_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml_engine", "models", "vietqr_nlp_model.pkl")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_engine", "models", "vietqr_nlp_model.pkl")),
        "/app/ml_engine/models/vietqr_nlp_model.pkl"
    ]

    for p in candidate_paths:
        if os.path.exists(p):
            try:
                _model = joblib.load(p)
                logger.info(f"Loaded ML model from: {p}")
                return _model
            except Exception as e:
                logger.warning(f"Failed to load model from {p}: {e}")

    logger.warning("ML model pkl file not found. Falling back to heuristic mode.")
    return None

def predict_fraud_probability(message: str) -> float:
    """
    Predicts probability P_ML in [0.0, 1.0] that the transfer message contains
    coercion, legal impersonation, or social engineering tricks.
    """
    if not message or not message.strip():
        return 0.0

    pipeline = get_ml_pipeline()
    if pipeline is None:
        # Fallback heuristic
        return 0.1

    try:
        # LogisticRegression predict_proba returns [P(label=0), P(label=1)]
        prob_classes = pipeline.predict_proba([message.lower()])[0]
        # Label 1 is fraud
        return float(prob_classes[1])
    except Exception as e:
        logger.error(f"Error in ML prediction: {e}")
        return 0.1
