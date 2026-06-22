import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import json
import os

def train_and_evaluate():
    print("Loading dataset...")
    df = pd.read_csv("dataset/phishing_emails.csv")
    
    # Text preprocessing & Vectorization
    X = df['text']
    y = df['label']
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    X_vec = vectorizer.fit_transform(X)
    
    # Split the dataset
    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)
    
    # Initialize models to compare
    models = {
        "Logistic Regression": LogisticRegression(),
        "Multinomial Naive Bayes": MultinomialNB(),
        "Random Forest": RandomForestClassifier(random_state=42)
    }
    
    best_model = None
    best_accuracy = 0
    best_name = ""
    best_metrics = {}
    
    print("Training and evaluating models...")
    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred).tolist()
        
        print(f"{name} - Accuracy: {acc:.4f}, F1: {f1:.4f}")
        
        if acc > best_accuracy:
            best_accuracy = acc
            best_model = model
            best_name = name
            phishing_rate = float(df['label'].mean())
            best_metrics = {
                "model_name": name,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "confusion_matrix": cm,
                "total_analyzed": len(df),
                "phishing_count": int(df['label'].sum()),
                "safe_count": int((df['label'] == 0).sum()),
                "phishing_rate": phishing_rate,
                "safe_rate": float(1 - phishing_rate)
            }
            
    print(f"\nBest model automatically selected: {best_name} with Accuracy {best_accuracy:.4f}")
    
    # Save the trained model and vectorizer
    joblib.dump(best_model, "model.pkl")
    joblib.dump(vectorizer, "vectorizer.pkl")
    
    # Save the evaluation metrics for the dashboard
    with open("metrics.json", "w") as f:
        json.dump(best_metrics, f)
        
    print("Training complete. Model, vectorizer, and metrics saved successfully.")

if __name__ == "__main__":
    train_and_evaluate()
