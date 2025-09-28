"""
Test the Pydantic models with the expected JSON structure
"""

from models import AskAgentResponse, FinancialInsight, PlotlyChart, PlotlyTrace, PlotlyLayout, PlotlyAxis, PlotlyMargin, PlotlyMarker

# Test data matching the system instruction example
test_data = {
    "success": True,
    "intent": "spending_by_category",
    "filters": {
        "category": "groceries",
        "start_date": "2025-08-01",
        "end_date": "2025-08-31"
    },
    "insight": {
        "summary": "You spent the most on groceries ($450) this month.",
        "chart": {
            "data": [
                {
                    "type": "bar",
                    "x": ["Groceries", "Transportation", "Entertainment"],
                    "y": [450, 300, 200],
                    "marker": {
                        "color": "#4F46E5",
                        "line": {"color": "#FFFFFF", "width": 1}
                    },
                    "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
                }
            ],
            "layout": {
                "title": {
                    "text": "<b>Spending by Category - August 2025</b>",
                    "x": 0.5,
                    "xanchor": "center",
                    "font": {"size": 18, "color": "#374151", "family": "Arial, sans-serif"}
                },
                "xaxis": {
                    "title": {"text": "<b>Category</b>", "font": {"size": 14, "color": "#374151"}},
                    "tickfont": {"size": 11, "color": "#374151"},
                    "gridcolor": "#E5E7EB",
                    "showgrid": True
                },
                "yaxis": {
                    "title": {"text": "<b>Amount ($)</b>", "font": {"size": 14, "color": "#374151"}},
                    "tickfont": {"size": 11, "color": "#374151"},
                    "tickformat": "$,.0f",
                    "gridcolor": "#E5E7EB",
                    "showgrid": True
                },
                "margin": {"t": 60, "l": 80, "r": 40, "b": 60},
                "plot_bgcolor": "#FAFAFA",
                "paper_bgcolor": "#FFFFFF",
                "font": {"family": "Arial, sans-serif", "color": "#374151"}
            }
        },
        "explanation": "A bar chart is ideal for comparing spending across categories."
    },
    "raw_data": {
        "transactions": [
            {"date": "2025-08-02", "merchant": "Whole Foods", "amount": 150, "category": "Groceries"},
            {"date": "2025-08-10", "merchant": "Trader Joe's", "amount": 300, "category": "Groceries"}
        ]
    },
    "error": None
}

try:
    # Test creating the response object
    response = AskAgentResponse(**test_data)
    print("✅ AskAgentResponse created successfully")
    print(f"Intent: {response.intent}")
    print(f"Summary: {response.insight.summary}")
    print(f"Chart type: {response.insight.chart.data[0].type}")
    print(f"Chart title: {response.insight.chart.layout.title}")
    
except Exception as e:
    print(f"❌ Error creating AskAgentResponse: {e}")
    print(f"Error type: {type(e).__name__}")
