"""
Example of how to integrate the professional chart styling into main.py Step 3 fallback
This shows the specific code changes needed in your ask_agent_endpoint function
"""

# Add this import at the top of main.py
from chart_integration import generate_chart_for_intent

# Replace the Step 3 fallback section (around lines 1460-1520) with this:

def step_3_fallback_with_styled_charts(intent, extracted_filters, raw_data):
    """
    Enhanced Step 3 fallback that uses professional chart styling
    """
    logger.warning(f"Using fallback insight generation with professional styling for intent: {intent}")
    
    # Generate summary based on intent
    if intent == "total_spent":
        total_spent = raw_data.get("total_spent", 0)
        summary = f"Your total spending was ${total_spent:,.2f} for the selected period."
        explanation = "A bar chart clearly displays the total amount spent, making it easy to understand your spending magnitude."
    
    elif intent == "total_income":
        total_income = raw_data.get("total_income", 0)
        summary = f"Your total income was ${total_income:,.2f} for the selected period."
        explanation = "A bar chart effectively shows your total income in a clear, easy-to-read format."
    
    elif intent == "spending_by_category":
        categories_data = raw_data.get("total_by_category", {})
        if categories_data:
            top_category = max(categories_data.items(), key=lambda x: x[1])
            total_spent = sum(categories_data.values())
            summary = f"You spent the most on {top_category[0]} (${top_category[1]:,.2f}) out of ${total_spent:,.2f} total spending."
        else:
            summary = "Category breakdown shows your spending distribution across different areas."
        explanation = "A bar chart is ideal for comparing spending across categories, clearly highlighting which areas dominate your budget."
    
    elif intent == "transactions_over_time":
        transaction_count = raw_data.get("transaction_count", 0)
        summary = f"Your transaction history shows {transaction_count} transactions over the selected time period."
        explanation = "A line chart effectively displays spending trends over time, making it easy to spot patterns and changes."
    
    elif intent == "balance_over_time":
        summary = "Your account balance changes are tracked over the selected time period."
        explanation = "An area chart visualizes balance trends effectively, showing how your account balance evolved over time."
    
    else:
        summary = f"Financial analysis completed for {intent.replace('_', ' ')}."
        explanation = "Chart type selected for optimal data visualization based on your query."
    
    # Generate professionally styled chart using the integration function
    try:
        plotly_chart = generate_chart_for_intent(
            intent=intent,
            raw_data=raw_data,
            chart_type="bar",  # Default, can be overridden based on intent
            filters=extracted_filters
        )
        logger.info(f"Successfully generated styled chart for intent: {intent}")
    except Exception as chart_error:
        logger.error(f"Failed to generate styled chart: {chart_error}")
        # Ultra-fallback to basic chart
        from main import PlotlyChart, PlotlyTrace, PlotlyLayout, PlotlyAxis, PlotlyMargin, PlotlyMarker
        plotly_chart = PlotlyChart(
            data=[
                PlotlyTrace(
                    type="bar",
                    x=["Analysis"],
                    y=[0],
                    marker=PlotlyMarker(color="rgba(156, 163, 175, 0.7)")
                )
            ],
            layout=PlotlyLayout(
                title="Financial Analysis",
                xaxis=PlotlyAxis(title="Category"),
                yaxis=PlotlyAxis(title="Amount ($)"),
                margin=PlotlyMargin(t=40, l=50, r=20, b=50),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
        )
    
    # Create FinancialInsight object
    from main import FinancialInsight
    insight = FinancialInsight(
        summary=summary,
        explanation=explanation,
        chart=plotly_chart
    )
    
    return insight


# Example of how this integrates into the main ask_agent_endpoint:
"""
# In your main.py ask_agent_endpoint function, replace the Step 3 fallback section with:

except Exception as e:
    logger.warning(f"Gemini Step 3 failed ({str(e)}), using fallback insight generation")
    
    # Use the enhanced fallback with professional styling
    insight = step_3_fallback_with_styled_charts(intent, extracted_filters, raw_data)
    
    # Return complete AskAgentResponse
    return AskAgentResponse(
        success=True,
        intent=intent,
        filters=extracted_filters,
        insight=insight,
        raw_data=raw_data,
        error=None
    )
"""

# Example usage and test
if __name__ == "__main__":
    # Simulate test data
    test_raw_data = {
        "total_by_category": {
            "Restaurants": 650,
            "Gas": 320,
            "Groceries": 480,
            "Entertainment": 200,
            "Utilities": 150
        },
        "total_spent": 1800,
        "transaction_count": 45
    }
    
    test_filters = {
        "start_date": "2025-07-01",
        "end_date": "2025-08-31"
    }
    
    # Test the fallback function
    test_insight = step_3_fallback_with_styled_charts(
        intent="spending_by_category",
        extracted_filters=test_filters,
        raw_data=test_raw_data
    )
    
    print("Generated Insight:")
    print(f"Summary: {test_insight.summary}")
    print(f"Explanation: {test_insight.explanation}")
    print(f"Chart Title: {test_insight.chart.layout.title}")
    print(f"Chart Type: {test_insight.chart.data[0].type}")
    print(f"Data Points: {len(test_insight.chart.data[0].x) if test_insight.chart.data[0].x else 'N/A'}")
