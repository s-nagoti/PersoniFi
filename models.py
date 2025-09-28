"""
Pydantic models for PersoniFi FastAPI application
Separated to avoid circular imports
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# AI Agent Models for /api/ask-agent endpoint
class AskAgentRequest(BaseModel):
    """Request model for AI agent financial insights"""
    prompt: str = Field(..., description="User's natural language question about their finances", min_length=1, max_length=1000)

class PlotlyMarker(BaseModel):
    """Plotly marker configuration"""
    color: Optional[str] = Field(None, description="Marker color")
    line: Optional[Dict[str, Any]] = Field(None, description="Marker line configuration")
    size: Optional[int] = Field(None, description="Marker size")

class PlotlyTrace(BaseModel):
    """Plotly trace data structure"""
    type: str = Field(..., description="Chart type (e.g., 'bar', 'line', 'pie', 'scatter')")
    x: Optional[List[Any]] = Field(None, description="X-axis data")
    y: Optional[List[Any]] = Field(None, description="Y-axis data")
    values: Optional[List[float]] = Field(None, description="Values for pie charts")
    labels: Optional[List[str]] = Field(None, description="Labels for pie charts")
    name: Optional[str] = Field(None, description="Trace name")
    marker: Optional[PlotlyMarker] = Field(None, description="Marker styling")
    hovertemplate: Optional[str] = Field(None, description="Custom hover template")
    mode: Optional[str] = Field(None, description="Trace mode (e.g., 'lines+markers')")
    line: Optional[Dict[str, Any]] = Field(None, description="Line configuration")
    fill: Optional[str] = Field(None, description="Fill configuration for area charts")
    fillcolor: Optional[str] = Field(None, description="Fill color for area charts")
    
    class Config:
        extra = "allow"  # Allow additional fields that Plotly might use

class PlotlyAxis(BaseModel):
    """Plotly axis configuration"""
    title: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Axis title")
    tickfont: Optional[Dict[str, Any]] = Field(None, description="Tick font configuration")
    gridcolor: Optional[str] = Field(None, description="Grid color")
    showgrid: Optional[bool] = Field(None, description="Show grid lines")
    zeroline: Optional[bool] = Field(None, description="Show zero line")
    tickformat: Optional[str] = Field(None, description="Tick format")
    
    class Config:
        extra = "allow"  # Allow additional fields that Plotly might use

class PlotlyMargin(BaseModel):
    """Plotly margin configuration"""
    t: Optional[int] = Field(None, description="Top margin")
    l: Optional[int] = Field(None, description="Left margin")
    r: Optional[int] = Field(None, description="Right margin")
    b: Optional[int] = Field(None, description="Bottom margin")

class PlotlyLayout(BaseModel):
    """Plotly layout configuration"""
    title: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Chart title")
    xaxis: Optional[PlotlyAxis] = Field(None, description="X-axis configuration")
    yaxis: Optional[PlotlyAxis] = Field(None, description="Y-axis configuration")
    margin: Optional[PlotlyMargin] = Field(None, description="Chart margins")
    plot_bgcolor: Optional[str] = Field(None, description="Plot background color")
    paper_bgcolor: Optional[str] = Field(None, description="Paper background color")
    showlegend: Optional[bool] = Field(None, description="Show legend")
    legend: Optional[Dict[str, Any]] = Field(None, description="Legend configuration")
    font: Optional[Dict[str, Any]] = Field(None, description="Global font configuration")
    hovermode: Optional[str] = Field(None, description="Hover mode")
    
    class Config:
        extra = "allow"  # Allow additional fields that Plotly might use

class PlotlyChart(BaseModel):
    """Plotly-compatible chart structure"""
    data: List[PlotlyTrace] = Field(..., description="Chart data traces")
    layout: PlotlyLayout = Field(..., description="Chart layout configuration")

class FinancialInsight(BaseModel):
    """Model for financial insight with Plotly chart"""
    summary: str = Field(..., description="Brief summary of the financial insight")
    chart: PlotlyChart = Field(..., description="Plotly-compatible chart data")
    explanation: str = Field(..., description="Detailed explanation of why given chart was chosen")

class AskAgentResponse(BaseModel):
    """Response model for AI agent financial insights"""
    success: bool = Field(..., description="Whether the operation was successful")
    intent: Optional[str] = Field(None, description="Detected intent from user prompt")
    filters: Optional[Dict[str, Any]] = Field(None, description="Extracted filters for database query")
    insight: Optional[FinancialInsight] = Field(None, description="AI-generated financial insight with Plotly chart")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw database query results")
    error: Optional[str] = Field(None, description="Error message if operation failed")
