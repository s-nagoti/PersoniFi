"""
Professional Plotly Chart Styling for PersoniFi
Generates polished, consistent charts for financial data visualization
"""

from typing import List, Optional, Union, Dict, Any
from models import (
    PlotlyChart, PlotlyTrace, PlotlyLayout, PlotlyAxis, 
    PlotlyMargin, PlotlyMarker
)

# Professional color palette
COLORS = {
    'primary': ['#4F46E5', '#7C3AED', '#EC4899', '#F59E0B', '#10B981', '#EF4444', '#6366F1', '#8B5CF6'],
    'gradients': ['rgba(79, 70, 229, 0.8)', 'rgba(124, 58, 237, 0.8)', 'rgba(236, 72, 153, 0.8)', 
                  'rgba(245, 158, 11, 0.8)', 'rgba(16, 185, 129, 0.8)', 'rgba(239, 68, 68, 0.8)'],
    'background': {
        'plot': '#FAFAFA',
        'paper': '#FFFFFF'
    },
    'text': '#374151',
    'grid': '#E5E7EB'
}

def create_styled_chart(
    chart_type: str,
    title: str,
    x_data: Optional[List] = None,
    y_data: Optional[List] = None,
    labels: Optional[List] = None,
    values: Optional[List] = None,
    trace_name: Optional[str] = None,
    x_axis_title: str = "Category",
    y_axis_title: str = "Amount ($)",
    color_scheme: str = "primary"
) -> PlotlyChart:
    """
    Create a professionally styled Plotly chart with consistent branding.
    
    Args:
        chart_type: Type of chart ('bar', 'line', 'pie', 'area', 'scatter')
        title: Chart title
        x_data: X-axis data (for bar, line, area, scatter)
        y_data: Y-axis data (for bar, line, area, scatter)
        labels: Labels for pie charts
        values: Values for pie charts
        trace_name: Name for the data trace
        x_axis_title: Title for x-axis
        y_axis_title: Title for y-axis
        color_scheme: Color scheme to use ('primary', 'gradients')
    
    Returns:
        PlotlyChart: Fully styled chart object
    """
    
    # Select colors based on scheme
    colors = COLORS[color_scheme] if color_scheme in COLORS else COLORS['primary']
    
    # Create trace based on chart type
    if chart_type == 'pie':
        if not (labels and values):
            raise ValueError("Pie charts require both labels and values")
        
        trace = PlotlyTrace(
            type='pie',
            labels=labels,
            values=values,
            name=trace_name or "Distribution",
            marker=PlotlyMarker(
                colors=colors[:len(labels)],
                line={"color": "#FFFFFF", "width": 2}
            ),
            textinfo="label+percent",
            textfont={"size": 12, "color": COLORS['text']},
            hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
        )
        
        # Pie chart layout (no axes)
        layout = PlotlyLayout(
            title={
                "text": f"<b>{title}</b>",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": COLORS['text'], "family": "Arial, sans-serif"}
            },
            margin=PlotlyMargin(t=60, l=20, r=20, b=20),
            plot_bgcolor=COLORS['background']['plot'],
            paper_bgcolor=COLORS['background']['paper'],
            showlegend=True,
            legend={
                "orientation": "v",
                "yanchor": "middle",
                "y": 0.5,
                "xanchor": "left",
                "x": 1.05,
                "font": {"size": 11, "color": COLORS['text']}
            },
            font={"family": "Arial, sans-serif", "color": COLORS['text']}
        )
    
    else:
        # Bar, line, area, scatter charts
        if not (x_data and y_data):
            raise ValueError(f"{chart_type} charts require both x_data and y_data")
        
        # Determine marker/line styling based on chart type
        if chart_type == 'bar':
            marker = PlotlyMarker(
                color=colors[0],
                line={"color": "#FFFFFF", "width": 1}
            )
            trace_kwargs = {
                "marker": marker,
                "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
            }
        
        elif chart_type == 'line':
            marker = PlotlyMarker(
                color=colors[0],
                size=8,
                line={"color": "#FFFFFF", "width": 2}
            )
            trace_kwargs = {
                "mode": "lines+markers",
                "line": {"color": colors[0], "width": 3},
                "marker": marker,
                "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
            }
        
        elif chart_type == 'area':
            trace_kwargs = {
                "fill": "tonexty" if trace_name else "tozeroy",
                "fillcolor": colors[0].replace(')', ', 0.3)').replace('rgb', 'rgba') if 'rgb' in colors[0] else f"{colors[0]}40",
                "line": {"color": colors[0], "width": 2},
                "mode": "lines",
                "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
            }
        
        else:  # scatter
            marker = PlotlyMarker(
                color=colors[0],
                size=10,
                line={"color": "#FFFFFF", "width": 1}
            )
            trace_kwargs = {
                "mode": "markers",
                "marker": marker,
                "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
            }
        
        trace = PlotlyTrace(
            type=chart_type,
            x=x_data,
            y=y_data,
            name=trace_name or "Financial Data",
            **trace_kwargs
        )
        
        # Chart layout with axes
        layout = PlotlyLayout(
            title={
                "text": f"<b>{title}</b>",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": COLORS['text'], "family": "Arial, sans-serif"}
            },
            xaxis=PlotlyAxis(
                title={"text": f"<b>{x_axis_title}</b>", "font": {"size": 14, "color": COLORS['text']}},
                tickfont={"size": 11, "color": COLORS['text']},
                gridcolor=COLORS['grid'],
                gridwidth=1,
                showgrid=True,
                zeroline=False
            ),
            yaxis=PlotlyAxis(
                title={"text": f"<b>{y_axis_title}</b>", "font": {"size": 14, "color": COLORS['text']}},
                tickfont={"size": 11, "color": COLORS['text']},
                tickformat="$,.0f",
                gridcolor=COLORS['grid'],
                gridwidth=1,
                showgrid=True,
                zeroline=False
            ),
            margin=PlotlyMargin(t=60, l=80, r=40, b=60),
            plot_bgcolor=COLORS['background']['plot'],
            paper_bgcolor=COLORS['background']['paper'],
            showlegend=bool(trace_name),
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
                "font": {"size": 11, "color": COLORS['text']}
            },
            font={"family": "Arial, sans-serif", "color": COLORS['text']},
            hovermode="x unified" if chart_type in ['line', 'area'] else "closest"
        )
    
    return PlotlyChart(
        data=[trace],
        layout=layout
    )


def create_multi_trace_chart(
    chart_type: str,
    title: str,
    traces_data: List[Dict[str, Any]],
    x_axis_title: str = "Category",
    y_axis_title: str = "Amount ($)",
    color_scheme: str = "primary"
) -> PlotlyChart:
    """
    Create a chart with multiple data traces (for comparing multiple series).
    
    Args:
        chart_type: Type of chart ('bar', 'line', 'area', 'scatter')
        title: Chart title
        traces_data: List of trace dictionaries with keys: 'name', 'x', 'y'
        x_axis_title: Title for x-axis
        y_axis_title: Title for y-axis
        color_scheme: Color scheme to use
    
    Returns:
        PlotlyChart: Multi-trace styled chart object
    """
    colors = COLORS[color_scheme] if color_scheme in COLORS else COLORS['primary']
    traces = []
    
    for i, trace_data in enumerate(traces_data):
        color = colors[i % len(colors)]
        
        if chart_type == 'bar':
            marker = PlotlyMarker(
                color=color,
                line={"color": "#FFFFFF", "width": 1}
            )
            trace_kwargs = {
                "marker": marker,
                "hovertemplate": f"<b>{trace_data['name']}</b><br>%{{x}}: $%{{y:,.2f}}<extra></extra>"
            }
        
        elif chart_type == 'line':
            marker = PlotlyMarker(
                color=color,
                size=6,
                line={"color": "#FFFFFF", "width": 2}
            )
            trace_kwargs = {
                "mode": "lines+markers",
                "line": {"color": color, "width": 3},
                "marker": marker,
                "hovertemplate": f"<b>{trace_data['name']}</b><br>%{{x}}: $%{{y:,.2f}}<extra></extra>"
            }
        
        else:  # area, scatter
            trace_kwargs = {
                "mode": "lines" if chart_type == 'area' else "markers",
                "line": {"color": color, "width": 2} if chart_type == 'area' else None,
                "fill": "tonexty" if i > 0 and chart_type == 'area' else "tozeroy" if chart_type == 'area' else None,
                "fillcolor": color.replace(')', ', 0.3)').replace('rgb', 'rgba') if 'rgb' in color and chart_type == 'area' else f"{color}40" if chart_type == 'area' else None,
                "marker": PlotlyMarker(color=color, size=8) if chart_type == 'scatter' else None,
                "hovertemplate": f"<b>{trace_data['name']}</b><br>%{{x}}: $%{{y:,.2f}}<extra></extra>"
            }
        
        trace = PlotlyTrace(
            type=chart_type,
            x=trace_data['x'],
            y=trace_data['y'],
            name=trace_data['name'],
            **{k: v for k, v in trace_kwargs.items() if v is not None}
        )
        traces.append(trace)
    
    layout = PlotlyLayout(
        title={
            "text": f"<b>{title}</b>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18, "color": COLORS['text'], "family": "Arial, sans-serif"}
        },
        xaxis=PlotlyAxis(
            title={"text": f"<b>{x_axis_title}</b>", "font": {"size": 14, "color": COLORS['text']}},
            tickfont={"size": 11, "color": COLORS['text']},
            gridcolor=COLORS['grid'],
            gridwidth=1,
            showgrid=True,
            zeroline=False
        ),
        yaxis=PlotlyAxis(
            title={"text": f"<b>{y_axis_title}</b>", "font": {"size": 14, "color": COLORS['text']}},
            tickfont={"size": 11, "color": COLORS['text']},
            tickformat="$,.0f",
            gridcolor=COLORS['grid'],
            gridwidth=1,
            showgrid=True,
            zeroline=False
        ),
        margin=PlotlyMargin(t=60, l=80, r=40, b=60),
        plot_bgcolor=COLORS['background']['plot'],
        paper_bgcolor=COLORS['background']['paper'],
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 11, "color": COLORS['text']}
        },
        font={"family": "Arial, sans-serif", "color": COLORS['text']},
        hovermode="x unified" if chart_type in ['line', 'area'] else "closest"
    )
    
    return PlotlyChart(
        data=traces,
        layout=layout
    )


# Usage Example: Restaurants vs Gas spending comparison
if __name__ == "__main__":
    # Example 1: Single trace bar chart
    restaurants_vs_gas_chart = create_styled_chart(
        chart_type="bar",
        title="Spending Comparison: Restaurants vs Gas (Jul 1 - Aug 31, 2025)",
        x_data=["Restaurants", "Gas"],
        y_data=[650, 320],
        trace_name="Monthly Spending",
        x_axis_title="Category",
        y_axis_title="Total Amount ($)"
    )
    
    print("Single Trace Chart Structure:")
    print(f"Data traces: {len(restaurants_vs_gas_chart.data)}")
    print(f"Chart type: {restaurants_vs_gas_chart.data[0].type}")
    print(f"Title: {restaurants_vs_gas_chart.layout.title}")
    print()
    
    # Example 2: Multi-trace line chart for spending over time
    monthly_spending_chart = create_multi_trace_chart(
        chart_type="line",
        title="Monthly Spending Trends: Restaurants vs Gas",
        traces_data=[
            {
                "name": "Restaurants",
                "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                "y": [450, 520, 380, 610, 650]
            },
            {
                "name": "Gas",
                "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                "y": [280, 320, 250, 340, 320]
            }
        ],
        x_axis_title="Month",
        y_axis_title="Amount Spent ($)"
    )
    
    print("Multi-Trace Chart Structure:")
    print(f"Data traces: {len(monthly_spending_chart.data)}")
    print(f"Chart type: {monthly_spending_chart.data[0].type}")
    print(f"Trace names: {[trace.name for trace in monthly_spending_chart.data]}")
    print()
    
    # Example 3: Pie chart for category breakdown
    category_pie_chart = create_styled_chart(
        chart_type="pie",
        title="Spending Distribution by Category",
        labels=["Restaurants", "Gas", "Groceries", "Entertainment", "Utilities"],
        values=[650, 320, 480, 200, 150],
        trace_name="Category Breakdown"
    )
    
    print("Pie Chart Structure:")
    print(f"Chart type: {category_pie_chart.data[0].type}")
    print(f"Labels: {category_pie_chart.data[0].labels}")
    print(f"Values: {category_pie_chart.data[0].values}")
