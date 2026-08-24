# Workflow / architecture demo reference — create-an-asset

Read this only when the chosen format is a workflow or architecture demo.

## Structure by complexity

| Components | Structure |
|------------|-----------|
| 3-5 | Single-view diagram with step annotations |
| 5-10 | Zoomable canvas with a step-by-step walkthrough |
| 10+ | Multi-layer view (overview → detail) with a guided tour |

## Standard elements

1. Title bar: `[Scenario Name] — Powered by [Seller Product]`
2. Component nodes — one box per system
3. Flow arrows — animated, showing data movement
4. Step panel — sidebar explaining the current step in plain language
5. Controls — Play / Pause / Step Forward / Step Back / Reset
6. Annotations — callouts at decision points and value-adds
7. Data preview — sample payload or transformation at each step

## Component definition

```yaml
component:
  id: "snowflake"
  label: "Snowflake Data Warehouse"
  type: "database"          # human | document | ai | database | api | middleware | output
  icon: "database"
  description: "Financial performance data"
  brand_color: "#29B5E8"
```

Types and what each means: `human` — person initiating or receiving; `document` —
PDFs, contracts, files; `ai` — models and agents; `database` — data stores;
`api` — services; `middleware` — integration platforms, MCP servers; `output` —
dashboards, reports, notifications.

## Step definition

```yaml
step:
  number: 1
  from: "human"
  to: "claude"
  action: "Initiates performance review"
  description: "Sarah, a Brand Analyst at [Prospect], kicks off the quarterly review..."
  data_example: "Review request: Nike brand, Q4 2025"
  duration: "~1 second"
  value_note: "No manual data gathering required"
```

`value_note` is the field that turns a diagram into a sales asset — it names what the
prospect stops doing at that step. A demo without value notes shows plumbing, not value.

## Scenario narrative

Name a real person in a real role at the prospect and follow one concrete task end to
end. Abstract flows ("the user submits a request") lose the room.

```
Step 1 — Human trigger
"Alex, a Brand Performance Analyst at [Client], needs to review Q4 performance for
the Nike license agreement. She opens the review dashboard and clicks 'Start Review'."

Step 2 — Contract analysis
"Claude retrieves the Nike contract PDF and extracts the performance obligations:
minimum $50M revenue, 12% margin requirement, quarterly reporting deadline."

Step 3 — Data query
"Claude formulates a query and sends it to the integration layer: 'Get Q4 2025 revenue
and gross margin for Nike brand from Snowflake'."

Step 4 — Results and synthesis
"Snowflake returns the data. Claude compares actuals vs. obligations:
Revenue $52.3M ✓ (exceeded by $2.3M) / Margin 11.2% ⚠ (0.8% below threshold)."

Step 5 — Insight delivery
"Claude synthesizes an executive summary with recommendations: 'Review promotional
spend allocation to improve margin performance'."
```
