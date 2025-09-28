# Project Context:
# - Name: PersoniFi (Personal Finance Visualization Agent)
# - Backend: FastAPI (Python)
# - Database: Supabase (PostgreSQL)
# - Current Features:
#   1. /api/parse-transactions → accepts CSV/Excel uploads, parses to structured JSON
#   2. /api/save-transactions → saves structured JSON into Supabase "transactions" table
#   3. /api/get-transactions → fetches transactions from Supabase
#   4. /api/ask-agent → receives a user prompt, calls Gemini AI
#       - Gemini outputs: intent, filters, summary, justification, chart_type
#       - Backend then queries Supabase using intent/filters and returns chart-ready JSON
#
# My Goal:
# - Debug issues in the code (especially Supabase queries + FastAPI endpoints)
# - Ensure each endpoint is working and testable via Postman
#
# Instructions for Copilot:
# - When I paste code here, analyze it against this project context
# - Help me identify mistakes, missing imports, wrong Supabase queries, or FastAPI misconfigurations
# - Suggest fixes with explanations, not just raw code
