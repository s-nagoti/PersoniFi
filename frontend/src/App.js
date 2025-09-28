import React, { useState } from 'react';
import VisualizationPanel from './components/VisualizationPanel';
import PromptBox from './components/PromptBox';
import { askAgent, uploadAndSaveTransactions } from './services/api';
import './App.css';

function App() {
  const [chartData, setChartData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [insights, setInsights] = useState([]);
  const [currentInsight, setCurrentInsight] = useState(null);

  const handlePromptSubmit = async (prompt) => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await askAgent(prompt);
      
      if (response.success && response.insight) {
        // Update chart data from the insight
        if (response.insight.chart) {
          setChartData(response.insight.chart);
        }
        
        // Set current insight for display
        setCurrentInsight(response.insight);
        
        // Add to insights history
        setInsights(prev => [...prev, {
          id: Date.now(),
          question: prompt,
          summary: response.insight.summary,
          explanation: response.insight.explanation,
          intent: response.intent,
          timestamp: new Date().toISOString()
        }]);
      } else {
        setError(response.error || 'No insights returned from AI agent');
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
      const response = await uploadAndSaveTransactions(file);
      
      if (response.success) {
        // Show success message
        const transactionCount = response.metadata?.total_transactions || response.data?.length || 0;
        const savedCount = response.save_result?.transactions_inserted || transactionCount;
        
        setInsights(prev => [...prev, {
          id: Date.now(),
          question: `Uploaded file: ${file.name}`,
          summary: `Successfully processed and saved ${savedCount} transactions`,
          explanation: `File processed: ${response.metadata?.original_filename || file.name}. ${savedCount} transactions were saved to the database.`,
          intent: "file_upload",
          timestamp: new Date().toISOString()
        }]);
        
        console.log('Upload response:', response);
      } else {
        setError('Failed to upload and save transactions');
      }
    } catch (err) {
      setError(err.message || 'Failed to upload and save file');
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
          currentInsight={currentInsight}
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
