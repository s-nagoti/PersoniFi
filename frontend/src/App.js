import React, { useState } from 'react';
import VisualizationPanel from './components/VisualizationPanel';
import PromptBox from './components/PromptBox';
import { askAgent, parseTransactions } from './services/api';
import './App.css';

function App() {
  const [chartData, setChartData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [insights, setInsights] = useState([]);

  const handlePromptSubmit = async (prompt) => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await askAgent(prompt);
      
      // Update chart data if provided
      if (response.chart_data) {
        setChartData(response.chart_data);
      }
      
      // Add insights to the list
      if (response.insights) {
        setInsights(prev => [...prev, {
          id: Date.now(),
          question: prompt,
          insights: response.insights,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (err) {
      setError(err.message || 'Failed to get response from AI agent');
      console.error('Error calling ask-agent:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await parseTransactions(file);
      
      // You can handle the parsed transactions here
      console.log('Parsed transactions:', response);
      
      // Show success message or update UI
      setInsights(prev => [...prev, {
        id: Date.now(),
        question: `Uploaded file: ${file.name}`,
        insights: [`Successfully parsed ${response.transaction_count || 0} transactions`],
        timestamp: new Date().toISOString()
      }]);
    } catch (err) {
      setError(err.message || 'Failed to upload and parse file');
      console.error('Error uploading file:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>PersoniFi</h1>
        <p>AI-Powered Financial Analysis</p>
      </header>
      
      <main className="app-main">
        <VisualizationPanel 
          chartData={chartData}
          insights={insights}
          isLoading={isLoading}
          error={error}
        />
        
        <PromptBox 
          onPromptSubmit={handlePromptSubmit}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}

export default App;
