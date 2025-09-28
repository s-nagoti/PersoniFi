# PersoniFi Frontend

A modern React frontend for PersoniFi financial analysis application.

## Features

- **ChatGPT-style Layout**: Clean, professional interface with visualization panel and prompt box
- **File Upload**: Support for CSV and Excel transaction files
- **Interactive Charts**: Plotly.js integration for dynamic financial visualizations
- **AI Insights**: Natural language queries for financial analysis
- **Responsive Design**: Works on desktop and mobile devices

## Components

- `App` - Main application container
- `VisualizationPanel` - Displays Plotly charts and AI insights
- `PromptBox` - Input interface with upload and submit functionality

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Update the API URL in `.env` if needed:
```
REACT_APP_API_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

### Production

Build for production:
```bash
npm run build
```

## API Integration

The frontend communicates with the FastAPI backend through these endpoints:

- `POST /api/ask-agent` - Send queries to AI agent
- `POST /api/parse-transactions` - Upload and parse transaction files
- `POST /api/save-transactions` - Save parsed transactions to database

## File Support

Supported file formats for transaction upload:
- CSV files (.csv)
- Excel files (.xlsx, .xls)

## Development Features

- Mock API responses for development without backend
- Error handling and loading states
- Auto-resizing text input
- File validation

## Styling

The application uses custom CSS with a modern, clean design inspired by ChatGPT's interface. Key features:
- Responsive grid layout
- Smooth animations and transitions
- Professional color scheme
- Accessible design patterns

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
