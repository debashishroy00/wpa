# WealthPath AI - Prompt Engineering Guide

This document contains all the prompts used in the WealthPath AI system for optimization and analysis.

## System Overview

The system uses a multi-stage Agentic RAG (Retrieval-Augmented Generation) approach with mode-specific prompt engineering:

1. **Query Planning Stage**: Decomposes complex queries into sub-questions
2. **Response Generation Stage**: Generates responses with different depth levels based on mode
3. **Three Response Modes**: Direct, Balanced, Comprehensive

---

## 1. Query Planning Prompt (OPTIMIZED)

**Purpose**: Breaks down complex financial queries into domain-specific sub-questions with categorization for better retrieval.

**System Prompt**:
```
You are a financial query planner. Return only valid JSON.
```

**User Prompt Template**:
```
You are a financial query planner. Your job is to decompose user queries 
into 2–3 precise financial sub-questions.

Query: {message}
User context: Age {age}, State: {state}
Intent type: {intent}

Categorize each sub-question as:
- FACT: requires numeric/user data (assets, income, liabilities, etc.)
- RULE: requires authority context (IRS, state tax code, retirement rules)
- PATTERN: requires historical or behavioral context

Return a JSON array of steps:
[
    {"step": 1, "type": "FACT", "question": "...", "search_query": "...", "index": "user_facts"},
    {"step": 2, "type": "RULE", "question": "...", "search_query": "...", "index": "authority"},
    {"step": 3, "type": "PATTERN", "question": "...", "search_query": "...", "index": "user_history"}
]

Keep it simple - max 3 steps.
```

**Optimizations**:
- ✅ Domain-specific financial categorization (FACT/RULE/PATTERN)
- ✅ Index routing based on query type
- ✅ Financial domain expertise in system prompt

---

## 2. Response Generation Prompts by Mode

### 🟢 Direct Mode (Temperature: 0.1) - FINAL

**System Prompt**:
```
You are a precise financial data assistant. Provide one-sentence factual answers 
grounded only in the provided numbers. No analysis, no advice.
```

**User Prompt Template**:
```
Question: {message}
Facts: {facts_json}

Answer with:
1. A single sentence summary.
2. Supporting numbers only if directly relevant.

{if_gaps_exist: "Note: Answer limited due to {gap_descriptions}"}
```

**Example Output**:
```
"Your current net worth is $2,565,545, calculated as total assets of $2,879,827 minus liabilities of $314,282."
```

**Characteristics**:
- ✅ Single-sentence focus eliminates verbosity
- ✅ Supporting numbers only when directly relevant
- ✅ Zero analysis or recommendations

### Balanced Mode (Temperature: 0.3) - OPTIMIZED

**System Prompt**:
```
You are a practical financial advisor. Provide accurate information 
enhanced with relevant insights and actionable recommendations.
Do not speculate beyond provided data and evidence.
```

**User Prompt Template**:
```
Question: {message}

Financial Facts:
{facts_json}

Context:
{evidence_top_3_pieces}

Provide concise analysis that:
- States the direct answer
- Explains the key calculation or rule
- Highlights 1–2 practical recommendations
Do not speculate beyond provided data and evidence.

{if_gaps_exist: "Note: Answer limited because {gap_descriptions}"}
```

**Characteristics**:
- ✅ Anti-speculation guardrail in system prompt
- ✅ Structured 3-part analysis (answer → rule → recommendations)
- ✅ Limited to top 3 evidence pieces
- ✅ Explicit gap acknowledgement

### Comprehensive Mode (Temperature: 0.5) - OPTIMIZED

**System Prompt**:
```
You are an expert financial strategist with deep knowledge in wealth 
management, tax optimization, behavioral finance, and life planning. Provide sophisticated 
analysis that goes beyond the obvious, identifying patterns and opportunities.
```

**User Prompt Template**:
```
Question: {message}

Complete Financial Picture:
{facts_json}

Historical Patterns:
{evidence_full}

Behavioral Context:
{gap_analysis_and_iterations}

Provide deep analysis in four clearly labeled sections:

## 1. Current Position
Facts restated with calculations and context

## 2. Patterns & Risks  
Non-obvious trends, ratios, mismatches, and potential vulnerabilities

## 3. Strategies
Advanced tax, portfolio, estate planning opportunities

## 4. Behavioral Factors
Risk tolerance, decision biases, long-term habits, and psychological considerations

Each section must be clearly labeled. Be bold with insights while explaining your reasoning clearly.
```

**Characteristics**:
- ✅ Structured 4-part analysis prevents meandering
- ✅ Full context and evidence exposure
- ✅ Behavioral finance integration with dedicated section
- ✅ Clear section labeling for readability

---

## 3. Current System Context

### Available Data Context:
```json
{
  "net_worth": "$2,565,545",
  "monthly_surplus": "$7,863", 
  "age": "unknown",
  "assets": "$2,879,827",
  "liabilities": "$314,282",
  "investment_total": "$871,000",
  "retirement_total": "$310,216",
  "FI_number": "$2,244,300",
  "FI_progress": "1.14",
  "debt_to_asset_ratio": "10.91%",
  "savings_rate": "51.24%"
}
```

### Gap Handling:
```
Note: Some information gaps were identified:
{gap_descriptions}
Acknowledge these limitations in your response.
```

---

## 4. Optimization Status

### ✅ COMPLETED OPTIMIZATIONS:

1. **Financial Domain-Specific Planning**
   - ✅ FACT/RULE/PATTERN categorization implemented
   - ✅ Index routing based on query type
   - ✅ Financial query planner persona

2. **Enhanced Mode Differentiation**
   - ✅ Anti-hallucination guardrails in Direct mode
   - ✅ Structured 3-part analysis in Balanced mode
   - ✅ 4-section structure in Comprehensive mode
   - ✅ Progressive context control (facts → top-3 → full)

3. **Advanced Context Management**
   - ✅ Explicit gap acknowledgement in all modes
   - ✅ Evidence limiting by mode (none → 3 → all)
   - ✅ "Not available" handling for missing data

4. **Specialized Personas**
   - ✅ Financial data assistant (Direct)
   - ✅ Practical financial advisor (Balanced)
   - ✅ Expert financial strategist (Comprehensive)

### 🔄 FUTURE OPTIMIZATIONS:

1. **Chain-of-Thought Integration**
2. **Dynamic Temperature Adjustment**
3. **Query Pattern Recognition**
4. **Behavioral Finance Sub-prompts**
5. **Risk Assessment Templates**

---

## 5. Test Cases for Optimization

**Query**: "What is my net worth?"

**Expected Outputs**:
- **Direct**: "$2,565,545"
- **Balanced**: "Your net worth is $2,565,545, calculated as assets ($2,879,827) minus liabilities ($314,282). This represents strong financial health with low debt ratio."
- **Comprehensive**: "Your $2.5M net worth reveals strategic wealth positioning. Analysis of your 10.91% debt-to-asset ratio combined with 51.24% savings rate suggests advanced financial discipline patterns..."

**Current Performance**: ✅ Working as intended after fixes

---

## 6. Prompt Variables Reference

| Variable | Source | Type | Example |
|----------|---------|------|---------|
| `{message}` | User input | string | "What is my net worth?" |
| `{facts}` | User profile + financial data | dict | See context above |
| `{evidence}` | Vector search results | list | Search results from knowledge base |
| `{gaps}` | Information gap analysis | list | Missing data points |
| `{mode}` | Frontend selection | enum | "direct", "balanced", "comprehensive" |
| `{temperature}` | Mode-dependent | float | 0.1, 0.3, 0.5 |

---

## Usage Notes

- All prompts use f-string formatting with variables in curly braces
- JSON context is serialized with `json.dumps(facts, indent=2)`
- Evidence is formatted with custom `_format_evidence()` function
- Temperature values are mode-specific and fixed
- System maintains conversation context across multiple queries

This prompt architecture enables sophisticated financial advisory responses while maintaining clear differentiation between response modes based on user preference.