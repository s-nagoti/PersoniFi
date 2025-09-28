import React from 'react';
import Plot from 'react-plotly.js';
import './VisualizationPanel.css';

const VisualizationPanel = ({ chartData, insights, isLoading, error }) => {
  // Default placeholder chart data
  const defaultChartData = {
    data: [
      {
        x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        y: [1200, 1500, 1100, 1800, 1600, 2000],
        type: 'scatter',
        mode: 'lines+markers',
        marker: { color: '#3b82f6' },
        name: 'Monthly Spending'
      }
    ],
    layout: {
      title: {
        text: 'Financial Overview',
        font: { size: 18, family: 'Arial, sans-serif' }
      },
      xaxis: { title: 'Month' },
      yaxis: { title: 'Amount ($)' },
      margin: { t: 60, r: 50, b: 60, l: 80 },
      plot_bgcolor: '#ffffff',
      paper_bgcolor: '#ffffff',
      font: { family: 'Arial, sans-serif', size: 12 }
    }
  };

  const displayChartData = chartData || defaultChartData;

  return (
    <div className="visualization-panel">
      <div className="chart-container">
        {isLoading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Analyzing your data...</p>
          </div>
        )}
        
        {error && (
          <div className="error-message">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}
        
        {!isLoading && !error && (
          <Plot
            data={displayChartData.data}
            layout={{
              ...displayChartData.layout,
              autosize: true,
              responsive: true
            }}
            style={{ width: '100%', height: '100%' }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
            }}
          />
        )}
      </div>
      
      <div className="insights-container">
        <h3>AI Insights</h3>
        <div className="insights-list">
          {insights.length === 0 ? (
            <div className="empty-state">
              <p>Upload a file or ask a question to get started!</p>
              <p className="empty-state-subtitle">
                Try asking: "What are my top spending categories?" or "Show me my monthly trends"
              </p>
            </div>
          ) : (
            insights.map((insight) => (
              <div key={insight.id} className="insight-item">
                <div className="insight-question">
                  <strong>Q:</strong> {insight.question}
                </div>
                <div className="insight-response">
                  {insight.insights.map((text, index) => (
                    <p key={index}>{text}</p>
                  ))}
                </div>
                <div className="insight-timestamp">
                  {new Date(insight.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualizationPanel;
