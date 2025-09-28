import axios from 'axios';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error';
      throw new Error(`${error.response.status}: ${message}`);
    } else if (error.request) {
      // Network error
      throw new Error('Network error - please check your connection');
    } else {
      // Request setup error
      throw new Error('Request failed');
    }
  }
);

/**
 * Ask the AI agent a question and get insights with optional chart data
 * @param {string} prompt - User's question or prompt
 * @returns {Promise<Object>} Response containing insights and optional chart data
 */
export const askAgent = async (prompt) => {
  try {
    const response = await api.post('/api/ask-agent', {
      prompt: prompt
    });

    return response.data;
  } catch (error) {
    console.error('Error calling ask-agent:', error);
    
    // Return mock data for development/testing
    if (process.env.NODE_ENV === 'development') {
      return getMockAgentResponse(prompt);
    }
    
    throw error;
  }
};

/**
 * Upload and parse transaction files (CSV/Excel) and save to database
 * @param {File} file - File to upload
 * @returns {Promise<Object>} Parsed and saved transaction data
 */
export const uploadAndSaveTransactions = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/upload-and-save', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error uploading and saving transactions:', error);
    
    // Return mock data for development/testing
    if (process.env.NODE_ENV === 'development') {
      return getMockUploadResponse(file);
    }
    
    throw error;
  }
};

/**
 * Save parsed transaction data to database
 * @param {Array} transactions - Array of transaction objects
 * @returns {Promise<Object>} Save confirmation
 */
export const saveTransactions = async (transactions) => {
  try {
    const response = await api.post('/api/save-transactions', {
      transactions: transactions
    });

    return response.data;
  } catch (error) {
    console.error('Error saving transactions:', error);
    throw error;
  }
};

/**
 * Generate a unique session ID for tracking
 * @returns {string} Session ID
 */
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Mock response for ask-agent endpoint (development only)
 * @param {string} prompt - User prompt
 * @returns {Object} Mock response
 */
const getMockAgentResponse = (prompt) => {
  const mockResponses = {
    'spending': {
      success: true,
      intent: "spending_by_category",
      filters: { category: ["Food & Dining", "Transportation", "Shopping"] },
      insight: {
        summary: "Your top spending category is Food & Dining at $1,247 this month.",
        explanation: "Based on your transaction history, here's a breakdown of your spending by category. Food & Dining represents the largest portion of your expenses.",
        chart: {
          data: [
            {
              x: ['Food & Dining', 'Transportation', 'Shopping', 'Entertainment', 'Bills'],
              y: [1247, 543, 432, 298, 1876],
              type: 'bar',
              marker: { color: '#4F46E5' },
              name: 'Spending by Category'
            }
          ],
          layout: {
            title: {
              text: '<b>Monthly Spending by Category</b>',
              x: 0.5,
              xanchor: 'center',
              font: { size: 18, color: '#374151', family: 'Arial, sans-serif' }
            },
            xaxis: { 
              title: { text: 'Category', font: { size: 14, color: '#6b7280' } },
              tickfont: { color: '#6b7280' }
            },
            yaxis: { 
              title: { text: 'Amount ($)', font: { size: 14, color: '#6b7280' } },
              tickfont: { color: '#6b7280' }
            },
            margin: { t: 60, r: 50, b: 60, l: 80 },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff'
          }
        }
      }
    },
    'trends': {
      success: true,
      intent: "spending_trends",
      filters: { start_date: "2024-01-01", end_date: "2024-06-30" },
      insight: {
        summary: "Your spending has increased by 12% over the last 6 months.",
        explanation: "This chart shows your monthly spending trends. There's been a gradual increase in overall spending with some seasonal variations.",
        chart: {
          data: [
            {
              x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
              y: [2340, 2156, 2543, 2789, 2456, 2678],
              type: 'scatter',
              mode: 'lines+markers',
              marker: { color: '#4F46E5', size: 8 },
              line: { color: '#4F46E5', width: 3 },
              name: 'Monthly Spending'
            }
          ],
          layout: {
            title: {
              text: '<b>Spending Trends Over Time</b>',
              x: 0.5,
              xanchor: 'center',
              font: { size: 18, color: '#374151', family: 'Arial, sans-serif' }
            },
            xaxis: { 
              title: { text: 'Month', font: { size: 14, color: '#6b7280' } },
              tickfont: { color: '#6b7280' }
            },
            yaxis: { 
              title: { text: 'Total Spending ($)', font: { size: 14, color: '#6b7280' } },
              tickfont: { color: '#6b7280' }
            },
            margin: { t: 60, r: 50, b: 60, l: 80 },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff'
          }
        }
      }
    }
  };

  // Simple keyword matching for demo
  const lowerPrompt = prompt.toLowerCase();
  if (lowerPrompt.includes('spending') || lowerPrompt.includes('category')) {
    return mockResponses.spending;
  } else if (lowerPrompt.includes('trend') || lowerPrompt.includes('time') || lowerPrompt.includes('month')) {
    return mockResponses.trends;
  }

  // Default response
  return {
    success: true,
    intent: "general_inquiry",
    insight: {
      summary: "I've analyzed your financial data based on your question.",
      explanation: "Here are some key insights from your transaction history. Feel free to ask more specific questions about your finances!",
      chart: {
        data: [
          {
            x: ['Income', 'Expenses', 'Savings'],
            y: [5000, 3500, 1500],
            type: 'bar',
            marker: { color: '#4F46E5' },
            name: 'Financial Overview'
          }
        ],
        layout: {
          title: {
            text: '<b>Financial Overview</b>',
            x: 0.5,
            xanchor: 'center',
            font: { size: 18, color: '#374151', family: 'Arial, sans-serif' }
          },
          xaxis: { title: { text: 'Category', font: { size: 14, color: '#6b7280' } } },
          yaxis: { title: { text: 'Amount ($)', font: { size: 14, color: '#6b7280' } } },
          margin: { t: 60, r: 50, b: 60, l: 80 },
          plot_bgcolor: '#ffffff',
          paper_bgcolor: '#ffffff'
        }
      }
    }
  };
};

/**
 * Mock response for upload-and-save endpoint (development only)
 * @param {File} file - Uploaded file
 * @returns {Object} Mock upload response
 */
const getMockUploadResponse = (file) => {
  return {
    success: true,
    data: [
      {
        date: "2024-01-15",
        merchant: "GROCERY STORE PURCHASE",
        amount: -87.43,
        category: "Food & Dining"
      },
      {
        date: "2024-01-14", 
        merchant: "SALARY DEPOSIT",
        amount: 3500.00,
        category: "Income"
      },
      {
        date: "2024-01-13",
        merchant: "GAS STATION",
        amount: -45.67,
        category: "Transportation"
      }
    ],
    metadata: {
      total_transactions: Math.floor(Math.random() * 100) + 50,
      file_type: file.name.endsWith('.csv') ? 'csv' : 'excel',
      column_mapping: {
        date: "Transaction Date",
        amount: "Amount", 
        merchant: "Description",
        category: "Category"
      },
      original_filename: file.name,
      file_size: file.size,
      upload_timestamp: new Date().toISOString(),
      processing_time: new Date().toISOString()
    },
    save_result: {
      success: true,
      transactions_inserted: Math.floor(Math.random() * 100) + 50,
      message: "Transactions successfully saved to database"
    }
  };
};

export default api;
