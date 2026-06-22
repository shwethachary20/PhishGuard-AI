document.addEventListener('DOMContentLoaded', () => {
    // State variables
    let currentEmailData = null;
    let chartsInitialized = false;
    let pieChartInstance = null;
    let barChartInstance = null;

    // Navigation
    const navLinks = document.querySelectorAll('.nav-links li');
    const views = document.querySelectorAll('.view');
    const startBtn = document.getElementById('start-btn');

    function switchView(targetId) {
        // Update active nav link
        navLinks.forEach(link => {
            if (link.dataset.target === targetId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Show target view, hide others
        views.forEach(view => {
            if (view.id === targetId) {
                view.classList.add('active');
                if (targetId === 'dashboard' && !chartsInitialized) {
                    loadDashboardData();
                }
            } else {
                view.classList.remove('active');
            }
        });
    }

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            switchView(link.dataset.target);
        });
    });

    startBtn.addEventListener('click', () => {
        switchView('detection');
    });

    // Toast Notifications
    function showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = 'toast'; // Reset classes
        
        if (type === 'error') {
            toast.style.borderLeftColor = 'var(--danger-color)';
        } else if (type === 'success') {
            toast.style.borderLeftColor = 'var(--success-color)';
        } else {
            toast.style.borderLeftColor = 'var(--accent-color)';
        }

        toast.classList.remove('hidden');

        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }

    // Dashboard Data Loading
    async function loadDashboardData() {
        try {
            // Fetch Metrics
            const metricsRes = await fetch('/api/metrics');
            const metricsData = await metricsRes.json();

            if (metricsData.success) {
                const metrics = metricsData.metrics;
                
                // Update text stats
                document.getElementById('stat-total').textContent = metrics.total_analyzed;
                document.getElementById('stat-phishing-rate').textContent = (metrics.phishing_rate * 100).toFixed(1) + '%';
                document.getElementById('stat-safe-rate').textContent = (metrics.safe_rate * 100).toFixed(1) + '%';
                document.getElementById('stat-accuracy').textContent = (metrics.accuracy * 100).toFixed(2) + '%';
                document.getElementById('stat-precision').textContent = metrics.precision.toFixed(4);
                document.getElementById('stat-recall').textContent = metrics.recall.toFixed(4);
                document.getElementById('stat-f1').textContent = metrics.f1_score.toFixed(4);

                // Fetch Confusion Matrix
                const cmRes = await fetch('/api/confusion-matrix');
                const cmData = await cmRes.json();
                
                if (cmData.success) {
                    initCharts(metrics, cmData.confusion_matrix);
                    chartsInitialized = true;
                }
            } else {
                showToast("Failed to load metrics. Have you trained the model?", "error");
            }
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            showToast("Network error loading dashboard.", "error");
        }
    }

    // Chart.js Initialization
    function initCharts(metrics, confusionMatrix) {
        // Pie Chart - Detection Rate
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        if (pieChartInstance) pieChartInstance.destroy();
        
        pieChartInstance = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Safe Emails', 'Phishing Emails'],
                datasets: [{
                    data: [metrics.safe_rate * 100, metrics.phishing_rate * 100],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#e2e8f0' }
                    }
                }
            }
        });

        // Bar Chart - Confusion Matrix
        // Format: [[TN, FP], [FN, TP]]
        const TN = confusionMatrix[0][0];
        const FP = confusionMatrix[0][1];
        const FN = confusionMatrix[1][0];
        const TP = confusionMatrix[1][1];

        const barCtx = document.getElementById('barChart').getContext('2d');
        if (barChartInstance) barChartInstance.destroy();

        barChartInstance = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: ['True Negative', 'False Positive', 'False Negative', 'True Positive'],
                datasets: [{
                    label: 'Count',
                    data: [TN, FP, FN, TP],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)', // TN - Good
                        'rgba(245, 158, 11, 0.7)', // FP - Warning
                        'rgba(245, 158, 11, 0.7)', // FN - Warning
                        'rgba(239, 68, 68, 0.7)'   // TP - Bad email correctly identified
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#e2e8f0' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#e2e8f0' }
                    }
                }
            }
        });
    }

    // Detection Logic
    const analyzeBtn = document.getElementById('analyze-btn');
    const clearBtn = document.getElementById('clear-btn');
    const resultPanel = document.getElementById('result-panel');
    const analyzeBtnText = document.getElementById('analyze-btn-text');

    analyzeBtn.addEventListener('click', async () => {
        const subject = document.getElementById('email-subject').value.trim();
        const body = document.getElementById('email-body').value.trim();

        if (!subject && !body) {
            showToast("Please enter an email subject or body.", "error");
            return;
        }

        // UI Loading State
        analyzeBtn.disabled = true;
        analyzeBtnText.textContent = "Analyzing...";
        resultPanel.classList.add('hidden');

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subject, body })
            });

            const data = await response.json();

            if (data.success) {
                displayResult(data, subject, body);
                // Trigger dashboard update in background so it's ready when user switches
                loadDashboardData();
            } else {
                showToast(data.error || "Analysis failed.", "error");
            }
        } catch (error) {
            console.error("Analysis error:", error);
            showToast("Network error during analysis.", "error");
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtnText.textContent = "Analyze Email";
        }
    });

    function displayResult(data, subject, body) {
        // Save current data for report generation
        currentEmailData = {
            subject: subject,
            body: body,
            prediction: data.prediction,
            confidence: data.confidence,
            risk_level: data.risk_level,
            explainability: data.explainability
        };

        const resultHeader = document.getElementById('result-header');
        const predictionText = document.getElementById('prediction-text');
        
        predictionText.textContent = data.prediction;
        
        // Styling based on result
        resultHeader.className = 'result-header ' + data.prediction.toLowerCase();
        
        document.getElementById('risk-level').textContent = data.risk_level;
        
        const riskLevelElement = document.getElementById('risk-level');
        if (data.risk_level === 'Critical' || data.risk_level === 'High') {
            riskLevelElement.className = 'text-danger';
        } else if (data.risk_level === 'Medium') {
            riskLevelElement.className = 'text-warning';
        } else {
            riskLevelElement.className = 'text-success';
        }

        document.getElementById('confidence-score').textContent = data.confidence + '%';

        // Explainability
        const explainList = document.getElementById('explainability-list');
        explainList.innerHTML = '';
        
        if (data.explainability && data.explainability.length > 0) {
            data.explainability.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                explainList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = "No specific suspicious indicators found.";
            explainList.appendChild(li);
        }

        // Show panel with animation
        resultPanel.classList.remove('hidden');
        resultPanel.scrollIntoView({ behavior: 'smooth' });
    }

    clearBtn.addEventListener('click', () => {
        document.getElementById('email-subject').value = '';
        document.getElementById('email-body').value = '';
        resultPanel.classList.add('hidden');
        currentEmailData = null;
    });

    // Report Generation
    document.getElementById('download-report-btn').addEventListener('click', async () => {
        if (!currentEmailData) return;
        
        try {
            const btn = document.getElementById('download-report-btn');
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
            btn.disabled = true;

            const response = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentEmailData)
            });

            if (response.ok) {
                // Handle PDF download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `PhishGuard_Report_${new Date().getTime()}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                showToast("Report downloaded successfully.", "success");
            } else {
                showToast("Failed to generate report.", "error");
            }
        } catch (error) {
            console.error("Report error:", error);
            showToast("Network error generating report.", "error");
        } finally {
            const btn = document.getElementById('download-report-btn');
            btn.innerHTML = '<i class="fa-solid fa-download"></i> Download PDF Report';
            btn.disabled = false;
        }
    });

    // Train Model
    document.getElementById('train-model-btn').addEventListener('click', async () => {
        const btn = document.getElementById('train-model-btn');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Retraining...';
        btn.disabled = true;
        
        showToast("Model training started. This may take a moment...", "info");

        try {
            const response = await fetch('/api/train', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                showToast("Model retrained successfully!", "success");
                chartsInitialized = false; // Force refresh charts next time dashboard is opened
                if (document.getElementById('dashboard').classList.contains('active')) {
                    loadDashboardData();
                }
            } else {
                showToast("Training failed: " + data.error, "error");
            }
        } catch (error) {
            console.error("Training error:", error);
            showToast("Network error during training.", "error");
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-brain"></i> Retrain Model';
            btn.disabled = false;
        }
    });
});
