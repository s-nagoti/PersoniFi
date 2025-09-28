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
      query: prompt,
      // Add additional context if needed
      context: {
        timestamp: new Date().toISOString(),
        session_id: generateSessionId()
      }
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
 * Upload and parse transaction files (CSV/Excel)
 * @param {File} file - File to upload
 * @returns {Promise<Object>} Parsed transaction data
 */
export const parseTransactions = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/parse-transactions', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error parsing transactions:', error);
    
    // Return mock data for development/testing
    if (process.env.NODE_ENV === 'development') {
      return getMockParseResponse(file);
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
      insights: [
        "Your top spending category is Food & Dining at $1,247 this month.",
        "You've spent 23% more on transportation compared to last month.",
        "Consider setting a budget for entertainment expenses."
      ],
      chart_data: {
        data: [
          {
            x: ['Food & Dining', 'Transportation', 'Shopping', 'Entertainment', 'Bills'],
            y: [1247, 543, 432, 298, 1876],
            type: 'bar',
            marker: { color: ['#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444'] },
            name: 'Spending by Category'
          }
        ],
        layout: {
          title: 'Monthly Spending by Category',
          xaxis: { title: 'Category' },
          yaxis: { title: 'Amount ($)' },
          margin: { t: 60, r: 50, b: 60, l: 80 }
        }
      }
    },
    'trends': {
      insights: [
        "Your spending has increased by 12% over the last 3 months.",
        "There's a notable spike in dining expenses during weekends.",
        "Your savings rate is currently at 18% of income."
      ],
      chart_data: {
        data: [
          {
            x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            y: [2340, 2156, 2543, 2789, 2456, 2678],
            type: 'scatter',
            mode: 'lines+markers',
            marker: { color: '#3b82f6' },
            name: 'Monthly Spending'
          }
        ],
        layout: {
          title: 'Spending Trends Over Time',
          xaxis: { title: 'Month' },
          yaxis: { title: 'Total Spending ($)' },
          margin: { t: 60, r: 50, b: 60, l: 80 }
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
    insights: [
      "I've analyzed your financial data based on your question.",
      "Here are some key insights from your transaction history.",
      "Feel free to ask more specific questions about your finances!"
    ],
    chart_data: null
  };
};

/**
 * Mock response for parse-transactions endpoint (development only)
 * @param {File} file - Uploaded file
 * @returns {Object} Mock parse response
 */
const getMockParseResponse = (file) => {
  return {
    success: true,
    message: `Successfully parsed ${file.name}`,
    transaction_count: Math.floor(Math.random() * 100) + 50,
    file_info: {
      name: file.name,
      size: file.size,
      type: file.type
    },
    sample_transactions: [
      {
        date: '2024-01-15',
        description: 'GROCERY STORE PURCHASE',
        amount: -87.43,
        category: 'Food & Dining'
      },
      {
        date: '2024-01-14',
        description: 'SALARY DEPOSIT',
        amount: 3500.00,
        category: 'Income'
      },
      {
        date: '2024-01-13',
        description: 'GAS STATION',
        amount: -45.67,
        category: 'Transportation'
      }
    ]
  };
};

export default api;
