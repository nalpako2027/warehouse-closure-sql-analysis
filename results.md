# RESULTS FOR THE MULTILEVEL ANALYSIS QUESTIONS  

## LEVEL 1: CURRENT STATE OF THE WAREHOUSES  
**Q1- What are the current warehouses and their utilization rates?**  
*Result:*  
- There are 4 warehouses, other three of them use 67% to 75% of store capacity, the warehouse West uses only 
- 50% of the storage capacity. The West branch have the greatest amount of unused capacity.
- The last row has NULL values; however, In MySQL Workbench, it is a placeholder for inserting new records.


**Q2- What is the total inventory value stored in each warehouse (for potential financial impact)? 
How much inventory value would potentially need to be relocated if each warehouse were closed?**  
*Result:*  
- Total inventory value is the lowest in the South branch. Warehouse West is the second lowest.
- The East branch holds the greatest financial value ($14.1M). It would cost the most logistical and financial impact if closed.
- The lowest relocation cost would occur if South ($4.1M) or West($5.7) was relocated.


**Q3- What is the total number of distinct products stored in each warehouse?**  
*Result:*  
- Warehouses South (23), West (24) and North (25)   almost have the same number of distinct products.
- They have considerably lower distinct products than the East branch (38).



**Q4- How has each warehouse performed in terms of sales over the last year?**  
*Result:*  
- East is the undisputed sales leader, the revenue engine – It dominates across every single metric: the highest order volume (101), the highest total unit sales (16,595), and the broadest product assortment sold (37 unique products).
- North and South form a competitive middle tier – North generates the second-highest revenue and unit sales, while South has slightly more orders (71 vs. 60) and trails closely in average order value ($2,893 vs. $2,977). Both are stable performers but not exceptional.
-- West has the weakest fundamentals. Despite having the second-highest number of orders (90), it generates the lowest total revenue and the lowest average order value ($2,751). This indicates a high volume of small, low-value transactions, which is a classic sign of low-margin.



**Q5- Is warehouse capacity utilization actually has a relationship with sales performance?**  
*Result:*  
- West: ranked last on both capacity rank and sales rank. This is the least utilized and the weakest performer.
- South: The most utilized warehouse, ranked 1st in capacity rank (75%) but only 3rd in sales. Additionally, it has the lowest sales_per_pct_capacity (25,021.93). So there is an efficiency issue here.
- East: It leads sales by a wide margin ($3.85M vs the next highest North $2.08M). Its sales_per_pct_capacity is the highest. East is the strongest warehouse.
- North: For this warehouse, its capacity and sales rank agree; both are second. Its statistics does not suggest for or against argument for its closure.



**Q6- What is the year-over-year change for each warehouse? Are sales of the warehouses improve/decline?**
*Result:*   
- The East branch has the lowest growth percentage (16.65%), while the West branch has the highest (31.70%). However, the East branch has the highest year-over-year increase in total sales, with sales increasing by approximately $257K. This difference is largely related to the East branch's much larger sales base. Its recent-year sales are approximately $1.54M, substantially higher than the other branches.
- The West branch shows the strongest relative growth, increasing its sales by 31.70%, despite having one of the lowest total sales volumes.
- The North branch's 34.84% growth rate is relatively strong, but its sales growth appears more modest when considered alongside its overall sales volume.
- Overall, all four branches experienced positive year-over-year sales growth, so none currently shows an absolute decline in sales.
- The East branch's combination of high sales volume and comparatively lower growth suggests a more mature sales base, whereas the West branch shows stronger relative expansion from a smaller base.



### Column Selection and Justification for Level 1 Composite Score

Before scoring, the columns relevant to each question were identified, along with the justification for their inclusion or exclusion.

| Question | Column(s) Selected | Column(s) Excluded | Justification |
|---|---|---|---|
| Q1 | `warehousePctCap` | — | Serves as the direct indicator of warehouse utilization. |
| Q2 | `total_inventory_value` | — | Serves a dual purpose, also functioning as the relocation-cost proxy. |
| Q3 | `distinct_products` | — | Measures the operational complexity associated with closing the location. |
| Q4 | `total_sales_value`, `avg_order_value` | `total_orders`, `unique_products_sold` | `total_sales_value` serves as the core performance indicator; `total_orders` is excluded as it can be misleading (e.g., inflated by a high volume of low-value orders). `avg_order_value` captures customer quality independently of purchase volume. `unique_products_sold` is excluded to mitigate double counting, as this dimension is already captured in Q3 (`distinct_products`). |
| Q5 | `sales_per_pct_capacity` | `capacity_rank`, `sales_rank` | `sales_per_pct_capacity` serves as the indicator of warehouse efficiency; the rank columns are diagnostic in nature and are therefore not included as scoring inputs. |
| Q6 | `growth_percentage` | `total_sales_increase` | As a size-independent measure, growth rate provides a more equitable basis for cross-warehouse comparison. |


**Composite scores:**  
Weights for [warehousePctCap, total_inventory_value, distinct_products, total_sales_value, avg_order_value, sales_per_pct_capacity, growth_percentage]:
- Baseline weights [0.10, 0.20, 0.10, 0.25, 0.10, 0.15, 0.10]       :  South -> 0.816; West -> 0.811; North -> 0.676; East -> 0.132

*Sensitivity Analysis (Stress Test):*
- For equal weights [0.143, 0.143, 0.143, 0.143, 0.143, 0.143, 0.143]:  West -> 0.777; South -> 0.744; North -> 0.621; East -> 0.189
- Efficiency/Inventory size[0.10, 0.15, 0.05, 0.15, 0.10, 0.30, 0.15]:  South -> 0.787; West -> 0.722; North -> 0.651; East -> 0.182



===============================================================
### Conclusion for Level 1: Current State of Warehouses 
===============================================================

- Across three weighting scenarios, East is consistently the strongest performer (lowest closure suitability, 0.13–0.19) and North sits comfortably in the middle (0.62–0.68), so neither is a viable closure candidate under any weighting scenario tested.
- South and West trade the top spot depending on the weighting scheme — South leads under baseline and efficiency-focused weights (0.82 and 0.79) by leaning on its low relocation cost and poor capacity efficiency, while West leads under equal weighting (0.78) on the strength of its low utilization and weak raw sales — indicating the final recommendation between these two should rely on Level 2–4 evidence (product margin, customer impact, consolidation feasibility) rather than Level 1 alone.

===============================================================
## LEVEL 2: PRODUCT ANALYSIS  
===============================================================


**Q1- Which are the top 10% best-selling products by sales volume and value?**

- East (b) dominates with 6 of 7 top-selling products — highest concentration of best-sellers
- In top 10% total sale volume of products (of the total 110 distinct products), East holds 6, North holds 3, and West holds 2 products. Including top 10% total units sale into consideration, of the 21 products, East holds 8, North holds 5, West and South holds 4 products each.
- 1992 Ferrari 360 Spider red (#1) generates $271K in sales — nearly more than half of 2001 Ferrari Enzo (#2)
- Top 3 products (all in East) account for $643K combined. East warehouse best-sellers generate $1.35M total. It is the best performer.




**Q2- Which are the bottom 20% slowest-moving products (by sales volume)?**

- East (b) holds 9 of 22 slowest-moving products — highest concentration of slow stock
- West (c) holds 7 of 22 — significant concentration
- North (a) holds 3 of 22 — minimal
- South (d) holds 3 of 22 — minimal
- 1985 Toyota Supra has 0 units sold — complete dead stock. Located in East warehouse, it should be liquidated.
- Overall, East dominates slowest-moving products but it also had the highest concentration of best selling product.
- West had one of the lowest representation in high best-selling products in volume and sales value and it holds a significant amount of low-selling products.




**Q3- How many products are "dead stock" (zero or near-zero sales) in the last 6 months?**  
- Similar to the previous result, the 1985 Toyota Supra unit sold 0 within the last six-month. It is the only dead stock.
- Located in East warehouse, it should be liquidated immediately.



**Q4- What is the sales turnover rate (sales velocity) for products in each warehouse?**
- All warehouses have very low turnover rates.
- Turnover rate is the highest in South (0.282), relatively more efficient one; and it is lower in North (0.187), West (0.184) and East(0.162) branches.
- The time range is 2.5 years for Mint Classic data. For these turnover rates, it will approximately take 9 years for South branch, 13 years for North, 14 years for West and 15 years for East branch to sell all of their stocks.


**Q5- What is the profit margin per product by warehouse?**
- For reference: Minimum price is $26.55 and maximum is $214.3 and minimum MSRP is $33.19 and maximum MSRP is $214.30
- Total realized margin is highest for 1992 Ferrari 360 Spider. Similarly, 1952 Alpine Renault and 2001 Ferrari Enzo are other products with higher profit margin.
- Average profit margin per unit is $42.66 for East, the highest. Other warehouses have similar averages: $33.66 for North, $32.35 for West, $32.59 for South 


### Column Selection and Justification for Level 2 Composite Score

| Question | Column(s) Selected | Column(s) Excluded | Justification |
|---|---|---|---|
| Q1 | `critical_product_count` | — | Counts how many of the warehouse's products fall within the company's top decile by sales value; captures the risk of losing access to top sellers. |
| Q2 | `slow_mover_count` | — | Counts products in the bottom quintile by sales volume, housed in the warehouse; a higher count indicates a warehouse dominated by slow-moving inventory. |
| Q3 | `dead_stock_pct` \*| — | Expressed as a percentage of the warehouse's own catalog, rather than a raw count, so that a warehouse with fewer total products is not unfairly flagged for having a smaller dead-stock count in absolute terms. |
| Q4 | `turnover_rate` | — | A direct ratio of sales velocity to stock on hand, unaffected by warehouse size, serving as the cleanest efficiency signal at this level. |
| Q5 | `total_realized_margin`, `avg_realized_margin_per_unit` | `list_margin_per_unit` | `total_realized_margin` captures actual dollar profitability generated by the warehouse's products. `avg_realized_margin_per_unit` captures margin quality independently of sales volume. `list_margin_per_unit` (based on MSRP) is excluded, as it reflects theoretical rather than realized profitability. |
\* The East branch had a single dead stock, others don't have any. The number of the units in that dead stock is not extreme. For fair comparison, this was taken into account in weighting scenarios.


**Composite Scores:**  
Weights for [critical_product_count, slow_mover_count, dead_stock_pct, turnover_rate, total_realized_margin, avg_realized_margin_per_unit]:
  
- Baseline weights [0.25, 0.15, 0.05, 0.25, 0.20, 0.10]       :  West -> 0.815; North -> 0.603; South -> 0.548;  East-> 0.450   
*Sensitivity Analysis (Stress Test):*  
- For equal weights [0.167, 0.167, 0.167, 0.167, 0.167, 0.167]:  West -> 0.722; North -> 0.519; East -> 0.501; South -> 0.497
- Margin Focused [0.15, 0.10, 0.05, 0.15, 0.30, 0.25]         :  West -> 0.862; South -> 0.694; North -> 0.685; East -> 0.300



===============================================================
### Conclusion for Level 2: Product Analysis
===============================================================

- Unlike the near-tie between South and West on Level 1, product-level analysis points clearly to West as the strongest closure candidate — it leads across all three weighting scenarios (0.815 baseline, 0.722 equal, 0.862 margin-focused), with its lead widening substantially once margin is emphasized.
- South's position weakens considerably at Level 2: after nearly tying West on Level 1, it drops to a clear third under margin-focused weighting (0.548), suggesting South holds more profitable product margin than its Level 1 profile implied — a real reason for caution before finalizing South as a co-candidate.
- North and South stay closely clustered under baseline and equal weighting.
- East's suitability score drops sharply under margin-focus (0.300), indicating East houses disproportionately high-margin products worth protecting.
- Combined with Level 1, West is emerging as the more consistent closure candidate across levels, while South's case now depends more heavily on how Level 3–4 evidence (customer impact, feasibility) weighs in, and North showed a similar trend to that of South at this level.


===============================================================
## LEVEL 3: CUSTOMER IMPACT ANALYSIS
===============================================================


**Q1- Which customers would be affected by closing each potential warehouse?**  
- In North branch, one customer (La Rochelle Gifts) has a large total spending ($81.559) relative to other customers
- In the East branch, two customers with very large purchases ($217.758 and $163.060) could be affected. There are more customers with large sales volumes in this branch relative to others.
- In the West branch, one customer with large volume ($102.628) could be affected.
- In the South branch, two customers ($212.417 and $102.728) could be affected from the closure of its warehouse.
- In summary, the East Branch has more customers with large volume of sales that could cost the company the most. The West branch have customers that comparatively have lower total purchases.


**Q2- Recently, which customers only buy from a specific warehouse?**  

- Only 12 customers are exclusively served by a single warehouse.
- Their collective purchasing volume is generally insignificant (less than 10%) relative to overall sales.
- In general, the impact of closing a branch on dependent customers and their sales would be small.

**Q3- Does any warehouse serve a unique geographic region?**  
- Only Switzerland depends on a single warehouse, which is the b (East) branch.
- The East branch is already the least likely candidate based on previous anlayses


**Q4- What is the average order fulfillment time per warehouse?**  

- Average shipment speed is satisfactory in all branches.
- The average fulfillment time is 3.87 days for the South, 3.83 days for the North, 3.79 days for the East and 3.55 days for the West.
- Customers are the most satisfied with the fast shipping in the West branch and relatively the least satisfied in the South branch. However, they are very close.
- The distinctively long shipment days experienced by some customers could be analysed in terms of employee efficiency, but this is beyond the scope of the objectives of this level.
- Excluded cases are quite low, they are unlikely to change the decision based on available cases.


**Q5- What is order status / problem-order rate by warehouse?**  
- All warehouses have acceptable and similar problematic orders rate, ranging from 3.83% to 5.17%.
- The East branch has the least and the North has the highest rate of problematic orders, but differences are low related to order accuracy. They are similar to the baseline problem rate. No significant deviation/outlier.


**Q6- Can slow-moving products be relocated without hurting service?**  
- East warehouse has the largest burden — 9 slow-moving products totaling 47,949 units to relocate, representing more than all other warehouses combined (22,529 + 18,423 + 9,326 = 50,278)
- South warehouse has the smallest burden — only 3 slow-moving products and 9,326 units to relocate, making it the easiest to close from a slow-mover relocation perspective
- All warehouses have sufficient available capacity (assuming that their storage capacity is almost equal) West has the most space (50% available), while South has the least (25% available), suggesting all could absorb relocated inventory if needed
- East's slow-mover burden is disproportionately high — it contains the largest number of slow-moving products and units, making it a candidate for closure to eliminate dead stock and free up working capital; however, it is also the most profitable and the most efficient warehouse based on previous analyses at Level 1, 2 and partly 3.



### Column Selection and Justification for Level 3 Composite Score  

| Question | Column(s) Selected | Column(s) Excluded | Justification |
|---|---|---|---|
| Q1 | `top_customer_share_pct` | `customer_total_spent`, `warehouse_total_spent` (raw figures) | Expressed as a percentage of the warehouse's total revenue concentrated in a single customer, rather than the raw spend figures, so that customer concentration risk is comparable across warehouses regardless of their overall size. |
| Q2 | `exclusive_customer_spend` | `warehouse_count` | Quantifies, in dollars, the revenue tied to customers who purchase from this warehouse exclusively — the most concrete measure of revenue genuinely at risk if the warehouse closes. `warehouse_count` is excluded, as it is only used to identify exclusivity, not to measure its magnitude. |
| Q3 | `unique_region_count` | `total_orders` (validation only) | Counts the number of geographic regions uniquely served by the warehouse, capturing structural market-exit risk. `total_orders` per country is retained only as a validation check against low-sample-size distortion, not as a scoring input. |
| Q4 | `avg_fulfillment_days` | — | Measures existing service performance; a warehouse already shipping slowly represents less of a service regression if closed. |
| Q5 | `problem_order_pct` | `total_orders`, `problem_orders` (raw counts) | Expressed as a percentage of orders rather than a raw count, so that order-reliability issues are comparable across warehouses regardless of order volume. The raw counts are excluded as they are absorbed into this ratio. |


**Composite scores:**  
Weights for [top_customer_share_pct, exclusive_customer_spend, unique_region_count, avg_fulfillment_days, problem_order_pct]:


- Baseline weights [0.20, 0.30, 0.20, 0.15, 0.15]  :  South -> 0.762; North -> 0.681; West -> 0.0.477; East -> 0.209  
*Sensitivity Analysis (Stress Test):*  
- For equal weights [0.20, 0.20, 0.20, 0.20, 0.20] :  North -> 0.775; South -> 0.749; West -> 0.0.480; East -> 0.230
- Geographic Risk [0.15, 0.15, 0.40, 0.15, 0.15]   :  North -> 0.831; South -> 0.812; West -> 0.610; East -> 0.173
- Service Quality [0.15, 0.15, 0.15, 0.30, 0.25]   :  North -> 0.813; South -> 0.787; West -> 0.433; East -> 0.285



===============================================================
### Conclusion for Level 3: Customer Impact Analysis
===============================================================

- Level 3 analysis tells a very different story from Levels 1–2: South and North are the top closure candidates on customer-impact grounds — consistently in the top two across all four weighting scenarios (South 0.75–0.81, North 0.68–0.83), while West and East are both low-suitability here, with East the clear standout as the warehouse customers most depend on (0.17–0.29 across every scenario).
- This is a meaningful pivot: West, which looked like the strongest closure candidate on Level 1 and Level 2 evidence, now shows real customer-impact risk (0.43–0.61) likely reflecting a concentrated or region-exclusive customer base uncovered in Q1–Q3 that its weaker sales/margin numbers alone didn't capture.
- North and South's ranking order swaps depending on the scenario (North edges ahead under equal, geographic, and service weighting; South leads only under baseline), but the gap between them stays narrow throughout, so they are comparably low-risk from a customer standpoint rather than a definitive choice.
- *The Key Takeaway:* West's Level 1–2 case for closure now needs to be weighed against a real customer-retention risk that didn't show up until this level, while East is reinforced as the warehouse to protect across every dimension analyzed so far.


===============================================================
## LEVEL 4: CONSOLIDATION FEASIBILITY  
===============================================================

**Q1: Which warehouse has the lowest combined sales volume, inventory value, and product count?**

- This is also the Level 4 composite score

### Column Selection and Justification for Level 4 Composite Score  

| Metric | Column Selected | Column(s) Excluded | Justification |
|---|---|---|---|
| Sales | `total_sales_value` | — | The single strongest performance signal, consistent with its treatment in Level 1. |
| Turnover | `turnover_rate` | — | Already validated as the cleanest efficiency signal in Level 2; carried forward with similarly high weight here. |
| Inventory | `total_inventory_value` | — | Reflects real financial exposure, but is secondary to whether the warehouse is actually performing well. |
| Product Count | `distinct_products` | — | The least decisive metric, mainly reflecting operational complexity rather than performance or risk. |


**Composite scores:**  
Weights for [total_sales_value, turnover_rate, total_inventory_value, distinct_products]:  

-- Baseline weights [0.35, 0.30, 0.20, 0.15]           :  West -> 0.883; North -> 0.812; South -> 0.689; East -> 0.300
-- Equal weights [0.20, 0.20, 0.20, 0.20]              :  West -> 0.881; North -> 0.810; South -> 0.742; East -> 0.250
-- Relocation Burden Focused [0.15, 0.15, 0.40, 0.30]  :  West -> 0.878; South -> 0.845; North -> 0.802; East -> 0.150


===============================================================
### Conclusion for Level 4: Consolidation Feasibility
===============================================================  
- West is the clearest and most consistent closure candidate at Level 4, scoring highest across all three weighting scenarios (0.878–0.883) with almost no variation — a strong signal that West's feasibility case doesn't depend on how the metrics are weighted.
- East is consistently the strongest performer and least suitable to close (0.15–0.30), reinforcing its protected status from Levels 1, 2 and 3.
- South and North swap order depending on the scenario — North edges ahead under baseline and equal weighting, but South overtakes it under the relocation-burden focus (0.845 vs. 0.802), suggesting South is comparatively easier to physically close (lower inventory value/product count) even though it isn't the weakest overall performer.
- This is West's fourth consecutive level as the top or near-top closure candidate (alongside its strong showing in Levels 1 and 2), making it the most robust candidate heading into the final Level 5 recommendation — the remaining open question is whether Level 3's customer-impact risk for West (flagged earlier) is significant enough to override this consistency.


**Follow-up Consolidation Feasibility Evaluation:**  
**If we close the lowest-performing warehouse, which other warehouses have capacity to absorb its inventory?**  
*Note: warehousePctCap is a percentage only — the schema has no absolute unit capacity, so "headroom" here is directional, not an exact figure.*

- Available headroom percentages are East (33%), North (28%) and South (25%).
- The East branch has the most headroom and it was the strongest performer and highest-margin warehouse. However, relocating all West products into East may disrupt a functionally efficient warehouse.
- Based on headroom strategy, the inventory could be distributed proportional to headroom percentage. A better strategy is to distribute the inventory to multiple warehouses, moving most of  it to the warehouse with the highest turnover rate (South) that could absorb the inventory relatively more quickly without disrupting their efficiency for a longer time. Most inventory could be relocated to the South, East and North receive the remainder South's headroom can't accommodate.
- Alternatively, Proportional to their turnover rate, South could receive 50% of the inventory, North and East 25% each. Here, the distance between warehouses and relocation costs are assumed to be similar. If not, the decision should take these factors into account.

**How much inventory would need to be moved to close the target warehouse?**  
- Total units in West warehouse to relocate is 124,880 and its total value is 5,704,259
- Based on proportion of available headroom, East can receive 38.4% of the inventory; North 32.6% and South 29.1%


**Conclusion for Consolidation Feasibility Evaluation**  
- The Level 4 composite score strongly validates the operational case for consolidation, with West emerging as the definitive closure candidate for the fourth consecutive level. West achieves the highest feasibility score across all weighting scenarios (0.878–0.883), driven by its consistently low sales, inventory value, product count, and turnover. This ranking aligns perfectly with Level 1 (performance) and Level 2 (efficiency), confirming that West is not merely underperforming in one dimension, but is structurally the weakest link across the board.
- East, conversely, remains the strongest performer (0.15–0.30) and is clearly not a candidate for closure.
- Physically, closing West is operationally feasible. The 124,880 units (valued at ~$5.7M) can be fully absorbed by the remaining warehouses using a proportional headroom split (East 38.4%, North 32.6%, South 29.1%) or a turnover-weighted allocation to accelerate sell-through. However, because the schema lacks absolute unit capacity figures, these distribution strategies remain directional and should be validated against real shelf-space constraints before execution.
- The sole red flag carried forward from Level 3 is West's customer-impact risk while the operational and financial data unanimously point to West, the final closure decision hinges on whether that customer disruption is deemed acceptable or mitigable. If it can be managed, West is the unequivocal choice; if not, South emerges as the second-best operational fallback under the relocation-burden weighting (0.845).



===============================================================
## FINAL WEIGHTED DECISION 
===============================================================


### Level Weight Selection and Justification for the Final Recommendation

| Scenario | Weights (L1/L2/L3/L4) | Justification | Result (Ranked) |
|---|---|---|---|
| **Baseline** | 0.15 / 0.35 / 0.30 / 0.20 | Product performance and customer risk carry the most weight, consistent with the level weighting established throughout the analysis; serves as the primary, default-trust scenario. | West 0.727 → South 0.681 → North 0.679 → East 0.300 |
| **Equal weighting** | 0.25 / 0.25 / 0.25 / 0.25 | Removes analyst judgment entirely, serving as a neutral control case to test whether the baseline's emphasis on product and customer data is actually driving the outcome. | West 0.724 → South 0.704 → North 0.693 → East 0.273 |
| **Growth-protective** | 0.10 / 0.20 / 0.50 / 0.20 | Prioritizes customer retention and service continuity above all else, reflecting a business unwilling to risk existing accounts or regional coverage, even at the cost of slower cost savings. | South 0.710 → North 0.676 → West 0.659 → East 0.268 |
| **Cost-cutting / operationally driven** | 0.20 / 0.30 / 0.10 / 0.40 | Prioritizes execution ease and current performance while deliberately minimizing customer-risk weight, reflecting a business under financial pressure that needs to close a warehouse soon with minimal operational disruption. | West 0.808 → North 0.709 → South 0.679 → East 0.302 |
| **Status-quo-conservative** | 0.30 / 0.30 / 0.30 / 0.10 | Weighs current state, product data, and customer impact equally and heavily, treating feasibility as a lesser concern; appropriate for a decision-maker who wants broad-based evidence before acting. | West 0.719 → South 0.707 → North 0.669 → East 0.267 |

## 🎯Summary:  
✅ West is the top-ranked closure candidate in 4 of the 5 scenarios, losing only under the Growth-protective weighting, where South overtakes it.  
🏆East ranks lowest across every scenario, reinforcing it as the warehouse to protect.



