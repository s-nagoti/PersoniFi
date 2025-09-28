import React, { useState, useRef } from 'react';
import './PromptBox.css';

const PromptBox = ({ onPromptSubmit, onFileUpload, isLoading }) => {
  const [prompt, setPrompt] = useState('');
  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onPromptSubmit(prompt);
      setPrompt('');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileUpload(file);
      // Reset the file input
      e.target.value = '';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const isValidFileType = (file) => {
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    return validTypes.includes(file.type) || file.name.match(/\.(csv|xls|xlsx)$/i);
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (isValidFileType(file)) {
        onFileUpload(file);
      } else {
        alert('Please upload a valid CSV or Excel file');
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="prompt-box">
      <form onSubmit={handleSubmit} className="prompt-form">
        <div 
          className="input-container"
          onDrop={handleFileDrop}
          onDragOver={handleDragOver}
        >
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your finances or drag & drop a CSV/Excel file..."
            className="prompt-input"
            rows={1}
            disabled={isLoading}
          />
          
          <div className="action-buttons">
            <button
              type="button"
              onClick={triggerFileUpload}
              className="upload-button"
              disabled={isLoading}
              title="Upload CSV or Excel file"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14,2 14,8 20,8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10,9 9,9 8,9" />
              </svg>
              Upload
            </button>
            
            <button
              type="submit"
              className="submit-button"
              disabled={isLoading || !prompt.trim()}
            >
              {isLoading ? (
                <div className="spinner"></div>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22,2 15,22 11,13 2,9 22,2" />
                </svg>
              )}
            </button>
          </div>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xls,.xlsx"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </form>
      
      <div className="prompt-footer">
        <p className="upload-info">
          📁 Drag & drop files or click Upload • Supported: CSV, Excel (.xlsx, .xls) • Max 10MB
          <br />
          <span className="examples">
            💡 Try: "What are my top spending categories?" • "Show monthly trends" • "Analyze my expenses"
          </span>
        </p>
      </div>
    </div>
  );
};

export default PromptBox;
