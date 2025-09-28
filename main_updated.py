# This shows the changes needed for main.py

# 1. Change the endpoint decorator (around line 1019):
@app.post("/api/ask-agent", response_model=AskAgentResponse)  # Change this to return AskAgentResponse

# 2. Replace Step 3 placeholder (around lines 1239-1390) with this Gemini integration:

        # Step 3: Generate AI-powered insights using Gemini
        try:
            # Get chart recommendation from Gemini Step 1 (if available) or use defaults
            if 'chart' in locals() and chart:
                chart_type = chart.get("type", "bar")
                explanation = chart.get("justification", "Chart type selected for optimal data visualization")
            else:
                # Fallback chart recommendations based on intent
                if intent == "spending_by_category":
                    chart_type = "pie"
                    explanation = "Pie charts effectively show proportional breakdown of spending across categories"
                elif intent == "transactions_over_time":
                    chart_type = "line"
                    explanation = "Line charts are ideal for showing trends and changes over time"
                elif intent == "balance_over_time":
                    chart_type = "area"
                    explanation = "Area charts effectively show balance changes and trends over time"
                else:
                    chart_type = "bar"
                    explanation = "Bar charts clearly display total amounts for easy comparison"

            # Prepare input for Gemini Step 3 generation
            gemini_input = {
                "intent": intent,
                "filters": extracted_filters,
                "chart": {"type": chart_type, "justification": explanation},
                "explanation": explanation,
                "raw_data": raw_data
            }

            # Initialize Gemini client for Step 3 insight generation
            client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY"),
            )

            model = "gemini-flash-latest"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=json.dumps(gemini_input)),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                thinking_config = types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                system_instruction=[
                    types.Part.from_text(text="""You are a financial visualization AI assistant.  

Your task: Take the following inputs:
- "intent": the detected intent from the user's natural language query
- "filters": any extracted filters (e.g., category, start_date, end_date)
- "chart": a suggested Plotly chart type and associated details
- "explanation": a justification of why the chosen chart is appropriate
- "raw_data": raw transaction data retrieved from the Supabase database

Your output must strictly match the AskAgentResponse Pydantic model:

AskAgentResponse:
- success: bool → whether the request was successful
- intent: string → detected intent from user prompt
- filters: dict → extracted filters used for the database query
- insight: object → a FinancialInsight object containing:
    - summary: str → short, concise natural language summary of the insight
    - chart: object → a PlotlyChart object containing:
        - data: list of PlotlyTrace objects, each with:
            - type: str (bar, line, pie, scatter, etc.)
            - x: optional list of values for x-axis
            - y: optional list of values for y-axis
            - values: optional list of numbers (for pie charts)
            - labels: optional list of labels (for pie charts)
            - name: optional trace name
            - marker: optional marker object (with color)
        - layout: PlotlyLayout object with:
            - title: str
            - xaxis: optional axis configuration (title)
            - yaxis: optional axis configuration (title)
            - margin: optional margin object (t, l, r, b)
            - plot_bgcolor: optional
            - paper_bgcolor: optional
    - explanation: str → detailed justification of chart choice
- raw_data: dict → raw query results from the database
- error: optional str → error message if the operation failed

Constraints:
- Output must be valid JSON only, with **no extra text or markdown**.
- Ensure all fields required by the model are present.
- Summaries should be concise and insightful, not just descriptive.
- Chart objects must be valid and ready to render in Plotly (react-plotly.js).

Example output:

{
  "success": true,
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
          "marker": {"color": "rgba(99,110,250,0.7)"}
        }
      ],
      "layout": {
        "title": "Spending by Category - August 2025",
        "xaxis": {"title": "Category"},
        "yaxis": {"title": "Amount ($)"},
        "margin": {"t": 40, "l": 50, "r": 20, "b": 50},
        "plot_bgcolor": "white",
        "paper_bgcolor": "white"
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
  "error": null
}
"""),
                ],
            )

            # Collect the response from Gemini
            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text

            # Parse the JSON response from Gemini
            try:
                # Clean the response text - remove any markdown formatting
                clean_response = response_text.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()

                gemini_result = json.loads(clean_response)
                
                # Gemini should return the complete AskAgentResponse structure
                logger.info(f"Gemini generated complete response for intent: {intent}")
                return AskAgentResponse(**gemini_result)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini Step 3 response as JSON: {e}")
                logger.error(f"Raw Gemini response: {response_text}")
                raise Exception("Invalid JSON response from Gemini Step 3")

        except Exception as e:
            logger.warning(f"Gemini Step 3 failed ({str(e)}), using fallback insight generation")

            # FALLBACK: Create AskAgentResponse with simple insight
            if intent == "spending_by_category":
                summary = "You spent the most on Food & Dining ($450) this month, followed by Transportation ($300)."
                explanation = "A bar chart is the best choice because it clearly compares spending across categories, highlighting which ones dominate."
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
            else:
                summary = f"Analysis completed for {intent.replace('_', ' ')}."
                explanation = f"Chart type selected for optimal data visualization of {intent}."
                plotly_chart = PlotlyChart(
                    data=[
                        PlotlyTrace(
                            type="bar",
                            x=["Total"],
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

            # Create fallback insight object
            insight = FinancialInsight(
                summary=summary,
                explanation=explanation,
                chart=plotly_chart
            )

            logger.info(f"Generated fallback insight for intent: {intent}")

            # Return complete AskAgentResponse
            return AskAgentResponse(
                success=True,
                intent=intent,
                filters=extracted_filters,
                insight=insight,
                raw_data=raw_data,
                error=None
            )

# 3. Update the error handling (around lines 1403-1412):
    except Exception as e:
        logger.error(f"Error in ask-agent endpoint: {str(e)}")
        
        # Create error response with basic insight
        error_insight = FinancialInsight(
            summary="An error occurred while processing your request.",
            explanation="Unable to generate chart due to processing error.",
            chart=PlotlyChart(
                data=[
                    PlotlyTrace(
                        type="bar",
                        x=["Error"],
                        y=[0],
                        marker=PlotlyMarker(color="rgba(239, 68, 68, 0.7)")
                    )
                ],
                layout=PlotlyLayout(
                    title="Processing Error",
                    xaxis=PlotlyAxis(title="Status"),
                    yaxis=PlotlyAxis(title="Value"),
                    margin=PlotlyMargin(t=40, l=50, r=20, b=50),
                    plot_bgcolor="white",
                    paper_bgcolor="white"
                )
            )
        )
        
        return AskAgentResponse(
            success=False,
            intent=None,
            filters=None,
            insight=error_insight,
            raw_data=None,
            error=f"Failed to process request: {str(e)}"
        )
