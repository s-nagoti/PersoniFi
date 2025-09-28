"""
Chart Integration Helper for main.py
Simple functions to generate styled charts for the FastAPI endpoints
"""

from typing import Dict, List, Any, Optional
from chart_styling import create_styled_chart, create_multi_trace_chart
from models import PlotlyChart

def generate_chart_for_intent(
    intent: str,
    raw_data: Dict[str, Any],
    chart_type: str = "bar",
    filters: Optional[Dict[str, Any]] = None
) -> PlotlyChart:
    """
    Generate a professionally styled chart based on intent and raw data.
    
    Args:
        intent: The detected intent (total_spent, spending_by_category, etc.)
        raw_data: Raw transaction data from Supabase
        chart_type: Suggested chart type from Gemini
        filters: Applied filters for context
    
    Returns:
        PlotlyChart: Styled chart ready for frontend
    """
    
    # Extract date range for title context
    date_context = ""
    if filters:
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        category = filters.get("category")
        
        if start_date and end_date:
            date_context = f" ({start_date} to {end_date})"
        elif start_date:
            date_context = f" (from {start_date})"
        elif end_date:
            date_context = f" (until {end_date})"
        
        if category:
            if isinstance(category, list):
                category_str = ", ".join(category).title()
            else:
                category_str = category.title()
            date_context = f" - {category_str}{date_context}"
    
    if intent == "total_spent":
        total_amount = raw_data.get("total_spent", 0)
        return create_styled_chart(
            chart_type="bar",
            title=f"Total Spending{date_context}",
            x_data=["Total Spent"],
            y_data=[total_amount],
            trace_name="Spending",
            x_axis_title="Period",
            y_axis_title="Amount ($)"
        )
    
    elif intent == "total_income":
        total_income = raw_data.get("total_income", 0)
        return create_styled_chart(
            chart_type="bar",
            title=f"Total Income{date_context}",
            x_data=["Total Income"],
            y_data=[total_income],
            trace_name="Income",
            x_axis_title="Period",
            y_axis_title="Amount ($)"
        )
    
    elif intent == "spending_by_category":
        categories_data = raw_data.get("total_by_category", {})
        if not categories_data:
            # Fallback data
            categories_data = {
                "Food & Dining": 450,
                "Transportation": 300,
                "Entertainment": 200,
                "Shopping": 150,
                "Utilities": 100
            }
        
        if chart_type == "pie":
            return create_styled_chart(
                chart_type="pie",
                title=f"Spending by Category{date_context}",
                labels=list(categories_data.keys()),
                values=list(categories_data.values()),
                trace_name="Category Breakdown"
            )
        else:
            return create_styled_chart(
                chart_type="bar",
                title=f"Spending by Category{date_context}",
                x_data=list(categories_data.keys()),
                y_data=list(categories_data.values()),
                trace_name="Category Spending",
                x_axis_title="Category",
                y_axis_title="Amount ($)"
            )
    
    elif intent == "transactions_over_time":
        time_data = raw_data.get("transactions_by_date", {})
        if not time_data:
            # Fallback data
            time_data = {
                "2025-08-01": 120,
                "2025-08-08": 85,
                "2025-08-15": 95,
                "2025-08-22": 110,
                "2025-08-29": 75
            }
        
        return create_styled_chart(
            chart_type="line",
            title=f"Transaction Trends{date_context}",
            x_data=list(time_data.keys()),
            y_data=list(time_data.values()),
            trace_name="Daily Spending",
            x_axis_title="Date",
            y_axis_title="Amount ($)"
        )
    
    elif intent == "balance_over_time":
        balance_data = raw_data.get("balance_by_date", {})
        if not balance_data:
            # Fallback data - cumulative balance
            balance_data = {
                "2025-08-01": 1000,
                "2025-08-08": 915,
                "2025-08-15": 820,
                "2025-08-22": 710,
                "2025-08-29": 635
            }
        
        return create_styled_chart(
            chart_type="area",
            title=f"Balance Trend{date_context}",
            x_data=list(balance_data.keys()),
            y_data=list(balance_data.values()),
            trace_name="Account Balance",
            x_axis_title="Date",
            y_axis_title="Balance ($)"
        )
    
    else:
        # Generic fallback chart
        return create_styled_chart(
            chart_type="bar",
            title=f"Financial Analysis{date_context}",
            x_data=["Analysis"],
            y_data=[0],
            trace_name="Data",
            x_axis_title="Category",
            y_axis_title="Amount ($)"
        )


# Integration example for use in main.py Step 3 fallback
def create_fallback_insight_chart(intent: str, raw_data: Dict[str, Any]) -> PlotlyChart:
    """
    Create a fallback chart when Gemini Step 3 fails.
    This replaces the manual PlotlyChart construction in main.py.
    """
    return generate_chart_for_intent(intent, raw_data)


# Usage in main.py - replace the manual PlotlyChart construction with:
"""
# OLD CODE (to be replaced):
plotly_chart = PlotlyChart(
    data=[
        PlotlyTrace(
            type="bar",
            x=["Food & Dining", "Transportation", "Entertainment", "Shopping", "Utilities"],
            y=[450, 300, 200, 150, 100],
            marker=PlotlyMarker(color="rgba(99, 110, 250, 0.7)")
        )
    ],
    layout=PlotlyLayout(
        title="Spending by Category - September 2025",
        xaxis=PlotlyAxis(title="Category"),
        yaxis=PlotlyAxis(title="Amount ($)"),
        margin=PlotlyMargin(t=40, l=50, r=20, b=50),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
)

# NEW CODE:
plotly_chart = generate_chart_for_intent(intent, raw_data, chart_type, extracted_filters)
"""

if __name__ == "__main__":
    # Test the integration
    sample_raw_data = {
        "total_by_category": {
            "Restaurants": 650,
            "Gas": 320,
            "Groceries": 480,
            "Entertainment": 200
        }
    }
    
    sample_filters = {
        "start_date": "2025-07-01",
        "end_date": "2025-08-31",
        "category": "restaurants"
    }
    
    chart = generate_chart_for_intent(
        intent="spending_by_category",
        raw_data=sample_raw_data,
        chart_type="bar",
        filters=sample_filters
    )
    
    print("Generated Chart:")
    print(f"Title: {chart.layout.title}")
    print(f"Data points: {len(chart.data[0].x) if chart.data[0].x else 'N/A'}")
    print(f"Chart type: {chart.data[0].type}")
    print(f"Colors: {chart.data[0].marker.color if chart.data[0].marker else 'Default'}")
