-- ===============================================================
-- ########## LEVEL 0: PRELIMINARY DATA EXPLORATION & VALIDATION ##########
-- ===============================================================

-- Check how many rows each table has: 
SELECT COUNT(*) FROM customers; -- 122
SELECT COUNT(*) FROM warehouses; -- 4
SELECT COUNT(*) FROM employees; -- 23
SELECT COUNT(*) FROM orderdetails; -- 2996
SELECT COUNT(*) FROM orders; -- 326
SELECT COUNT(*) FROM products; -- 110

-- Is orderdetails really one row per order-line (orderNumber + productCode)?
SELECT COUNT(*), COUNT(DISTINCT CONCAT(orderNumber, '-', productCode))
FROM orderdetails;

-- NULL values
SELECT COUNT(*) FROM products WHERE warehouseCode IS NULL;
SELECT COUNT(*) FROM orders WHERE shippedDate IS NULL; -- There are 14 NULL values
SELECT COUNT(*) FROM customers WHERE country IS NULL OR customerName IS NULL;

-- 14 NULL values
SELECT status, COUNT(*) 
FROM orders 
WHERE shippedDate IS NULL 
GROUP BY status;
-- The total is only 14 (4 Cancelled, 4 On Hold and 6 In Process) out of 326 orders (~4.3%), this isn't 
-- large enough to meaningfully bias any warehouse's average on its own but it should be taken into 
-- account when calculating order fulfillment query


-- Some distinct categorical values
SELECT DISTINCT status, COUNT(*) FROM orders GROUP BY status;
SELECT DISTINCT country FROM customers ORDER BY country;

-- Products pointing to a warehouse that doesn't exist?
SELECT * FROM products p
LEFT JOIN warehouses w ON w.warehouseCode = p.warehouseCode
WHERE w.warehouseCode IS NULL;

-- Order lines pointing to a product that doesn't exist?
SELECT * FROM orderdetails od
LEFT JOIN products p ON p.productCode = od.productCode
WHERE p.productCode IS NULL;

-- Duplicate primary keys ? 
SELECT productCode, COUNT(*) FROM products GROUP BY productCode HAVING COUNT(*) > 1;

-- Negative or absurd values in numerical columns?
SELECT * FROM products WHERE buyPrice < 0 OR MSRP < buyPrice OR quantityInStock < 0;
SELECT * FROM warehouses WHERE warehousePctCap < 0 OR warehousePctCap > 100;



-- ===============================================================
-- ########### LEVEL 1: CURRENT STATE OF THE WAREHOUSES ##########
-- ===============================================================

-- ===============================================================
## Warehouse utilization rate
-- Q1- What are the current warehouses and their utilization rates? 

SELECT
	warehouseCode, 
    warehouseName, 
    warehousePctCap
FROM warehouses
WHERE warehouseCode IS NOT NULL
ORDER BY warehousePctCap DESC;

-- Result: 
-- There are 4 warehouses, other three of them use 67% to 75% of store capacity, the warehouse West uses only 
-- 50% of the storage capacity. The West branch have the greatest amount of unused capacity.
-- The last row has NULL values; however, In MySQL Workbench, it is a placeholder for inserting new records.


-- ===============================================================
## Inventory Value & Relocation Cost
-- Q2- What is the total inventory value stored in each warehouse (for potential financial impact)? How much inventory 
-- value would potentially need to be relocated if each warehouse were closed?

SELECT w.warehouseCode, w.warehouseName, SUM(quantityInStock*buyPrice) AS total_inventory_value
FROM warehouses w
JOIN products p ON w.warehouseCode = p.warehouseCode
GROUP BY w.warehouseCode, w.warehouseName
ORDER BY total_inventory_value DESC;

-- Result: 
-- Total inventory value is the lowest in the South branch. Warehouse West is the second lowest.
-- The East branch holds the greatest financial value ($14.1M). It would cost the most logistical and financial impact if closed.
-- The lowest relocation cost would occur if South ($4.1M) or West($5.7) was relocated.


-- ===============================================================
## Warehouse Product Diversity 
-- Q3- What is the total number of distinct products stored in each warehouse? 

SELECT warehouseName, COUNT(DISTINCT p.productCode) AS distinct_products
FROM products p
JOIN warehouses w ON w.warehouseCode = p.warehouseCode
GROUP BY warehouseName
ORDER BY distinct_products DESC;

-- Result: 
-- Warehouses South (23), West (24) and North (25)   almost have the same number of distinct products. 
-- They have considerably lower distinct products than the East branch (38).

-- ===============================================================
## Warehouse Sales Performance
-- Q4- How has each warehouse performed in terms of sales over the last year? 

-- Checking available dates
SELECT orderDate FROM orders ORDER BY orderDate DESC; -- The most recent is 2005-05-31, from 2003-01-06

SELECT 
	w.warehouseCode,
    w.warehouseName,
    COUNT(DISTINCT o.orderNumber) AS total_orders,
    SUM(od.quantityOrdered) AS total_unit_sold,
    ROUND(SUM(od.quantityOrdered*od.priceEach), 2) AS total_sales_value,
    ROUND(AVG(od.quantityOrdered*od.priceEach), 2) AS avg_order_value,
    COUNT(DISTINCT p.productCode) AS unique_products_sold
FROM 
	warehouses w
    INNER JOIN products p ON w.warehouseCode = p.warehouseCode
    INNER JOIN orderdetails od ON p.productCode = od.productCode
    INNER JOIN orders o ON od.orderNumber = o.orderNumber
WHERE
	o.orderDate BETWEEN '2004-06-01' AND '2005-05-31'
    AND o.status IN ('Shipped', 'Resolved') -- only including finished orders ('On Hold' and 'In Process' options are not finalized)
GROUP BY 
	w.warehouseCode, w.warehouseName
ORDER BY total_sales_value DESC;

-- Result: 
-- East is the undisputed sales leader, the revenue engine – It dominates across every single metric: 
-- the highest order volume (101), the highest total unit sales (16,595), and the broadest product assortment 
-- sold (37 unique products). 
-- North and South form a competitive middle tier – North generates the second-highest revenue and unit sales, 
-- while South has slightly more orders (71 vs. 60) and trails closely in average order value ($2,893 vs. $2,977). 
-- Both are stable performers but not exceptional.
-- West has the weakest fundamentals. Despite having the second-highest number of orders (90), it generates 
-- the lowest total revenue and the lowest average order value ($2,751). This indicates a high volume of small, 
-- low-value transactions, which is a classic sign of low-margin.



-- ===============================================================
-- Capacity Utilization and Sales Ranks
-- Q5- Is warehouse capacity utilization actually has a relationship with sales performance?

WITH sales_per_warehouse AS (
    SELECT
        p.warehouseCode,
        SUM(od.quantityOrdered * od.priceEach) AS total_sales_value,
        SUM(od.quantityOrdered)                AS total_units_sold
    FROM orderdetails od
    JOIN products p ON p.productCode = od.productCode
    GROUP BY p.warehouseCode
),

utilization_vs_sales AS (
    SELECT
        w.warehouseCode,
        w.warehouseName,
        w.warehousePctCap,
        s.total_sales_value,
        s.total_units_sold,
        RANK() OVER (ORDER BY w.warehousePctCap DESC)     AS capacity_rank,
        RANK() OVER (ORDER BY s.total_sales_value DESC)   AS sales_rank,
        ROUND(s.total_sales_value / NULLIF(w.warehousePctCap, 0), 2) AS sales_per_pct_capacity
    FROM warehouses w
    JOIN sales_per_warehouse s ON s.warehouseCode = w.warehouseCode
    WHERE w.warehouseCode IS NOT NULL  
)

SELECT * FROM utilization_vs_sales
ORDER BY warehousePctCap DESC;

-- Result: 
-- West: ranked last on both capacity rank and sales rank. This is the least utilized and the weakest performer.
-- South: The most utilized warehouse, ranked 1st in capacity rank (75%) but only 3rd in sales. Additionally, 
-- it has the lowest sales_per_pct_capacity (25,021.93). So there is an efficiency issue here.
-- East: It leads sales by a wide margin ($3.85M vs the next highest North $2.08M). Its sales_per_pct_capacity is the highest.
-- East is the strongest warehouse. 
-- North: For this warehouse, its capacity and sales rank agree; both are second. Its statistics does not suggest for 
-- or against argument for its closure.



-- ===============================================================
-- Sales level and its direction
-- Q6- What is the year-over-year change for each warehouse? Are sales of the warehouses improve/decline?
-- Before the intended query, check the sale status categories:
SELECT DISTINCT status FROM orders;

WITH warehouse_sales AS(
	SELECT 
		w.warehouseCode,
		w.warehouseName,
		CASE
			WHEN o.orderDate BETWEEN '2004-06-01' AND '2005-05-31' THEN 'Recent_Year'
			WHEN o.orderDate BETWEEN '2003-06-01' AND '2004-05-31' THEN 'Previous_Year' 
		END AS period,
		ROUND(SUM(od.quantityOrdered * od.priceEach), 2) AS total_sales
	FROM
		warehouses w
        INNER JOIN products p ON w.warehouseCode = p.warehouseCode
        INNER JOIN orderdetails od ON p.productCode = od.productCode
        INNER JOIN orders o ON od.orderNumber = o.orderNumber
	WHERE 
		o.orderDate BETWEEN '2003-06-01' AND '2005-05-31'
        AND o.status IN ('Shipped', 'Resolved')
	GROUP BY
		w.warehouseCode, w.warehouseName, period
)

SELECT 
	warehouseCode, 
	warehouseName,
    MAX(CASE WHEN period = 'Previous_Year' THEN total_sales END) AS previous_year_sales,
    MAX(CASE WHEN period = 'Recent_Year' THEN total_sales END) AS recent_year_sales,
    ROUND(
		MAX(CASE WHEN period = 'Recent_Year' THEN total_sales END) - 
        MAX(CASE WHEN period = 'Previous_Year' THEN total_sales END)) AS total_sales_increase,
    ROUND(
		((MAX(CASE WHEN period = 'Recent_Year' THEN total_sales END) - 
        MAX(CASE WHEN period = 'Previous_Year' THEN total_sales END)) /
        MAX(CASE WHEN period = 'Previous_Year' THEN total_sales END))*100, 
        2
    ) AS growth_percentage
FROM 
	warehouse_sales
GROUP BY 
warehouseCode, warehouseName
ORDER BY growth_percentage DESC;

-- Result: 
-- The East branch has the lowest growth percentage (16.65%), while the West branch has the highest (31.70%).
-- However, the East branch has the highest year-over-year increase in total sales, with sales increasing by approximately $257K.
-- This difference is largely related to the East branch's much larger sales base. Its recent-year sales 
-- are approximately $1.54M, substantially higher than the other branches.
-- The West branch shows the strongest relative growth, increasing its sales by 31.70%, despite having one of 
-- the lowest total sales volumes.
-- The North branch's 34.84% growth rate is relatively strong, but its sales growth appears more modest when 
-- considered alongside its overall sales volume.
-- Overall, all four branches experienced positive year-over-year sales growth, so none currently shows an 
-- absolute decline in sales.
-- The East branch's combination of high sales volume and comparatively lower growth suggests a more mature 
-- sales base, whereas the West branch shows stronger relative expansion from a smaller base.



-- ===============================================================
-- ##### LEVEL 1 COMPOSITE SCORE: Current State Assessment #####
-- ===============================================================

-- First, select columns of interest and the justification for its inclusion

-- Q1
-- warehousePctCap: The direct utilization signal

-- Q2
-- total_inventory_value: Doubles as the relocation-cost proxy

-- Q3
-- distinct_products: Measures operational complexity of closing the location

-- Q4 
-- total_sales_value: The core performance signal (total_orders excluded because it can mislead, e.g., more low-value orders)
-- avg_order_value: Captures customer quality independent of purchase volume
-- To prevent double counting risk, unique_products_sold excluded, Q3 already includes it (distinct_products)

-- Q5
-- sales_per_pct_capacity: The indicator of warehouse efficiency
-- Capacity rank and sales rank columns are diagnostic, not scoring inputs

-- Q6
-- growth_percentage: Growth rate is size independent, a good indicator for fair cross-warehouse comparison

WITH 
utilization AS(
	SELECT 
		warehouseCode, 
        warehouseName, 
        warehousePctCap
    FROM warehouses
    WHERE warehouseCode IS NOT NULL
), 

inventory_value AS(
	SELECT 
		w.warehouseCode,
        SUM(p.quantityInStock*p.buyPrice) AS total_inventory_value
	FROM warehouses w
    JOIN products p ON w.warehouseCode = p.warehouseCode
    GROUP BY w.warehouseCode
),
product_diversity AS (
	SELECT w.warehouseCode,
		COUNT(DISTINCT p.productCode) AS distinct_products
	FROM warehouses w
    JOIN products p ON w.warehouseCode = p.warehouseCode
    GROUP BY w.warehouseCode
),
sales_performance AS (
	SELECT
		w.warehouseCode,
        ROUND(SUM(od.quantityOrdered*od.priceEach), 2) AS total_sales_value,
        ROUND(AVG(od.quantityOrdered*od.priceEach),2) AS avg_order_value
	FROM warehouses w
    JOIN products p ON w.warehouseCode = p.warehouseCode
    JOIN orderdetails od ON p.productCode = od.productCode
    JOIN orders o ON od.orderNumber = o.orderNumber
    WHERE o.orderDate BETWEEN '2004-06-01' AND '2005-05-31'
		AND o.status IN ('Shipped', 'Resolved')
	GROUP BY w.warehouseCode
),
capacity_efficiency AS (
	SELECT 
		p.warehouseCode,
        ROUND(SUM(od.quantityOrdered*od.priceEach) / NULLIF (w.warehousePctCap, 0), 2) AS sales_per_pct_capacity
	FROM warehouses w
    JOIN products p ON w.warehouseCode = p.warehouseCode
    JOIN orderdetails od ON p.productCode = od.productCode
    GROUP BY p.warehouseCode, w.warehousePctCap
),
warehouse_sales_periods AS (
	SELECT 
		w.warehouseCode,
        CASE
			WHEN o.orderDate BETWEEN '2004-06-01' AND '2005-05-31' THEN 'Recent_Year'
            WHEN o.orderDate BETWEEN '2003-06-01' AND '2004-05-31' THEN 'Previous_Year'
		END AS period,
        SUM(od.quantityOrdered*od.priceEach) AS total_sales
	FROM warehouses w
    JOIN products p ON w.warehouseCode = p.warehouseCode
    JOIN orderdetails od ON p.productCode = od.productCode
    JOIN orders o ON od.orderNumber = o.orderNumber
    WHERE 
		o.orderDate BETWEEN '2003-06-01' AND '2005-05-31'
        AND o.status IN ('Shipped', 'Resolved')
	GROUP BY w.warehouseCode, period
),
yoy_growth AS (
	SELECT 
		warehouseCode,
        ROUND(
			((MAX(CASE WHEN period = 'Recent_Year' THEN total_sales END) - 
            MAX(CASE WHEN period = 'Previous_Year' THEN total_sales END)) /
            MAX(CASE WHEN period = 'Previous_Year' THEN total_sales END)) * 100, 2
		) AS growth_percentage
	FROM warehouse_sales_periods
    GROUP BY warehouseCode
),
combined_metrics AS (
	SELECT 
		u.warehouseCode,
        u.warehouseName,
        u.warehousePctCap,
        iv.total_inventory_value,
        pd.distinct_products,
        sp.total_sales_value,
        sp.avg_order_value,
        ce.sales_per_pct_capacity,
        yg.growth_percentage
	FROM 
		utilization u
	JOIN inventory_value iv ON iv.warehouseCode = u.warehouseCode
    JOIN product_diversity pd ON pd.warehouseCode = u.warehouseCode
    JOIN sales_performance sp ON sp.warehouseCode = u.warehouseCode
    JOIN capacity_efficiency ce ON ce.warehouseCode = u.warehouseCode
    JOIN yoy_growth yg ON yg.warehouseCode = u.warehouseCode
),
normalized AS (
	SELECT 
		warehouseCode,
        warehouseName,
        -- Normalize each metric 0-1 across warehouses. Direction-corrected so that higher 
        -- normalized vlaue suggests more suitable to close
        ROUND (1- (warehousePctCap - MIN(warehousePctCap) OVER())
			/ NULLIF(MAX(warehousePctCap) OVER() - MIN(warehousePctCap) OVER(), 0), 3) AS n_utilization,
		ROUND (1- (total_inventory_value - MIN(total_inventory_value) OVER())
			/ NULLIF(MAX(total_inventory_value) OVER() - MIN(total_inventory_value) OVER(), 0), 3) AS n_inventory_value,
		ROUND (1- (distinct_products - MIN(distinct_products) OVER())
			/ NULLIF(MAX(distinct_products) OVER() - MIN(distinct_products) OVER(), 0), 3) AS n_product_diversity,
		ROUND (1- (total_sales_value - MIN(total_sales_value) OVER())
			/ NULLIF(MAX(total_sales_value) OVER() - MIN(total_sales_value) OVER(), 0), 3) AS n_sales_value,
		ROUND (1- (avg_order_value - MIN(avg_order_value) OVER())
			/ NULLIF(MAX(avg_order_value) OVER() - MIN(avg_order_value) OVER(), 0), 3) AS n_avg_order_value,
		ROUND (1- (sales_per_pct_capacity - MIN(sales_per_pct_capacity) OVER())
			/ NULLIF(MAX(sales_per_pct_capacity) OVER() - MIN(sales_per_pct_capacity) OVER(), 0), 3) AS n_capacity_efficiency,
		ROUND (1- (growth_percentage - MIN(growth_percentage) OVER())
			/ NULLIF(MAX(growth_percentage) OVER() - MIN(growth_percentage) OVER(), 0), 3) AS n_growth
	FROM combined_metrics
)
-- Apply within-level weights and produce the Level 1 (Current State Assessment) composite score
SELECT
	warehouseCode,
    warehouseName,
    n_utilization,
    n_inventory_value,
    n_product_diversity,
    n_sales_value,
    n_avg_order_value,
    n_capacity_efficiency,
    n_growth,
    ROUND(
		n_utilization * 0.10 -- These weights were changed for each weight distribution scenario given below
        + n_inventory_value * 0.20
        + n_product_diversity * 0.10
        + n_sales_value * 0.25
        + n_avg_order_value * 0.10
        + n_capacity_efficiency * 0.15
        + n_growth * 0.10
	, 3) AS level1_composite_score
FROM normalized
ORDER BY level1_composite_score DESC;

-- RESULTS:
-- Composite scores: 
-- Baseline weights [0.10, 0.20, 0.10, 0.25, 0.10, 0.15, 0.10].       :  South -> 0.816; West -> 0.811; North -> 0.676; East -> 0.132

-- Sensitivity Analysis (Stress Test):
-- For equal weights [0.143, 0.143, 0.143, 0.143, 0.143, 0.143, 0.143]:  West -> 0.777; South -> 0.744; North -> 0.621; East -> 0.189
-- Efficiency/Inventory size[0.10, 0.15, 0.05, 0.15, 0.10, 0.30, 0.15]:  South -> 0.787; West -> 0.722; North -> 0.651; East -> 0.182



-- ===============================================================
-- ##### CONCLUSION FOR CURRENT STATE OF WAREHOUSES #####
-- ===============================================================

-- Across three weighting scenarios, East is consistently the strongest performer (lowest closure 
-- suitability, 0.13–0.19) and North sits comfortably in the middle (0.62–0.68), so neither is a 
-- viable closure candidate under any weighting scenario tested. South and West trade the top spot 
-- depending on the weighting scheme — South leads under baseline and efficiency-focused weights (0.82 
-- and 0.79) by leaning on its low relocation cost and poor capacity efficiency, while West leads under 
-- equal weighting (0.78) on the strength of its low utilization and weak raw sales — indicating the 
-- final recommendation between these two should rely on Level 2–4 evidence (product margin, customer 
-- impact, consolidation feasibility) rather than Level 1 alone.










