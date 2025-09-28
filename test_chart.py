import plotly.graph_objects as go

# Hardcoded example response
response_json = {
  "success": True,
  "intent": "spending_by_category",
  "filters": {
    "category": ["restaurants", "gas"],
    "start_date": "2025-07-01",
    "end_date": "2025-08-31"
  },
  "insight": {
    "summary": "Total spending on Restaurants and Gas between July 1st and August 31st, 2025, was $970.00. Restaurants were the dominant expense, totaling $650.00.",
    "chart": {
      "data": [
        {
          "type": "bar",
          "x": ["Restaurants", "Gas"],
          "y": [650, 320],
          "values": None,
          "labels": None,
          "name": "Spending",
          "marker": {"color": "rgba(255, 165, 0, 0.8)"}
        }
      ],
      "layout": {
        "title": "Spending Comparison: Restaurants vs. Gas (Jul 1 - Aug 31, 2025)",
        "xaxis": {"title": "Category"},
        "yaxis": {"title": "Total Amount ($)"},
        "margin": {"t": 40, "l": 50, "r": 20, "b": 50},
        "plot_bgcolor": "#f7f7f7",
        "paper_bgcolor": "white"
      }
    },
    "explanation": "A bar chart is the most effective visualization for comparing the magnitude of spending across specific, discrete categories (Restaurants and Gas). It clearly illustrates which category accumulated more expenses during the specified two-month period."
  },
  "raw_data": {},
  "error": None
}

# Extract chart info
chart_data = response_json['insight']['chart']['data']
chart_layout = response_json['insight']['chart']['layout']

# Create Plotly traces dynamically
traces = []
for trace_json in chart_data:
    if trace_json['type'] == 'bar':
        traces.append(
            go.Bar(
                x=trace_json['x'],
                y=trace_json['y'],
                name=trace_json.get('name'),
                marker=trace_json.get('marker')
            )
        )
    # Add other types here if needed (line, pie, scatter, etc.)

# Create figure
fig = go.Figure(data=traces, layout=chart_layout)

# Show chart in browser
fig.show()
