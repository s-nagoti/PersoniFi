import plotly.graph_objects as go
from chart_integration import generate_chart_for_intent

# Real API response JSON
response_json = {
  "success": True,
  "intent": "spending_by_category",
  "filters": {
    "category": [
      "groceries",
      "gas"
    ],
    "start_date": "2024-07-17",
    "end_date": "2024-08-12"
  },
  "insight": {
    "summary": "Between July 17 and August 12, 2024, your total spending on Groceries and Gas was $730.00. Groceries accounted for the majority of this expenditure ($550.00).",
    "chart": {
      "data": [
        {
          "type": "bar",
          "x": [
            "Groceries",
            "Gas"
          ],
          "y": [
            550,
            180
          ],
          "values": None,
          "labels": None,
          "name": "Spending",
          "marker": {
            "color": "#4F46E5",
            "line": {
              "color": "#FFFFFF",
              "width": 1
            },
            "size": None
          },
          "hovertemplate": "<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>",
          "mode": None,
          "line": None,
          "fill": None,
          "fillcolor": None
        }
      ],
      "layout": {
        "title": {
          "text": "<b>Spending Comparison: Groceries vs. Gas (Jul 17 - Aug 12, 2024)</b>",
          "x": 0.5,
          "xanchor": "center",
          "font": {
            "size": 18,
            "color": "#374151"
          }
        },
        "xaxis": {
          "title": {
            "text": "<b>Category</b>",
            "font": {
              "size": 14,
              "color": "#374151"
            }
          },
          "tickfont": {
            "size": 12
          },
          "gridcolor": "#E5E7EB",
          "showgrid": None,
          "zeroline": None,
          "tickformat": None
        },
        "yaxis": {
          "title": {
            "text": "<b>Amount ($)</b>",
            "font": {
              "size": 14,
              "color": "#374151"
            }
          },
          "tickfont": None,
          "gridcolor": "#E5E7EB",
          "showgrid": None,
          "zeroline": None,
          "tickformat": "$,.0f"
        },
        "margin": {
          "t": 60,
          "l": 80,
          "r": 40,
          "b": 60
        },
        "plot_bgcolor": "#FAFAFA",
        "paper_bgcolor": "#FFFFFF",
        "showlegend": None,
        "legend": None,
        "font": None,
        "hovermode": None
      }
    },
    "explanation": "A bar chart is the most effective way to compare the total spending magnitude between two distinct categories (groceries and gas) over the specified period. The vertical height of each bar clearly shows which category received the greater financial allocation, providing immediate visual comparison."
  },
  "raw_data": {
    "categories": {
      "Groceries": 550,
      "Gas": 180
    },
    "total_by_category": {
      "Groceries": 550,
      "Gas": 180
    }
  },
  "error": None
}

print("🧪 Testing Real API Response Data")
print("=" * 50)

# Extract data from the API response
intent = response_json['intent']
filters = response_json['filters']
raw_data = response_json['raw_data']
chart_type = response_json['insight']['chart']['data'][0]['type']

print(f"Intent: {intent}")
print(f"Filters: {filters}")
print(f"Raw data: {raw_data}")
print(f"Chart type: {chart_type}")

# Test 1: Use the integration function to generate a chart from the API data
print("\n📊 Test 1: Using chart_integration.generate_chart_for_intent()")
generated_chart = generate_chart_for_intent(
    intent=intent,
    raw_data=raw_data,
    chart_type=chart_type,
    filters=filters
)

print("✅ Chart generated using integration function")
print(f"   Title: {generated_chart.layout.title}")
print(f"   Data points: {len(generated_chart.data[0].x)}")
print(f"   Colors: {generated_chart.data[0].marker.color if generated_chart.data[0].marker else 'Default'}")

# Test 2: Use the original API response chart data directly
print("\n📊 Test 2: Using original API response chart data")
chart_data = response_json['insight']['chart']['data']
chart_layout = response_json['insight']['chart']['layout']

# Create Plotly traces from the API response
traces = []
for trace_json in chart_data:
    if trace_json['type'] == 'bar':
        # Clean the marker data - remove invalid properties for bar charts
        marker_data = trace_json.get('marker', {})
        if marker_data:
            # Remove 'size' property which is not valid for bar markers
            marker_data = {k: v for k, v in marker_data.items() if k != 'size' and v is not None}
        
        traces.append(
            go.Bar(
                x=trace_json['x'],
                y=trace_json['y'],
                name=trace_json.get('name'),
                marker=marker_data if marker_data else None,
                hovertemplate=trace_json.get('hovertemplate')
            )
        )
    # Add other types here if needed (line, pie, scatter, etc.)

# Create figure from API response
fig = go.Figure(data=traces, layout=chart_layout)

print("✅ Chart created from API response data")
print(f"   Title: {chart_layout['title']['text']}")
print(f"   Data points: {len(trace_json['x'])}")
print(f"   Colors: {trace_json['marker']['color']}")

# Show the chart from API response
print("\n🚀 Displaying Chart from API Response...")
fig.show()

print("\n✨ Both methods work!")
print("   - Integration function: Uses professional styling")
print("   - API response: Uses exact data from your endpoint")
print("   - Both should look similar but with different styling approaches")
