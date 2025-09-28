import React from 'react';
import './SummaryPanel.css';

const SummaryPanel = ({ currentInsight, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="summary-panel">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing your financial data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="summary-panel error">
        <div className="error-content">
          <h3>❌ Error</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!currentInsight) {
    return (
      <div className="summary-panel empty">
        <div className="empty-content">
          <h3>📊 Ready for Analysis</h3>
          <p>Upload a file or ask a question to get AI-powered financial insights!</p>
          <div className="suggestions">
            <p><strong>Try asking:</strong></p>
            <ul>
              <li>"What are my top spending categories?"</li>
              <li>"Show me my monthly spending trends"</li>
              <li>"How much did I spend on groceries last month?"</li>
              <li>"Analyze my largest expenses"</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="summary-panel">
      <div className="summary-content">
        <div className="summary-header">
          <h3>🤖 AI Analysis</h3>
        </div>
        
        <div className="summary-section">
          <h4>Summary</h4>
          <p className="summary-text">{currentInsight.summary}</p>
        </div>
        
        <div className="explanation-section">
          <h4>Chart Justification</h4>
          <p className="explanation-text">{currentInsight.explanation}</p>
        </div>
      </div>
    </div>
  );
};

export default SummaryPanel;

