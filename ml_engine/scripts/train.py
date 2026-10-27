import re
import os
import sys
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def clean_vietnamese_text(text: str) -> str:
    """
    Cleans raw Vietnamese transfer messages:
    - Lowercase
    - Collapses dot/underscore obfuscations (e.g. 'p.h.a.t' -> 'phat')
    - Removes strange non-alphanumeric chars
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'(\b\w)\.(\w)\.(\w)', r'\1\2\3', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def train_model():
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.csv")
    model_output_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(model_output_dir, exist_ok=True)
    model_output_path = os.path.join(model_output_dir, "vietqr_nlp_model.pkl")

    print(f"[*] Dang nap dataset tu: {dataset_path}")
    df = pd.read_csv(dataset_path, encoding='utf-8')
    df['cleaned_text'] = df['text'].apply(clean_vietnamese_text)

    X = df['cleaned_text']
    y = df['label']

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 3), max_features=5000)),
        ('clf', LogisticRegression(C=1.0, solver='liblinear', random_state=42))
    ])

    print("[*] Dang huan luyen mo hinh Logistic Regression + TF-IDF...")
    pipeline.fit(X, y)

    y_pred = pipeline.predict(X)
    acc = accuracy_score(y, y_pred)
    print(f"[+] Do chinh xac tren tap huan luyen: {acc * 100:.2f}%")
    print("\nBao cao phan loai:\n", classification_report(y, y_pred))

    joblib.dump(pipeline, model_output_path)
    file_size_kb = os.path.getsize(model_output_path) / 1024
    print(f"[+] Da luu mo hinh tai: {model_output_path}")
    print(f"[+] Dung luong tep model: {file_size_kb:.2f} KB (Toi uu Cloud)")

if __name__ == "__main__":
    train_model()
