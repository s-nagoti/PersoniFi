# PersoniFi Frontend Integration Guide

## 🚀 Quick Start

### Prerequisites
1. **Backend Running**: Make sure your FastAPI backend is running on `http://localhost:8000`
2. **Node.js**: Version 16+ installed
3. **Dependencies**: Run `npm install` in the frontend directory

### Starting the Frontend

**Option 1: Using convenience scripts**
```bash
# Windows
.\start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

**Option 2: Manual start**
```bash
cd frontend
npm install
npm start
```

The React app will start at `http://localhost:3000`

## 🔌 Backend Integration

### API Endpoints Used

1. **`POST /api/ask-agent`**
   - **Purpose**: Send user queries to AI agent
   - **Request**: `{ "prompt": "user question" }`
   - **Response**: Structured response with insights and Plotly chart data

2. **`POST /api/upload-and-save`**
   - **Purpose**: Upload and save transaction files
   - **Request**: FormData with file
   - **Response**: Parsed transactions and save confirmation

### Response Formats Expected

**Ask Agent Response:**
```json
{
  "success": true,
  "intent": "spending_by_category",
  "filters": { "category": ["Food", "Gas"] },
  "insight": {
    "summary": "Brief insight summary",
    "explanation": "Detailed explanation",
    "chart": {
      "data": [...],  // Plotly data traces
      "layout": {...} // Plotly layout config
    }
  },
  "raw_data": {...}
}
```

**Upload Response:**
```json
{
  "success": true,
  "data": [...],  // Parsed transactions
  "metadata": {
    "total_transactions": 150,
    "original_filename": "file.csv"
  },
  "save_result": {
    "success": true,
    "transactions_inserted": 150
  }
}
```

## 🎨 Features Implemented

### 1. File Upload Integration
- **Drag & Drop**: Drop CSV/Excel files directly on the input area
- **Button Upload**: Click upload button to select files
- **Validation**: Checks file type and size
- **Progress**: Shows loading state during upload
- **Feedback**: Displays success/error messages

### 2. AI Chat Integration
- **Natural Language**: Ask questions in plain English
- **Real-time Charts**: Dynamic Plotly chart rendering
- **Insights Display**: Structured insight presentation
- **History**: Keeps track of recent queries

### 3. Chart Visualization
- **Plotly Integration**: Full Plotly.js support
- **Backend Styling**: Uses chart styles from backend
- **Responsive**: Charts adapt to screen size
- **Interactive**: Hover, zoom, pan capabilities

### 4. UX Features
- **Loading States**: Visual feedback during API calls
- **Error Handling**: User-friendly error messages
- **Responsive Design**: Works on mobile and desktop
- **Professional Styling**: Clean, modern interface

## 🛠️ Development Features

### Mock Data
- Development mode includes realistic mock responses
- Allows frontend development without backend
- Demonstrates expected data structures

### Environment Configuration
- Set `REACT_APP_API_URL` to change backend URL
- Automatic fallback to `http://localhost:8000`
- Development/production mode detection

### Error Handling
- Network error detection
- API error parsing
- User-friendly error messages
- Graceful fallbacks

## 📊 Chart Integration

### Plotly Configuration
- Professional styling with your brand colors
- Responsive layouts
- Interactive features enabled
- Custom hover templates

### Backend Chart Support
- Supports all chart types from your backend:
  - Bar charts (spending by category)
  - Line charts (trends over time)
  - Pie charts (expense breakdown)
  - Scatter plots (transaction analysis)

### Chart Styling
- Uses colors and fonts from your `chart_styling.py`
- Maintains consistent visual theme
- Professional appearance

## 🔍 Testing

### Manual Testing
1. **Start both servers**:
   - Backend: `python main.py` (port 8000)
   - Frontend: `npm start` (port 3000)

2. **Test file upload**:
   - Drag a CSV file to the input area
   - Check for success message
   - Verify transactions were saved

3. **Test AI queries**:
   - Ask: "What are my top spending categories?"
   - Verify chart appears
   - Check insights display

### Mock Mode Testing
- Set `NODE_ENV=development` for mock responses
- Test without backend running
- Verify UI behavior and styling

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure backend has CORS middleware configured
   - Check FastAPI CORS settings

2. **API Connection Failed**
   - Verify backend is running on port 8000
   - Check `REACT_APP_API_URL` environment variable

3. **File Upload Fails**
   - Check file size (max 10MB)
   - Verify file format (CSV, Excel only)
   - Check backend upload endpoint

4. **Charts Not Displaying**
   - Verify Plotly.js is installed
   - Check browser console for errors
   - Ensure chart data structure matches expected format

### Debug Tips
- Open browser DevTools Network tab
- Check API request/response in console
- Verify environment variables loaded
- Test with mock data first

## 📝 Customization

### Styling
- Modify CSS files in `src/components/`
- Update color scheme in CSS variables
- Adjust responsive breakpoints

### API Integration
- Update endpoints in `src/services/api.js`
- Modify request/response handling
- Add new API functions as needed

### Chart Configuration
- Customize Plotly config in `VisualizationPanel.js`
- Add new chart types
- Modify styling and interactions
