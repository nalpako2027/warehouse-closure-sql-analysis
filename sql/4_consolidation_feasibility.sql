-- ===============================================================
-- ################# Level 4: Consolidation Feasibility ##########
-- ===============================================================


-- ===============================================================
-- Q1: Which warehouse has the lowest combined sales volume, inventory value,
--     and product count? (This is also the Level 4 composite score.)

WITH

sales AS (
    SELECT 
		w.warehouseCode, 
		w.warehouseName,
		ROUND(SUM(od.quantityOrdered * od.priceEach), 2) AS total_sales_value
    FROM warehouses w
    JOIN products p ON p.warehouseCode = w.warehouseCode
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY w.warehouseCode, w.warehouseName
),

inventory AS (
    SELECT 
		w.warehouseCode,
		SUM(p.quantityInStock * p.buyPrice) AS total_inventory_value
    FROM warehouses w
    JOIN products p ON p.warehouseCode = w.warehouseCode
    GROUP BY w.warehouseCode
),

products_count AS (
    SELECT 
		w.warehouseCode,
		COUNT(DISTINCT p.productCode) AS distinct_products
    FROM warehouses w
    JOIN products p ON p.warehouseCode = w.warehouseCode
    GROUP BY w.warehouseCode
),

turnover AS (
    SELECT 
		w.warehouseCode,
		ROUND(SUM(COALESCE(od.quantityOrdered, 0)) / NULLIF(SUM(p.quantityInStock), 0), 3) AS turnover_rate
    FROM warehouses w
    JOIN products p ON p.warehouseCode = w.warehouseCode
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber AND o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY w.warehouseCode
),

combined AS (
    SELECT s.warehouseCode, s.warehouseName, s.total_sales_value,
           i.total_inventory_value, pc.distinct_products, t.turnover_rate
    FROM sales s
    JOIN inventory i ON i.warehouseCode = s.warehouseCode
    JOIN products_count pc ON pc.warehouseCode = s.warehouseCode
    JOIN turnover t ON t.warehouseCode = s.warehouseCode
),

normalized AS (
    SELECT
        warehouseCode, warehouseName,
        -- high sales -> invert
        ROUND(1 - (total_sales_value - MIN(total_sales_value) OVER())
              / NULLIF(MAX(total_sales_value) OVER() - MIN(total_sales_value) OVER(), 0), 3) AS n_sales,
        -- high inventory value ->  invert
        ROUND(1 - (total_inventory_value - MIN(total_inventory_value) OVER())
              / NULLIF(MAX(total_inventory_value) OVER() - MIN(total_inventory_value) OVER(), 0), 3) AS n_inventory,
        -- high product count -> invert
        ROUND(1 - (distinct_products - MIN(distinct_products) OVER())
              / NULLIF(MAX(distinct_products) OVER() - MIN(distinct_products) OVER(), 0), 3) AS n_products,
        -- high turnover  invert
        ROUND(1 - (turnover_rate - MIN(turnover_rate) OVER())
              / NULLIF(MAX(turnover_rate) OVER() - MIN(turnover_rate) OVER(), 0), 3) AS n_turnover
    FROM combined
)

SELECT
    n.warehouseCode, n.warehouseName,
    n_sales, n_inventory, n_products, n_turnover,
    ROUND(
        n_sales     * 0.15 +
        n_turnover  * 0.15 +
        n_inventory * 0.40 +
        n_products  * 0.30
    , 3) AS level4_composite_score
FROM normalized n
ORDER BY level4_composite_score DESC;

-- WEIGHTS SELECTION:
-- Baseline weights [0.35, 0.30, 0.20, 0.15]: Sales value gets the largest weight (0.35) — the
-- single strongest performance signal, weighted highest, consistent with how it was treated in
-- Level 1. Turnover rate is second (0.30) — already validated as the cleanest efficiency signal
-- in Level 2; carried forward with similarly high weight here. Inventory value (0.20) reflects
-- real financial exposure, but is secondary to whether the warehouse is actually performing well.
-- Product count (0.15) is the least decisive metric — mainly reflects operational complexity
-- rather than performance or risk.

-- Results: 
-- Baseline weights [0.35, 0.30, 0.20, 0.15]           :  West -> 0.883; North -> 0.812; South -> 0.689; East -> 0.300
-- Equal weights [0.20, 0.20, 0.20, 0.20]              :  West -> 0.881; North -> 0.810; South -> 0.742; East -> 0.250
-- Relocation Burden Focused [0.15, 0.15, 0.40, 0.30]  :  West -> 0.878; South -> 0.845; North -> 0.802; East -> 0.150


-- Conclusion: 
-- West is the clearest and most consistent closure candidate at Level 4, scoring highest across all three weighting 
-- scenarios (0.878–0.883) with almost no variation — a strong signal that West's feasibility case doesn't depend on 
-- how the metrics are weighted.
-- East is consistently the strongest performer and least suitable to close (0.15–0.30), reinforcing its protected 
-- status from Levels 1, 2 and 3.
-- South and North swap order depending on the scenario — North edges ahead under baseline and equal weighting, but 
-- South overtakes it under the relocation-burden focus (0.845 vs. 0.802), suggesting South is comparatively easier 
-- to physically close (lower inventory value/product count) even though it isn't the weakest overall performer.
-- This is West's fourth consecutive level as the top or near-top closure candidate (alongside its strong showing 
-- in Levels 1 and 2), making it the most robust candidate heading into the final Level 5 recommendation — the 
-- remaining open question is whether Level 3's customer-impact risk for West (flagged earlier) is significant enough 
-- to override this consistency.


-- ===============================================================
-- Q2: If we close the lowest-performing warehouse, which other warehouses
--     have capacity to absorb its inventory? 

SET @target_warehouse = 'West';   -- the warehouse in Q1 that ranks #1 

SELECT
    warehouseName,
    warehousePctCap,
    ROUND(100 - warehousePctCap, 1) AS available_headroom_pct
FROM warehouses
WHERE warehouseCode IS NOT NULL
  AND warehouseName <> @target_warehouse
ORDER BY available_headroom_pct DESC;

-- Note: warehousePctCap is a percentage only — the schema has no absolute unit
-- capacity, so "headroom" here is directional, not an exact figure.

-- Results: 
-- Available headroom percentages are East (33%), North (28%) and South (25%). 
-- The East branch has the most headroom and it was the strongest performer and highest-margin warehouse. However, relocating 
-- all West products into East may disrupt a functionally efficient warehouse. Based on headroom strategy, the inventory could be 
-- distributed proportional to headroom percentage. A better strategy is to distribute the inventory to multiple warehouses, moving 
-- most of  it to the warehouse with the highest turnover rate (South) that could absorb the inventory relatively more quickly 
-- without disrupting their efficiency for a longer time. Most inventory could be relocated to the South, East and North receive 
-- the remainder South's headroom can't accommodate. Alternatively, Proportional to their turnover rate, South could receive 50% of 
-- the inventory, North and East 25% each.
-- Here, the distance between warehouses and relocation costs are assumed to be similar. If not, the decision should take these factors
-- into account.


-- ===============================================================
-- Q3: How much inventory would need to be moved to close the target warehouse?

SELECT
    w.warehouseName,
    SUM(p.quantityInStock) AS total_units_to_relocate,
    ROUND(SUM(p.quantityInStock * p.buyPrice), 2) AS total_value_to_relocate
FROM warehouses w
JOIN products p ON p.warehouseCode = w.warehouseCode
WHERE w.warehouseName = @target_warehouse
GROUP BY w.warehouseName;

-- Results: 
-- Total units in West warehouse to relocate is 124,880 and its total value is 5,704,259


-- ===============================================================
-- Post-closure capacity check 
-- Two allocation strategies: most-room-first vs. proportional split

WITH target_units AS (
    SELECT SUM(p.quantityInStock) AS units_to_relocate
    FROM warehouses w
    JOIN products p ON p.warehouseCode = w.warehouseCode
    WHERE w.warehouseName = @target_warehouse
),

remaining AS (
    SELECT warehouseName, warehousePctCap,
           ROUND(100 - warehousePctCap, 1) AS headroom_pct
    FROM warehouses
    WHERE warehouseCode IS NOT NULL AND warehouseName <> @target_warehouse
),

total_headroom AS (
    SELECT SUM(headroom_pct) AS sum_headroom FROM remaining
)

SELECT
    r.warehouseName,
    r.warehousePctCap AS current_pct_cap,
    r.headroom_pct,
    CASE WHEN r.headroom_pct = (SELECT MAX(headroom_pct) FROM remaining)
         THEN 'Receives full relocation (most-room strategy)'
         ELSE 'No relocation under this strategy'
    END AS strategy_a_most_room,
    ROUND(r.headroom_pct / (SELECT sum_headroom FROM total_headroom) * 100, 1) AS strategy_b_proportional_share_pct
FROM remaining r
ORDER BY r.headroom_pct DESC;

-- Validation note: no absolute-unit capacity column exists, so this shows relocation
-- STRATEGY (who receives how much share) rather than a recomputed post-closure %.
-- Present qualitatively in the report unless an assumed total-capacity figure is supplied.
-- Results: 
-- Based on proportion of available headroom, East can receive 38.4% of the inventory; North 32.6% and South 29.1%




-- ===============================================================
-- ##### CONCLUSION FOR CONSOLIDATION FEASIBILITY #####
-- ===============================================================
-- The Level 4 composite score strongly validates the operational case for consolidation, with West emerging as 
-- the definitive closure candidate for the fourth consecutive level. West achieves the highest feasibility score 
-- across all weighting scenarios (0.878–0.883), driven by its consistently low sales, inventory value, product 
-- count, and turnover. This ranking aligns perfectly with Level 1 (performance) and Level 2 (efficiency), confirming 
-- that West is not merely underperforming in one dimension, but is structurally the weakest link across the board. 
-- East, conversely, remains the strongest performer (0.15–0.30) and is clearly not a candidate for closure.
-- Physically, closing West is operationally feasible. The 124,880 units (valued at ~$5.7M) can be fully absorbed by 
-- the remaining warehouses using a proportional headroom split (East 38.4%, North 32.6%, South 29.1%) or a turnover-weighted 
-- allocation to accelerate sell-through. However, because the schema lacks absolute unit capacity figures, these 
-- distribution strategies remain directional and should be validated against real shelf-space constraints before execution.

-- The sole red flag carried forward from Level 3 is West's customer-impact risk while the operational and financial data 
-- unanimously point to West, the final closure decision hinges on whether that customer disruption is deemed acceptable or 
-- mitigable. If it can be managed, West is the unequivocal choice; if not, South emerges as the second-best operational 
-- fallback under the relocation-burden weighting (0.845).

-- Orhan Kaplan
-- Github Account: nalpkao2027
