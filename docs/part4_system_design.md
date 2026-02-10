# Part 4: Mini System Design - Sales Insight & Alert System

## Overview

A lightweight, production-ready system that monitors sales performance and delivers actionable insights to revenue leaders.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SALES INSIGHT & ALERT SYSTEM                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐   │
│  │   DATA       │    │   ANALYSIS   │    │      DELIVERY            │   │
│  │   LAYER      │───▶│   ENGINE     │───▶│      LAYER               │   │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘   │
│         │                   │                        │                   │
│         ▼                   ▼                        ▼                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐   │
│  │ • CRM Sync   │    │ • Win Rate   │    │ • Email Alerts           │   │
│  │ • CSV Import │    │   Trends     │    │ • Dashboard API          │   │
│  │ • Data       │    │ • Driver     │    │ • Slack/Teams            │   │
│  │   Validation │    │   Analysis   │    │ • Weekly Reports         │   │
│  └──────────────┘    │ • Risk       │    └──────────────────────────┘   │
│                      │   Scoring    │                                    │
│                      │ • Anomaly    │                                    │
│                      │   Detection  │                                    │
│                      └──────────────┘                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Data Ingestion (Daily at 2 AM)
```
CRM (Salesforce/HubSpot) ──API──▶ ETL Pipeline ──▶ Data Warehouse
                                      │
                                      ▼
                              Data Validation
                              • Missing fields check
                              • Date sanity check
                              • Duplicate detection
```

### 2. Analysis Pipeline (Daily at 3 AM)
```
Data Warehouse ──▶ Metric Computation ──▶ Insight Generation ──▶ Alert Queue
                         │                       │
                         ▼                       ▼
                  • Win rate by segment   • Anomaly flags
                  • Stage conversions     • Trend changes
                  • Rep performance       • Risk scores
```

### 3. Delivery (On-demand + Scheduled)
```
Alert Queue ──▶ Priority Filter ──▶ Routing Engine ──▶ Notification Channel
                     │                    │
                     ▼                    ▼
              • P1: Immediate      • Slack: Real-time
              • P2: Daily digest   • Email: Summaries
              • P3: Weekly report  • Dashboard: Self-serve
```

---

## Example Alerts

### 🔴 Critical (Immediate)
```
ALERT: Win Rate Drop Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Segment: Enterprise + North America
Current Win Rate: 28% (down from 42%)
Time Period: Last 14 days
Affected Pipeline: $2.4M across 12 deals

Recommended Action:
→ Review lost deal reasons with NA Enterprise team
→ Schedule pipeline review with rep_22, rep_14
```

### 🟡 Warning (Daily Digest)
```
ALERT: Rep Performance Shift
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rep: rep_05
Momentum Index: 0.65 (declining)
Recent Win Rate: 22% vs Historical: 34%

Suggested Action:
→ 1:1 coaching session recommended
→ Review recent lost deals for patterns
```

### 🟢 Insight (Weekly Report)
```
INSIGHT: High-Performing Segment Identified
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Segment: FinTech + Referral Leads
Win Rate: 58% (vs. company avg 47%)
Deal Velocity: 1.5x faster than average

Opportunity:
→ Increase marketing spend on FinTech referral programs
→ Document and share winning playbook with team
```

---

## Operational Cadence

| Process | Frequency | Duration | Owner |
|---------|-----------|----------|-------|
| Data Sync | Daily 2 AM | ~15 min | Automated |
| Metric Computation | Daily 3 AM | ~30 min | Automated |
| Anomaly Detection | Daily 4 AM | ~10 min | Automated |
| Alert Dispatch | Real-time | Instant | Automated |
| Weekly Summary | Monday 8 AM | ~5 min | Automated |
| Model Retrain | Monthly | ~2 hours | Applied AI / Data Science Engineer |

---

## User Feedback Loop

Insights are only valuable if they drive action. To close the loop:

1. **Relevance feedback** — CROs can mark alerts as *useful* or *not relevant*
2. **Threshold tuning** — Feedback is logged to refine alert sensitivity and thresholds over time
3. **Auto-suppression** — Repeatedly ignored alerts are automatically deprioritized
4. **Impact tracking** — When a CRO acts on an alert, downstream win-rate changes are tracked to validate signal quality

> Without this loop, the system eventually succumbs to alert fatigue and becomes shelfware.

---

## Technical Components

### Tech Stack
- **Data Pipeline**: Apache Airflow / Dagster
- **Storage**: PostgreSQL + Redis (cache)
- **Analysis**: Python (pandas, scikit-learn)
- **API**: FastAPI
- **Notifications**: SendGrid + Slack API
- **Monitoring**: Datadog / Prometheus

> *Specific tools are illustrative; equivalent technologies may be used depending on existing infrastructure.*

### Key Tables
```sql
-- Core fact table
deals (deal_id, created_date, closed_date, outcome, amount, ...)

-- Computed metrics
daily_metrics (date, segment, win_rate, deal_count, avg_cycle)

-- Alert history
alerts (alert_id, type, severity, segment, message, sent_at)
```

---

## Failure Cases & Limitations

### Known Limitations
1. **Lag Time**: 24-hour delay in insights (batch processing)
2. **Attribution**: Can't determine causation, only correlation
3. **Context Blindness**: No qualitative data (call notes, competitor info)
4. **Small Sample Issues**: Alerts may fire on statistically insignificant changes

### Failure Modes
| Failure | Impact | Mitigation |
|---------|--------|------------|
| CRM API down | No fresh data | Cache last known state, alert ops team |
| Anomaly false positive | Alert fatigue | Confidence thresholds, user feedback loop |
| Model drift | Poor predictions | Monthly retraining, monitoring metrics |
| Data quality issues | Bad insights | Validation layer, data quality dashboards |

### Graceful Degradation
- If analysis fails → Serve cached insights with "stale data" warning
- If alerts can't send → Queue for retry, escalate after 3 failures
- If model unavailable → Fall back to rule-based heuristics

---

## Future Enhancements (If Productized)

1. **Real-time Processing**: Stream from CRM webhooks
2. **Natural Language Insights**: LLM-generated explanations
3. **Predictive Alerts**: "Win rate likely to drop next week"
4. **Self-Service Analytics**: Let users ask questions in plain English
5. **A/B Testing Framework**: Measure impact of interventions
