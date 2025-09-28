import React from 'react';
import Plot from 'react-plotly.js';
import './VisualizationPanel.css';

const VisualizationPanel = ({ chartData, insights, currentInsight, isLoading, error }) => {
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
      
     
    </div>
  );
};

export default VisualizationPanel;
