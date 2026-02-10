# Part 1: Problem Framing

## 1. What is the Real Business Problem?

The CRO's concern reveals a **diagnostic gap** in their sales intelligence:
- **Symptom**: Win rate has declined over two quarters
- **Paradox**: Pipeline volume remains healthy
- **Core Problem**: Leadership lacks visibility into **why** deals are being lost

This isn't just a "win rate" problem—it's a **decision intelligence problem**. The CRO needs:
1. Root cause identification (what changed?)
2. Segment-level diagnosis (where is the problem concentrated?)
3. Actionable levers (what can we control?)

> **Expanding pipeline volume is often the wrong response to declining win rate, as it masks execution problems instead of addressing them.** The instinct to "add more top-of-funnel" treats the symptom while the disease compounds.

---

## 2. Key Questions an AI System Should Answer

### Diagnostic Questions
1. **Where is the win rate dropping?** (Region, Industry, Product, Rep)
2. **When did the decline start?** (Trend analysis)
3. **Which deal stages have increased drop-off?** (Funnel analysis)
4. **Are specific reps/teams underperforming?** (Performance attribution)

### Predictive Questions
5. **Which current deals are at risk?** (Risk scoring)
6. **What's the expected revenue this quarter?** (Forecasting)

### Prescriptive Questions
7. **What actions could improve outcomes?** (Recommendations)
8. **Where should coaching/resources be focused?** (Prioritization)

---

## 3. Critical Metrics for Diagnosing Win Rate Issues

### Primary Metrics
| Metric | Definition | Why It Matters |
|--------|------------|----------------|
| **Win Rate** | Won Deals / Total Closed Deals | Core KPI being investigated |
| **Win Rate by Segment** | Win rate per region/industry/product | Identifies problem areas |
| **Stage Conversion Rate** | % moving from stage N to N+1 | Pinpoints funnel leaks |

### Secondary Metrics
| Metric | Definition | Why It Matters |
|--------|------------|----------------|
| **Sales Cycle Length** | Days from created to closed | Longer cycles → higher risk |
| **Average Deal Size** | Mean deal_amount | Revenue quality indicator |
| **Rep Performance Index** | Win rate vs. team average | Identifies training needs |

### Custom Metrics (Invented)
| Metric | Definition | Why It Matters |
|--------|------------|----------------|
| **Deal Velocity Score** | Deal Amount ÷ Sales Cycle Days | Measures deal quality/efficiency |
| **Rep Momentum Index** | (Recent 30-day Win Rate) ÷ (90-day Win Rate) | Detects improving/declining reps |

---

## 4. Assumptions About Data & Business

### Data Assumptions
1. **Data Completeness**: All closed deals have an outcome (won/lost)
2. **Date Accuracy**: created_date and closed_date are reliable
3. **No Survivorship Bias**: Pipeline includes both won and lost deals
4. **Consistent Definitions**: Deal stages are uniformly applied across reps

### Business Assumptions
1. **External Factors**: No major market disruption (recession, competitor entry)
2. **Team Stability**: No major sales team changes (new hires, departures)
3. **Product Stability**: No significant product/pricing changes
4. **Seasonality**: Q1/Q2 patterns are comparable to prior years
5. **Lead Quality**: Marketing lead sources remained consistent

### Data Signals Treated with Caution

| Signal | Why We Distrust It |
|--------|--------------------|
| **Closed-lost reasons** | Reps self-report; high reporting bias and inconsistency |
| **Deal stages** | May be applied inconsistently across reps and teams |
| **Sales cycle days** | Dependent on accurate `created_date`, which may be backdated |

These signals are still used — but insights derived from them are flagged as directional, not definitive.

### Limitations
- No CRM activity data (emails, calls, meetings)
- No competitor information on lost deals
- No customer sentiment or NPS data
- No quota/target context for reps
