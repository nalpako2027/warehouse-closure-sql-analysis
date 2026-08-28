-- ===============================================================
-- ############# Level 3: Customer Impact Analysis ###############
-- ===============================================================

-- ===============================================================
## Q1- Which customers would be affected by closing each potential warehouse?
-- Calculate customer total spending from a warehouse and their ranking

WITH total_spent AS(
	SELECT 
		c.customerNumber, 
        c.customerName, 
        c.country, 
        w.warehouseCode, 
        w.warehouseName,
        SUM(od.quantityOrdered * od.priceEach) AS customer_total_spent
    FROM customers c
    INNER JOIN orders o ON c.customerNumber = o.customerNumber
    INNER JOIN orderdetails od ON od.orderNumber = o.orderNumber
    INNER JOIN products p ON od.productCode = p.productCode
    INNER JOIN warehouses w ON p.warehouseCode = w.warehouseCode
    WHERE o.orderDate BETWEEN '2004-06-01' AND '2005-05-31'
		AND o.status NOT IN ('Cancelled', 'Disputed')
	GROUP BY 
		c.customerNumber, 
        c.customerName, 
        c.country, 
        w.warehouseCode, 
        w.warehouseName
)
SELECT 
	*,
	ROW_NUMBER() OVER(
        PARTITION BY warehouseCode
        ORDER BY customer_total_spent DESC
    ) AS cust_spent_rank
FROM total_spent; 

-- Result: 
-- In North branch, one customer (La Rochelle Gifts) has a large total spending ($81.559) relative to other customers
-- In the East branch, two customers with very large purchases ($217.758 and $163.060) could be affected. There are more 
-- customers with large sales volumes in this branch relative to others.
-- In the West branch, one customer with large volume ($102.628) could be affected.
-- In the South branch, two customers ($212.417 and $102.728) could be affected from the closure of its warehouse.
-- In summary, the East Branch has more customers with large volume of sales that could cost the company the most. The West branch
-- have customers that comparatively have lower total purchases.


-- ===============================================================
## Q2- Recently, which customers only buy from a specific warehouse?

WITH customer_warehouse_spending AS (
    -- Step 1: Calculate total spending per customer per warehouse
    SELECT 
        c.customerNumber,
        c.customerName,
        c.country,
        w.warehouseCode,
        w.warehouseName,
        SUM(od.quantityOrdered * od.priceEach) AS total_spent
    FROM customers c
    INNER JOIN orders o ON c.customerNumber = o.customerNumber
    INNER JOIN orderdetails od ON o.orderNumber = od.orderNumber
    INNER JOIN products p ON od.productCode = p.productCode
    INNER JOIN warehouses w ON p.warehouseCode = w.warehouseCode
    WHERE o.orderDate BETWEEN '2004-06-01' AND '2005-05-31'
        AND o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY 
        c.customerNumber,
        c.customerName,
        c.country,
        w.warehouseCode,
        w.warehouseName
),
customer_warehouse_count AS (
    -- Step 2: Count how many warehouses each customer buys from
    SELECT 
        customerNumber,
        COUNT(DISTINCT warehouseCode) AS warehouse_count
    FROM customer_warehouse_spending
    GROUP BY customerNumber
)
-- Step 3: Join them to get only customers with 1 warehouse
SELECT 
    cws.customerNumber,
    cws.customerName,
    cws.country,
    cws.warehouseCode,
    cws.warehouseName,
    ROUND(cws.total_spent, 2) AS total_spent,
    cwc.warehouse_count
FROM customer_warehouse_spending cws
INNER JOIN customer_warehouse_count cwc 
    ON cws.customerNumber = cwc.customerNumber
WHERE cwc.warehouse_count = 1
ORDER BY cws.total_spent DESC;

-- Result: 
-- Only 12 customers are exclusively served by a single warehouse.
-- Their collective purchasing volume is generally insignificant (less than 10%) relative to overall sales.
-- In general, the impact of closing a branch on dependent customers and their sales would be small.


-- ===============================================================
-- Q3: Does any warehouse serve a unique geographic region?

WITH country_warehouse AS (
    SELECT DISTINCT
        c.country,
        p.warehouseCode
    FROM customers c
    JOIN orders o ON o.customerNumber = c.customerNumber
    JOIN orderdetails od ON od.orderNumber = o.orderNumber
    JOIN products p ON p.productCode = od.productCode
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
),

country_warehouse_count AS (
    SELECT country, COUNT(DISTINCT warehouseCode) AS warehouse_count
    FROM country_warehouse
    GROUP BY country
)

SELECT
    cw.warehouseCode,
    cw.country,
    cwc.warehouse_count
FROM country_warehouse cw
JOIN country_warehouse_count cwc ON cwc.country = cw.country
WHERE cwc.warehouse_count = 1
ORDER BY cw.warehouseCode, cw.country;

-- Validation: check sample size before trusting any "uniquely served" country
SELECT
    c.country,
    COUNT(DISTINCT o.orderNumber) AS total_orders
FROM customers c
JOIN orders o ON o.customerNumber = c.customerNumber
GROUP BY c.country
ORDER BY total_orders ASC;

-- Rollup: count of uniquely-served regions per warehouse (for scoring)
WITH country_warehouse AS (
    SELECT DISTINCT c.country, p.warehouseCode
    FROM customers c
    JOIN orders o ON o.customerNumber = c.customerNumber
    JOIN orderdetails od ON od.orderNumber = o.orderNumber
    JOIN products p ON p.productCode = od.productCode
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
),
country_warehouse_count AS (
    SELECT country, COUNT(DISTINCT warehouseCode) AS warehouse_count
    FROM country_warehouse
    GROUP BY country
)
SELECT
    cw.warehouseCode,
    COUNT(DISTINCT cw.country) AS unique_region_count
FROM country_warehouse cw
JOIN country_warehouse_count cwc ON cwc.country = cw.country
WHERE cwc.warehouse_count = 1
GROUP BY cw.warehouseCode
ORDER BY unique_region_count DESC;


-- Result: 
-- Only Switzerland depends on a single warehouse, which is the b (East) branch. 
-- The East branch is already the least likely candidate based on previous anlayses

-- ===============================================================
-- Q4: What is the average order fulfillment time per warehouse? 

WITH warehouse_orders AS (
    SELECT DISTINCT
        p.warehouseCode,
        o.orderNumber,
        o.orderDate,
        o.shippedDate
    FROM products p
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
)

SELECT
    wo.warehouseCode,
    w.warehouseName,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN shippedDate IS NULL THEN 1 ELSE 0 END) AS excluded_unshipped,
    ROUND(AVG(CASE WHEN shippedDate IS NOT NULL THEN DATEDIFF(shippedDate, orderDate) END), 2) AS avg_fulfillment_days
FROM warehouse_orders wo
LEFT JOIN warehouses w ON wo.warehouseCode = w.warehouseCode
GROUP BY warehouseCode, warehouseName
ORDER BY avg_fulfillment_days DESC;

-- Result: 
-- Average shipment speed is satisfactory in all branches. 
-- The average fulfillment time is 3.87 days for the South, 3.83 days for the North, 3.79 days for the East and 3.55 days for the West. 
-- Customers are the most satisfied with the fast shipping in the West branch and relatively the least satisfied in the South branch.  
-- However, they are very close. The distinctively long shipment days experienced by some customers could be analysed in terms of 
-- of employee efficiency, but this is beyond the scope of the objectives of this level. 
-- Excluded cases are quite low, they are unlikely to change the decision based on available cases.

-- ===============================================================
-- Q5: What is order status / problem-order rate by warehouse? 

WITH warehouse_orders AS (
    SELECT DISTINCT
        p.warehouseCode,
        o.orderNumber,
        o.status
    FROM products p
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
),

warehouse_problem_rate AS (
    SELECT
        warehouseCode,
        COUNT(*) AS total_orders,
        SUM(CASE WHEN status IN ('Cancelled','On Hold','Disputed') THEN 1 ELSE 0 END) AS problem_orders,
        ROUND(SUM(CASE WHEN status IN ('Cancelled','On Hold','Disputed') THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS pct_problem_order
    FROM warehouse_orders
    GROUP BY warehouseCode
),

company_baseline AS (
    SELECT ROUND(
        SUM(CASE WHEN status IN ('Cancelled','On Hold','Disputed') THEN 1 ELSE 0 END) / COUNT(*) * 100, 2
    ) AS pct_baseline_problem
    FROM orders
)

SELECT
    w.warehouseName,
    wpr.*,
    cb.pct_baseline_problem,
    ROUND(wpr.pct_problem_order - cb.pct_baseline_problem, 2) AS diff_from_baseline
FROM warehouse_problem_rate wpr
CROSS JOIN company_baseline cb
LEFT JOIN warehouses w ON wpr.warehouseCode = w.warehouseCode
ORDER BY pct_problem_order DESC;


-- Result:
-- All warehouses have acceptable and similar problematic orders rate, ranging from 3.83% to 5.17%. 
-- The East branch has the least and the North has the highest rate of problematic orders, but differences are low 
-- related to order accuracy. They are similar to the baseline problem rate. No significant deviation/outlier.

-- ===============================================================
-- Q6: Can slow-moving products be relocated without hurting service?
-- Note: The anlaysis to this question reports the burden, not a full feasibility model; 
-- the real feasibility check belongs in Level 4


WITH product_sales AS (
    SELECT
        p.productCode, 
        p.warehouseCode, 
        p.quantityInStock,
        COALESCE(SUM(od.quantityOrdered), 0) AS units_sold  
    FROM products p
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber
                       AND o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY p.productCode, p.warehouseCode, p.quantityInStock
),

slow_movers AS (
    SELECT *, NTILE(5) OVER (ORDER BY units_sold ASC) AS volume_tile
    FROM product_sales
),

slow_mover_burden AS (
    SELECT
        warehouseCode,
        COUNT(*) AS slow_mover_count,
        SUM(quantityInStock) AS slow_mover_units_to_relocate
    FROM slow_movers
    WHERE volume_tile = 1 --  only 20% slow movers 
    GROUP BY warehouseCode
)

SELECT
    w.warehouseName,
    smb.slow_mover_count,
    smb.slow_mover_units_to_relocate,
    w.warehousePctCap,
    ROUND(100 - w.warehousePctCap, 1) AS own_available_capacity_pct
FROM slow_mover_burden smb
JOIN warehouses w ON w.warehouseCode = smb.warehouseCode
ORDER BY smb.slow_mover_units_to_relocate DESC;

-- Results: 
-- East warehouse has the largest burden — 9 slow-moving products totaling 47,949 units to relocate, 
-- representing more than all other warehouses combined (22,529 + 18,423 + 9,326 = 50,278)
-- South warehouse has the smallest burden — only 3 slow-moving products and 9,326 units to relocate, 
-- making it the easiest to close from a slow-mover relocation perspective
-- All warehouses have sufficient available capacity (assuming that their storage capacity is almost equal) 
-- West has the most space (50% available), while South has the least (25% available), suggesting all could absorb relocated inventory if needed
-- East's slow-mover burden is disproportionately high — it contains the largest number of slow-moving 
-- products and units, making it a candidate for closure to eliminate dead stock and free up working capital;
-- however, it is also the most profitable and the most efficient warehouse based on previous analyses at Level 1, 2 and partly 3.

-- ===============================================================
-- ##### LEVEL 3 COMPOSITE: CUSTOMER IMPACT ANALYSIS #####
-- ===============================================================

WITH customer_spend AS (
    SELECT c.customerNumber, p.warehouseCode,
           SUM(od.quantityOrdered * od.priceEach) AS customer_total_spent
    FROM customers c
    JOIN orders o ON o.customerNumber = c.customerNumber
    JOIN orderdetails od ON od.orderNumber = o.orderNumber
    JOIN products p ON p.productCode = od.productCode
    WHERE o.orderDate BETWEEN '2004-06-01' AND '2005-05-31'
      AND o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY c.customerNumber, p.warehouseCode
),
warehouse_totals AS (
    SELECT 
		warehouseCode, 
        SUM(customer_total_spent) AS warehouse_total_spent
    FROM customer_spend 
    GROUP BY warehouseCode
),
top_customer AS (
    SELECT 
		warehouseCode, 
        MAX(customer_total_spent) AS top_customer_spent
    FROM customer_spend 
    GROUP BY warehouseCode
),
concentration AS (
    SELECT tc.warehouseCode,
           ROUND(tc.top_customer_spent / wt.warehouse_total_spent * 100, 2) AS top_customer_share_pct
    FROM top_customer tc
    JOIN warehouse_totals wt ON wt.warehouseCode = tc.warehouseCode
),

customer_warehouse_spending AS (
    SELECT c.customerNumber, p.warehouseCode,
           SUM(od.quantityOrdered * od.priceEach) AS total_spent
    FROM customers c
    JOIN orders o ON o.customerNumber = c.customerNumber
    JOIN orderdetails od ON o.orderNumber = od.orderNumber
    JOIN products p ON od.productCode = p.productCode
    WHERE o.orderDate BETWEEN '2004-06-01' AND '2005-05-31'
      AND o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY c.customerNumber, p.warehouseCode
),
customer_warehouse_count AS (
    SELECT customerNumber, COUNT(DISTINCT warehouseCode) AS warehouse_count
    FROM customer_warehouse_spending GROUP BY customerNumber
),
exclusive_spend AS (
    SELECT cws.warehouseCode, SUM(cws.total_spent) AS exclusive_customer_spend
    FROM customer_warehouse_spending cws
    JOIN customer_warehouse_count cwc ON cwc.customerNumber = cws.customerNumber
    WHERE cwc.warehouse_count = 1
    GROUP BY cws.warehouseCode
),
country_warehouse AS (
    SELECT DISTINCT c.country, p.warehouseCode
    FROM customers c
    JOIN orders o ON o.customerNumber = c.customerNumber
    JOIN orderdetails od ON od.orderNumber = o.orderNumber
    JOIN products p ON p.productCode = od.productCode
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
),
country_warehouse_count AS (
    SELECT 
		country, 
        COUNT(DISTINCT warehouseCode) AS warehouse_count
    FROM country_warehouse 
    GROUP BY country
),
unique_regions AS (
    SELECT 
		cw.warehouseCode, 
        COUNT(DISTINCT cw.country) AS unique_region_count
    FROM country_warehouse cw
    JOIN country_warehouse_count cwc ON cwc.country = cw.country
    WHERE cwc.warehouse_count = 1
    GROUP BY cw.warehouseCode
),

warehouse_orders AS (
    SELECT DISTINCT p.warehouseCode, o.orderNumber, o.orderDate, o.shippedDate, o.status
    FROM products p
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
),
fulfillment AS (
    SELECT warehouseCode,
           ROUND(AVG(CASE WHEN shippedDate IS NOT NULL THEN DATEDIFF(shippedDate, orderDate) END), 2) AS avg_fulfillment_days
    FROM warehouse_orders GROUP BY warehouseCode
),
problem_rate AS (
    SELECT warehouseCode,
           ROUND(SUM(CASE WHEN status IN ('Cancelled','On Hold','Disputed') THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS problem_order_pct
    FROM warehouse_orders GROUP BY warehouseCode
),

combined AS (
    SELECT
        w.warehouseCode,
        COALESCE(c.top_customer_share_pct, 0) AS top_customer_share_pct,
        COALESCE(es.exclusive_customer_spend, 0) AS exclusive_customer_spend,
        COALESCE(ur.unique_region_count, 0) AS unique_region_count,
        f.avg_fulfillment_days,
        p.problem_order_pct
    FROM (SELECT DISTINCT warehouseCode FROM warehouses WHERE warehouseCode IS NOT NULL) w
    LEFT JOIN concentration c ON c.warehouseCode = w.warehouseCode
    LEFT JOIN exclusive_spend es ON es.warehouseCode = w.warehouseCode
    LEFT JOIN unique_regions ur ON ur.warehouseCode = w.warehouseCode
    JOIN fulfillment f ON f.warehouseCode = w.warehouseCode
    JOIN problem_rate p ON p.warehouseCode = w.warehouseCode
),

normalized AS (
    SELECT
        warehouseCode,
        ROUND(1 - (top_customer_share_pct - MIN(top_customer_share_pct) OVER())
              / NULLIF(MAX(top_customer_share_pct) OVER() - MIN(top_customer_share_pct) OVER(), 0), 3) AS n_concentration,
        ROUND(1 - (exclusive_customer_spend - MIN(exclusive_customer_spend) OVER())
              / NULLIF(MAX(exclusive_customer_spend) OVER() - MIN(exclusive_customer_spend) OVER(), 0), 3) AS n_exclusive_spend,
        ROUND(1 - (unique_region_count - MIN(unique_region_count) OVER())
              / NULLIF(MAX(unique_region_count) OVER() - MIN(unique_region_count) OVER(), 0), 3) AS n_unique_regions,
        ROUND((avg_fulfillment_days - MIN(avg_fulfillment_days) OVER())
              / NULLIF(MAX(avg_fulfillment_days) OVER() - MIN(avg_fulfillment_days) OVER(), 0), 3) AS n_fulfillment,
        ROUND((problem_order_pct - MIN(problem_order_pct) OVER())
              / NULLIF(MAX(problem_order_pct) OVER() - MIN(problem_order_pct) OVER(), 0), 3) AS n_problem_rate
    FROM combined
)

SELECT
    w.warehouseName,
    n_concentration, n_exclusive_spend, n_unique_regions, n_fulfillment, n_problem_rate,
    ROUND(
        n_concentration   * 0.15 +
        n_exclusive_spend * 0.15 +
        n_unique_regions  * 0.15 +
        n_fulfillment     * 0.30 +
        n_problem_rate    * 0.25
    , 3) AS level3_composite_score
FROM normalized n
LEFT JOIN warehouses w ON w.warehouseCode = n.warehouseCode
ORDER BY level3_composite_score DESC;

-- WEIGHTS SELECTION:
-- Baseline weights [0.20, 0.30, 0.20, 0.15, 0.15]: Exclusive customer spend receives the largest weight (0.30) 
-- because it is the only metric quantified in real dollars rather than a count or percentage, making it the 
-- most concrete measure of revenue genuinely at risk if a warehouse closes. Customer concentration and unique 
-- region count are tied at 0.20 each, since both represent structural single-point-of-failure risk — one measures 
-- dependency on a single customer, the other dependency on a single geographic market — and neither is inherently 
-- more severe than the other without further business context. Fulfillment time and problem-order rate share the 
-- smallest weight (0.15 each) because both push toward closure rather than against it, and both are indirect 
-- service-quality signals rather than direct measures of customer harm.

-- Equal weighting [0.20, 0.20, 0.20, 0.20, 0.20]: This scenario removes analyst judgment entirely and treats all five 
-- customer-impact signals as equally important, serving as a neutral control case. It tests whether the baseline's 
-- emphasis on exclusive customer spend is actually driving the warehouse ranking, or whether the result holds regardless 
-- of how much weight that single metric receives. Agreement between this scenario and the baseline strengthens 
-- confidence in the ranking; disagreement would indicate the baseline's weighting choices materially shape the outcome.

-- Geographic Risk [0.15, 0.15, 0.40, 0.15, 0.15]: This scenario deliberately concentrates weight on unique region 
-- count (0.40) to test the case where regional market withdrawal is considered a more severe business risk than 
-- losing individual customer accounts. A lost customer can potentially be retained or replaced through account 
-- management; a lost region typically represents a structural market exit with no easy recovery path. The remaining 
-- four metrics are reduced to a uniform low weight (0.15 each) so that geographic exposure is isolated as the dominant 
-- signal, making it possible to see how much the ranking shifts when regional risk is prioritized above all other 
-- customer-impact considerations.

-- Service Quality [0.15, 0.15, 0.15, 0.30, 0.25]: This scenario shifts weight onto the two metrics that reflect a 
-- warehouse's existing service performance — fulfillment time (0.30) and problem-order rate (0.25) — rather than 
-- customer-concentration risk. The rationale is that a warehouse already underperforming on delivery speed and order 
-- reliability is a weaker asset worth protecting, regardless of how much revenue or how many regions currently route 
-- through it; closing an already-underperforming warehouse is a smaller regression in service quality than closing 
-- a fast, reliable one. The three customer-risk metrics are reduced to a uniform low weight (0.15 each) so that current 
-- service performance, rather than customer dependency, becomes the dominant driver of the ranking in this scenario.


-- RESULTS
-- Composite scores: 
-- Baseline weights [0.20, 0.30, 0.20, 0.15, 0.15]  :  South -> 0.762; North -> 0.681; West -> 0.0.477; East -> 0.209

-- Sensitivity Analysis (Stress Test):
-- For equal weights [0.20, 0.20, 0.20, 0.20, 0.20] :  North -> 0.775; South -> 0.749; West -> 0.0.480; East -> 0.230
-- Geographic Risk [0.15, 0.15, 0.40, 0.15, 0.15]   :  North -> 0.831; South -> 0.812; West -> 0.610; East -> 0.173
-- Service Quality [0.15, 0.15, 0.15, 0.30, 0.25]   :  North -> 0.813; South -> 0.787; West -> 0.433; East -> 0.285

-- ===============================================================
-- ##### CONCLUSION FOR CUSTOMER IMPACT ANALYSIS #####
-- ===============================================================

-- Level 3 analysis tells a very different story from Levels 1–2: South and North are the top closure candidates on 
-- customer-impact grounds — consistently in the top two across all four weighting scenarios (South 0.75–0.81, North 0.68–0.83),
-- while West and East are both low-suitability here, with East the clear standout as the warehouse customers most depend on 
-- (0.17–0.29 across every scenario). This is a meaningful pivot: West, which looked like the strongest closure candidate on 
-- Level 1 and Level 2 evidence, now shows real customer-impact risk (0.43–0.61) — likely reflecting a concentrated or 
-- region-exclusive customer base uncovered in Q1–Q3 that its weaker sales/margin numbers alone didn't capture. North and South's 
-- ranking order swaps depending on the scenario (North edges ahead under equal, geographic, and service weighting; South leads 
-- only under baseline), but the gap between them stays narrow throughout, so they are comparably low-risk from a customer standpoint 
-- rather than a definitive choice. 
-- The Key Takeaway: West's Level 1–2 case for closure now needs to be weighed against a real customer-retention risk that didn't 
-- show up until this level, while East is reinforced as the warehouse to protect across every dimension analyzed so far.





