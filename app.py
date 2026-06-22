from flask import Flask, request, jsonify, render_template, send_file
import joblib
import json
import os
import re
from fpdf import FPDF
from datetime import datetime
import subprocess

app = Flask(__name__)

# Constants
MODEL_PATH = "model.pkl"
VECTORIZER_PATH = "vectorizer.pkl"
METRICS_PATH = "metrics.json"
REPORTS_DIR = "reports"

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

SUSPICIOUS_KEYWORDS = [
    "verify", "password", "account suspended", "click here", 
    "login now", "update information", "urgent", "security alert"
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/train", methods=["POST"])
def train_model():
    try:
        # Run the training script
        subprocess.run(["python", "train_model.py"], check=True)
        return jsonify({"success": True, "message": "Model trained successfully."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json
    subject = data.get("subject", "")
    body = data.get("body", "")
    
    full_text = subject + " " + body
    
    # 1. Feature Extraction & Explainability
    explainability = []
    
    # Check URLs
    urls = re.findall(r'(https?://\S+)', full_text)
    num_links = len(urls)
    if num_links > 0:
        explainability.append(f"Contains {num_links} link(s)")
        
    # Check suspicious keywords
    found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw.lower() in full_text.lower()]
    if found_keywords:
        explainability.append(f"Suspicious keywords detected: {', '.join(found_keywords)}")
        
    # Check special characters
    num_special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', full_text))
    if num_special_chars > 20:
        explainability.append("High number of special characters detected")
        
    # Check uppercase words
    uppercase_words = len(re.findall(r'\b[A-Z]{2,}\b', full_text))
    if uppercase_words > 5:
        explainability.append("Excessive use of uppercase words")
        
    # Urgent language
    if "urgent" in full_text.lower() or "immediately" in full_text.lower() or "action required" in full_text.lower():
        explainability.append("Urgent language indicator detected")

    # 2. Prediction
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        return jsonify({"success": False, "error": "Model not trained yet."})
        
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    
    X_vec = vectorizer.transform([full_text])
    prediction = model.predict(X_vec)[0] # 1 is Phishing, 0 is Safe
    probabilities = model.predict_proba(X_vec)[0]
    
    confidence = max(probabilities) * 100
    
    result = "PHISHING" if prediction == 1 else "SAFE"
    
    # Determine Risk Level
    if result == "SAFE":
        risk_level = "Low"
        if found_keywords or num_links > 0:
            risk_level = "Medium"
    else:
        risk_level = "High"
        if confidence > 80 and len(explainability) > 2:
            risk_level = "Critical"
            
    # Update metrics for live dashboard
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r") as f:
                metrics = json.load(f)
            
            total_analyzed = metrics.get("total_analyzed", 0)
            phishing_count = metrics.get("phishing_count", 0)
            safe_count = metrics.get("safe_count", 0)
            
            total_analyzed += 1
            if prediction == 1:
                phishing_count += 1
            else:
                safe_count += 1
                
            metrics["total_analyzed"] = total_analyzed
            metrics["phishing_count"] = phishing_count
            metrics["safe_count"] = safe_count
            metrics["phishing_rate"] = phishing_count / total_analyzed
            metrics["safe_rate"] = safe_count / total_analyzed
            
            with open(METRICS_PATH, "w") as f:
                json.dump(metrics, f)
        except Exception as e:
            print("Metrics update error:", e)

    return jsonify({
        "success": True,
        "prediction": result,
        "confidence": round(confidence, 2),
        "risk_level": risk_level,
        "explainability": explainability
    })

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    if not os.path.exists(METRICS_PATH):
        return jsonify({"success": False, "error": "No metrics found. Train the model first."})
        
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
        
    return jsonify({
        "success": True,
        "metrics": metrics
    })

@app.route("/api/confusion-matrix", methods=["GET"])
def get_confusion_matrix():
    if not os.path.exists(METRICS_PATH):
        return jsonify({"success": False, "error": "No metrics found."})
        
    with open(METRICS_PATH, "r") as f:
        metrics = json.load(f)
        
    return jsonify({
        "success": True,
        "confusion_matrix": metrics.get("confusion_matrix", [])
    })

@app.route("/api/report", methods=["POST"])
def generate_report():
    try:
        data = request.json
        subject = data.get("subject", "").encode('latin-1', 'replace').decode('latin-1')
        body = data.get("body", "").encode('latin-1', 'replace').decode('latin-1')
        prediction = data.get("prediction", "Unknown").encode('latin-1', 'replace').decode('latin-1')
        confidence = data.get("confidence", 0)
        risk_level = data.get("risk_level", "Unknown").encode('latin-1', 'replace').decode('latin-1')
        explainability = data.get("explainability", [])
        
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, text="PhishGuard AI - Email Analysis Report", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(10)
        
        # Date and Time
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 10, text=f"Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # Result Summary
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, text="Analysis Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 10, text=f"Prediction Result: {prediction}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, text=f"Confidence Score: {confidence}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, text=f"Risk Level: {risk_level}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # Detected Indicators
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, text="Detected Indicators (Explainability)", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=12)
        if not explainability:
             pdf.cell(0, 10, text="- No specific suspicious indicators detected.", new_x="LMARGIN", new_y="NEXT")
        else:
            for indicator in explainability:
                ind_text = indicator.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 10, text=f"- {ind_text}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
                
        # Email Content
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, text="Original Email Content", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=12)
        pdf.multi_cell(0, 10, text=f"Subject: {subject}", new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(0, 10, text=f"Body:\n{body}", new_x="LMARGIN", new_y="NEXT")
        
        report_filename = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        report_path = os.path.join(REPORTS_DIR, report_filename)
        
        pdf.output(report_path)
        
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        print("PDF Generation Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
