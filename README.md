# Warehouse Closure Analysis: A SQL-Based Multi-Criteria Decision Framework

A SQL case study using the Mint Classic sample database (MySQL Workbench) to determine which warehouse — if any — should be closed, using a two-level weighted scoring model built entirely from queryable data.

---

## Executive Summary

This project evaluates whether consolidating Mint Classic's four warehouses (North, South, East, West) is a financially and operationally sound decision, and if so, deciding which warehouse is the best candidate for closure. Rather than relying on a single metric (e.g., "close whichever warehouse has the lowest sales"), this analysis builds a **19-question, 5-level investigative framework** — moving from descriptive state assessment through product, customer, and feasibility analysis to a final recommendation — and operationalizes each question's output into a **normalized, weighted score** so that warehouses can more objectively be compared on a single, defensible scale rather than subjective warehouse-by-warehouse judgment.

All analysis is performed in SQL against the Mint Classic schema (`warehouses`, `products`, `orders`, `orderdetails`, `customers`) using MySQL Workbench. Results, final recommendation, and risk discussion are documented separately (see [Results](#results) and [Conclusion & Recommendations](#conclusion--recommendations) below).

---

## Business Problem

Mint Classic operates four warehouses with uneven utilization (ranging 50–75% of capacity in the current dataset). Maintaining underused warehouse space carries ongoing fixed costs — lease, staffing, utilities — without a proportional return in sales throughput. The business question is:

> **Can Mint Classic help deciding on closing one warehouse without materially harming sales, customer service levels, or high-value/high-margin product availability — and if so, which one?**

This is not a question a single query can answer safely. A warehouse might look like a weak performer on raw sales volume but turn out to hold the company's highest-margin products, serve a geographically isolated customer base, or already run close to capacity — any of which would make closing it a costly financial mistake. The goal of this project is to systematically rule those risks in or out with data, rather than closing a warehouse based on the most visible metric alone.

---

## Method

The analysis was split into five levels: current state of warehouses, product analysis, customer impact analysis, consolidation feasibility and final recommendation. Prior to the analyses, Preliminary Data Exploration & Validation was performed as Level 0 to audit data quality and integrity.

### 1. Five-Level Investigative Framework

The analysis is organized into 19 questions across four levels, moving from "what do we have" to "what should we do":

| Level | Focus | Example questions |
|---|---|---|
| **1 — Current State Assessment** | Baseline utilization, inventory value, sales performance per warehouse | Utilization rates, inventory value, sales-vs-capacity correlation |
| **2 — Product Analysis** | What's actually moving through each warehouse | Best/worst sellers, dead stock, turnover rate, profit margin |
| **3 — Customer Impact Analysis** | Who gets hurt if a warehouse closes | Affected customers, unique regions served, fulfillment time, order problem rates |
| **4 — Consolidation Feasibility** | Can the closure physically and financially happen | Composite ranking, absorption capacity, relocation volume, post-closure capacity |
| **5 — Recommendation** | Synthesis | Final closure candidate, implementation plan, risks |

Each question specifies the exact tables/columns needed, the SQL technique used to answer it (e.g., CTEs, window functions), and a validation note where the raw data requires a sanity check before trusting the output (e.g., anchoring "last 12 months" to `MAX(orderDate)` rather than the current date, since the dataset is historical).

### 2. Two-Level Weighted Scoring Strategy

Because the 19 questions return results in incompatible units (dollars, percentages, counts, days), each question's result is converted into a **comparable, directionally-consistent score** before it can be combined into a single ranking. This happens in two stages: normalize and weight **within** each level, then weight **across** levels.

**Step 1 — Normalize each question's result (0 to 1) across warehouses:**

$$N_q(w) = \frac{V_q(w) - \min(V_q)}{\max(V_q) - \min(V_q)}$$

Where $V_q(w)$ is warehouse $w$'s raw result for question $q$, and the min/max are taken across all warehouses being compared. This is computed in SQL using window functions (`MIN(...) OVER ()`, `MAX(...) OVER ()`), guarded with `NULLIF()` to avoid divide-by-zero when all warehouses tie.

**Step 2 — Apply direction correction.** The composite score is defined as a **Closure Suitability Score** — higher means more suitable to close. Some raw metrics point the right way already (e.g., higher dead-stock % → more suitable to close); others need inverting:

$$
N_q'(w) = \begin{cases} 
N_q(w) & \text{high raw value} \Rightarrow \text{more suitable to close} \\ 
1 - N_q(w) & \text{high raw value} \Rightarrow \text{less suitable to close} 
\end{cases}
$$


*Example:* utilization rate (`warehousePctCap`) is inverted — a warehouse running at low capacity is a *better* closure candidate, so its normalized score is flipped before entering the composite.

**Step 3 — Weight questions within a level:**

$$S_L(w) = \sum_{q \in L} \omega_q \cdot N_q'(w), \text{where} \qquad \sum_{q \in L} \omega_q = 1$$

Each level's questions are weighted by how decision-relevant they are within that level (e.g., within Level 2, turnover rate and margin are weighted more heavily than raw product count).  

This analysis utilizes a modular pipeline approach using Common Table Expressions (CTEs) to isolate the calculation of raw metrics for each question. These raw values are then normalized and weighted together at the end of each MySQL script, keeping the codebase easy to maintain and fine-tune.

**Step 4 — Weight across levels into one composite score:**

$$C(w) = \sum_{L=1}^{4} \Omega_L \cdot S_L(w),  \text{where} \qquad \sum_{L} \Omega_L = 1$$

| Level | Weight $\Omega_L$ | Rationale |
|---|---|---|
| 1 — Current State | 0.15 | Descriptive context; low decision weight alone |
| 2 — Product Analysis | 0.35 | Core driver of the decision — what's actually moving |
| 3 — Customer Impact | 0.30 | Risk of harming service carries real weight |
| 4 — Consolidation Feasibility | 0.20 | Gates the decision more than it ranks it |

Warehouses are ranked by $C(w)$; the highest score is the primary closure candidate.

**Step 5 — Apply gates and overrides.** Three checks are not folded into the weighted score, because they aren't comparable per-warehouse metrics — they're pass/fail conditions applied *after* ranking:

- **Unique-region flag** — if the top-ranked candidate uniquely serves a geographic region, this is surfaced as an explicit risk rather than averaged away in a weighted sum.
- **Absorption capacity check** — a property of the *remaining* warehouses, not the candidate itself; confirms the closure is physically executable.
- **Cost savings** — no operating-cost data exists in the schema, so this stays a narrative discussion rather than a scored input.

### 3. Validation Approach

Throughout the SQL, results are checked against known data-quality risks before being trusted:
- Date-relative questions ("last 12 months," "last 6 months") are anchored to `MAX(orderDate)` in the dataset, not the current system date, since Mint Classic's data is historical.
- Aggregations that divide by a count or stock quantity are wrapped in `NULLIF()` to avoid divide-by-zero errors.
- Placeholder/NULL rows (e.g., the empty insert row MySQL Workbench displays in the `warehouses` table) are explicitly filtered out before aggregation.
- Any single-warehouse-region findings (Q10) are spot-checked against raw order counts to rule out low-sample-size artifacts before being flagged as real geographic risk.

### 4. Sensitivity Analysis

Because the level weights $\Omega_L$ in Step 4 are analyst-assigned rather than derived from the data, the final recommendation is only as trustworthy as those weights are defensible. To test this, the composite score $C(w)$ is recomputed under several alternative weighting scenarios, and the resulting warehouse rankings are compared to the baseline scenario. If the top closure candidate stays the same across most or all scenarios, that is strong evidence the recommendation is robust rather than an artifact of one particular weight choice; if it flips easily, that is itself an important finding and tempers how confidently the recommendation can be stated.

**Candidate weighting scenarios** (Level 1 / Level 2 / Level 3 / Level 4):

| Scenario | Weights | Rationale |
|---|---|---|
| Baseline | 0.15 / 0.35 / 0.30 / 0.20 | Product-and-customer-weighted, as defined in Step 4 |
| Equal weighting | 0.25 / 0.25 / 0.25 / 0.25 | No level assumed more important than another — a neutral control case |
| Product-prioritized | 0.10 / 0.50 / 0.25 / 0.15 | Treats what's actually moving through the warehouse as the dominant signal |
| Customer-risk-averse | 0.10 / 0.25 / 0.50 / 0.15 | Weights service disruption most heavily, for a risk-conservative decision-maker |
| Feasibility-constrained | 0.10 / 0.25 / 0.25 / 0.40 | Prioritizes whether the closure is physically/operationally executable at all |

**How stability is assessed:**
- **Rank stability** — does the #1-ranked (most closure-suitable) warehouse change across scenarios? This is the headline check.
- **Score margin** — even when the top candidate doesn't change, how close is the runner-up? A narrow margin under the baseline that widens or narrows under alternative scenarios indicates how much of the decision is being driven by the weighting choice itself versus the underlying data.
- **Rank correlation** — Spearman's rank correlation between the baseline ranking and each alternative scenario's ranking, to quantify overall agreement rather than relying on the top rank alone.

---

## Repository Structure

```
├── README.md
├── LICENSE
├── sql/
│   └── 1_warehouse_performance_assessment.sql
    └── 2_product_analysis.sql
    └── 3_customer_impact_analysis.sql
    └── 4_consolidation_feasibility.sql
    └── 5_final_recommendation.sql
├── docs/
│   └── analysis_questions.md
│   └── results.md
└── results/
    └── (to be added)
```

---

## Results  
    
### Level 1: Current State Assessment of The Warehouses   
**Warehouse utilization rate:**  
There are 4 warehouses, other three of them use 67% to 75% of store capacity, the warehouse West uses only 
 50% of the storage capacity. The West branch have the greatest amount of unused capacity.


**Inventory Value (Potential Financial Impact of Relocation):**   
- Total inventory value is the lowest in the South branch ($4.1M). Warehouse West is the second lowest.
- The East branch holds the greatest financial value ($14.1M). It would cost the most logistical and financial impact if closed.
- The lowest relocation cost would occur if South ($4.1M) or West($5.7) was relocated.


**Warehouse Product Diversity:**  
- Warehouses South (23), West (24) and North (25)   almost have the same number of distinct products.
- They have considerably lower distinct products than the East branch (38).

**Warehouse Sales Performance (the last year):**  
- Available dates are from 2005-05-31 to 2003-01-06.
- East is the undisputed sales leader, the revenue engine – It dominates across every single metric: the highest order volume (101), the highest total unit sales (16,595), and the broadest product assortment sold (37 unique products).
- North and South form a competitive middle tier – North generates the second-highest revenue and unit sales, while South has slightly more orders (71 vs. 60) and trails closely in average order value ($2,893 vs. $2,977). Both are stable performers but not exceptional.
- West has the weakest fundamentals. Despite having the second-highest number of orders (90), it generates the lowest total revenue and the lowest average order value ($2,751). This indicates a high volume of small, low-value transactions, which is a classic sign of low-margin.

**Capacity Utilization and Sales Ranks:**  




## Conclusion & Recommendations
*(to be added)*
