-- ===============================================================
-- ################# Level 2: Product Analysis ###################
-- ===============================================================


-- ===============================================================
-- Q1: Which are the top 10% best-selling products by sales volume and value?
WITH product_sales AS(
	SELECT
		p.productCode,
        p.productName,
        p.warehouseCode,
        SUM(od.quantityOrdered) AS total_units_sold,
        ROUND(SUM(od.quantityordered*priceEach), 2) AS total_sales_value
	FROM products p
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY p.productCode, p.productName, p.warehouseCode
),
ranked AS(
	SELECT
		*,
        NTILE(10) OVER (ORDER BY total_sales_value DESC) AS sales_value_tile,
        NTILE(10) OVER (ORDER BY total_units_sold DESC) AS sales_volume_tile
	FROM product_sales
)
SELECT 
	productCode, 
    productName, 
    r.warehouseCode,
    w.warehouseName,
    total_units_sold,
    total_sales_value
FROM ranked r
LEFT JOIN warehouses w ON r.warehouseCode = w.warehouseCode
WHERE sales_value_tile = 1 OR sales_volume_tile =1
ORDER BY total_sales_value DESC; --  LIMIT 11;

-- Result
-- East (b) dominates with 6 of 7 top-selling products — highest concentration of best-sellers
-- In top 10% total sale volume of products (of the total 110 distinct products), East holds 6, North holds 3, 
-- and West holds 2 products. Including top 10% total units sale into consideration, of the 21 products, East 
-- holds 8, North holds 5, West and South holds 4 products each.  
-- 1992 Ferrari 360 Spider red (#1) generates $271K in sales — nearly more than half of 2001 Ferrari Enzo (#2)
-- Top 3 products (all in East) account for $643K combined
-- East warehouse best-sellers generate $1.35M total. It is the best performer.


-- =======================================================================
-- Q2: Which are the bottom 20% slowest-moving products (by sales volume)?

WITH product_sales AS (
	SELECT 
		p.productCode,
        p.productName,
        p.warehouseCode,
        COALESCE(SUM(od.quantityOrdered), 0) AS total_units_sold 
	FROM products p 
    -- LEFT JOIN from products so zero-sale products are included and marked zero by COALESCE
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber
		AND o.status NOT IN ('Cancelled', 'Disputed')
	GROUP BY p.productCode, p.productName, p.warehouseCode
),
ranked AS (
	SELECT 
		*,
		NTILE(5) OVER(ORDER BY total_units_sold ASC) AS volume_tile
	FROM product_sales
)
SELECT 
	productCode, productName, r.warehouseCode, w.warehouseName, total_units_sold
FROM ranked r
LEFT JOIN warehouses w ON w.warehouseCode = r.warehouseCode
WHERE volume_tile = 1 
ORDER BY total_units_sold ASC;

-- Results:
-- East (b) holds 9 of 22 slowest-moving products — highest concentration of dead/slow stock
-- West (c) holds 7 of 22 — significant concentration
-- North (a) holds 3 of 22 — minimal
-- South (d) holds 3 of 22 — minimal
-- 1985 Toyota Supra has 0 units sold — complete dead stock. Located in East warehouse, it should be liquidated.
-- Overall, East dominates slowest-moving products but it also had the highest concentration of best selling product.
-- West had one of the lowest representation in high best-selling products in volume and sales value and 
-- it holds a significant amount of low-selling products.




-- =======================================================================
-- Q3: How many products are "dead stock" (zero or near-zero sales) in the last 6 months?
WITH reference_date AS (
	SELECT MAX(orderDate) AS max_date 
    FROM orders
),
recent_sales AS(
	SELECT 
		p.productCode,
        p.productName,
        p.warehouseCode,
        p.quantityInStock,
        COALESCE(SUM(od.quantityOrdered), 0) AS units_sold_last_6mo
	FROM products p
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber
		AND o.status NOT IN ('Cancelled', 'Disputed')
        AND o.orderDate > (SELECT max_date FROM reference_date) - INTERVAL 6 MONTH
	GROUP BY p.productCode, p.productName, p.warehouseCode, p.quantityInStock
)

SELECT 
	productCode, 
		productName, 
		warehouseCode, 
		quantityInStock, 
        units_sold_last_6mo
FROM recent_sales
WHERE units_sold_last_6mo <= 5 -- treat 0-5 units as near-zero
ORDER BY units_sold_last_6mo ASC, quantityInStock DESC;

-- Result: 
-- Similar to the previous result, the 1985 Toyota Supra unit sold 0 within the last six-month. It is the only dead stock. 
-- Located in East warehouse, it should be liquidated immediately.

-- 7733 1985 Toyota Supra exists in stock. Is this extreme? 
SELECT productName, quantityInStock
FROM products 
ORDER BY quantityInStock DESC; 
-- Not extreme, many products have more than 9000 units in stock. 25 more products have higher number of units. 
-- Therefore, its weight should be smaller.


-- =======================================================================
-- Q4: What is the sales turnover rate (sales velocity) for products in each warehouse?

WITH product_turnover AS(
	SELECT 
		p.warehouseCode,
        p.productCode,
        p.quantityInStock,
        COALESCE(SUM(od.quantityOrdered), 0) AS unit_sold
	FROM products p
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber
		AND o.status NOT IN ('Cancelled', 'Disputed')
	GROUP BY p.warehouseCode, p.productCode, p.quantityInStock
)
SELECT 
	pt.warehouseCode,
    w.warehouseName,
    SUM(unit_sold) AS total_units_sold,
    SUM(quantityInStock) AS total_units_in_stock,
    ROUND(
		SUM(unit_sold) / NULLIF (SUM(quantityInStock), 0)
    , 3) AS turnover_rate
FROM product_turnover pt
JOIN  warehouses w ON pt.warehouseCode = w.warehouseCode
GROUP BY pt.warehouseCode, w.warehouseName
ORDER BY turnover_rate DESC;


-- All warehouses have very low turnover rates. 
-- Turnover rate is the highest in South (0.282), relatively more efficient one; 
-- and it is lower in North (0.187), West (0.184) and East(162) branches.
-- The time range is 2.5 years for Mint Classic data. For these turnover rates,
-- it will approximately take 9 years for South branch, 
-- 13 years for North, 14 years for West and 15 years for East branch to sell all of their stocks.



-- =======================================================================
-- Q5: What is the profit margin per product by warehouse?

SELECT
    p.warehouseCode,
    p.productCode,
    p.productName,
    p.buyPrice,
    p.MSRP,
    ROUND(p.MSRP - p.buyPrice, 2)                              AS list_margin_per_unit,
    ROUND(AVG(od.priceEach - p.buyPrice), 2)                    AS avg_realized_margin_per_unit,
    SUM(od.quantityOrdered)                                     AS units_sold,
    ROUND(SUM((od.priceEach - p.buyPrice) * od.quantityOrdered), 2) AS total_realized_margin
FROM products p
JOIN orderdetails od ON od.productCode = p.productCode
JOIN orders o ON o.orderNumber = od.orderNumber
WHERE o.status NOT IN ('Cancelled', 'Disputed')
GROUP BY p.warehouseCode, p.productCode, p.productName, p.buyPrice, p.MSRP
ORDER BY total_realized_margin DESC;

-- Rolled up to the warehouse level (for feeding into the composite score later):
SELECT
    p.warehouseCode,
    w.warehouseName,
    ROUND(SUM((od.priceEach - p.buyPrice) * od.quantityOrdered), 2) AS total_realized_margin,
    ROUND(AVG(od.priceEach - p.buyPrice), 2)                        AS avg_realized_margin_per_unit
FROM products p
JOIN orderdetails od ON od.productCode = p.productCode
JOIN orders o ON o.orderNumber = od.orderNumber
JOIN warehouses w ON w.warehouseCode =p.warehouseCode
WHERE o.status NOT IN ('Cancelled', 'Disputed')
GROUP BY p.warehouseCode
ORDER BY total_realized_margin DESC;

-- An additional exploration for min.-max. prices
SELECT MIN(priceEach), MAX(priceEach), AVG(priceEach)
FROM orderdetails;
-- Minimum price is $26.55 and maximum is $214.30

SELECT MIN(buyPrice), MAX(buyPrice), AVG(buyPrice), MIN(MSRP), MAX(MSRP)
FROM products;
-- Minimum MSRP is $33.19 and maximum MSRP is $214.30



-- Result: 
-- Total realized margin is highest for 1992 Ferrari 360 Spider. Similarly, 1952 Alpine Renault and 2001 Ferrari 
-- Enzo are other products with higher profit margin. 
-- Average profit margin per unit is $42.66 for East, the highest. Other warehouses have similar averages: 
-- $33.66 for North, $32.35 for West, $32.59 for South 



-- ===============================================================
-- ##### LEVEL 2 COMPOSITE SCORE: PRODUCT ANALYSIS #####
-- ===============================================================

WITH

reference_date AS (
    SELECT MAX(orderDate) AS max_date FROM orders
),

-- Base: every product, with sales totals (0 if never sold) — feeds Q1, Q2
product_sales_all AS (
    SELECT
        p.productCode,
        p.warehouseCode,
        COALESCE(SUM(od.quantityOrdered), 0) AS total_units_sold,
        COALESCE(SUM(od.quantityOrdered * od.priceEach), 0) AS total_sales_value
    FROM products p
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber
                       AND o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY p.productCode, p.warehouseCode
),

-- Q1: count of top-10%-by-value products per warehouse
tiled_by_value AS (
    SELECT
        productCode, warehouseCode,
        NTILE(10) OVER (ORDER BY total_sales_value DESC) AS value_tile
    FROM product_sales_all
),

critical_products AS (
    SELECT warehouseCode, COUNT(*) AS critical_product_count
    FROM tiled_by_value
    WHERE value_tile = 1
    GROUP BY warehouseCode
),

-- Q2: count of bottom-20%-by-volume products per warehouse
tiled_by_volume AS (
    SELECT
        productCode, warehouseCode,
        NTILE(5) OVER (ORDER BY total_units_sold ASC) AS volume_tile
    FROM product_sales_all
),

slow_movers AS (
    SELECT warehouseCode, COUNT(*) AS slow_mover_count
    FROM tiled_by_volume
    WHERE volume_tile = 1
    GROUP BY warehouseCode
),

-- Q3: dead stock as a % of each warehouse's own catalog
recent_sales AS (
    SELECT
        p.productCode,
        p.warehouseCode,
        COALESCE(SUM(od.quantityOrdered), 0) AS units_sold_last_6mo
    FROM products p
    LEFT JOIN orderdetails od ON od.productCode = p.productCode
    LEFT JOIN orders o ON o.orderNumber = od.orderNumber
                       AND o.status NOT IN ('Cancelled', 'Disputed')
                       AND o.orderDate > (SELECT max_date FROM reference_date) - INTERVAL 6 MONTH
    GROUP BY p.productCode, p.warehouseCode
),

dead_stock AS (
    SELECT
        warehouseCode,
        ROUND(
            SUM(CASE WHEN units_sold_last_6mo <= 2 THEN 1 ELSE 0 END) / COUNT(*) * 100
        , 2) AS dead_stock_pct
    FROM recent_sales
    GROUP BY warehouseCode
),

-- Q4: turnover rate per warehouse
turnover AS (
    SELECT
        p.warehouseCode,
        ROUND(
            SUM(psa.total_units_sold) / NULLIF(SUM(p.quantityInStock), 0)
        , 3) AS turnover_rate
    FROM products p
    JOIN product_sales_all psa ON psa.productCode = p.productCode
    GROUP BY p.warehouseCode
),

-- Q5: profit margin per warehouse
margin AS (
    SELECT
        p.warehouseCode,
        ROUND(SUM((od.priceEach - p.buyPrice) * od.quantityOrdered), 2) AS total_realized_margin,
        ROUND(AVG(od.priceEach - p.buyPrice), 2) AS avg_realized_margin_per_unit
    FROM products p
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY p.warehouseCode
),

-- Combine every raw metric into one row per warehouse
combined AS (
    SELECT
        w.warehouseCode,
        COALESCE(cp.critical_product_count, 0) AS critical_product_count,
        COALESCE(sm.slow_mover_count, 0)       AS slow_mover_count,
        ds.dead_stock_pct,
        t.turnover_rate,
        m.total_realized_margin,
        m.avg_realized_margin_per_unit
    FROM (SELECT DISTINCT warehouseCode FROM products WHERE warehouseCode IS NOT NULL) w
    LEFT JOIN critical_products cp ON cp.warehouseCode = w.warehouseCode
    LEFT JOIN slow_movers sm       ON sm.warehouseCode = w.warehouseCode
    JOIN dead_stock ds              ON ds.warehouseCode = w.warehouseCode
    JOIN turnover t                 ON t.warehouseCode = w.warehouseCode
    JOIN margin m                   ON m.warehouseCode = w.warehouseCode
),

-- Normalize 0-1, direction-corrected, so higher values means more suitable to close
normalized AS (
    SELECT
        warehouseCode,

        -- Q1: many critical products -> less suitable -> invert
        ROUND(1 - (critical_product_count - MIN(critical_product_count) OVER())
              / NULLIF(MAX(critical_product_count) OVER() - MIN(critical_product_count) OVER(), 0), 3) AS n_critical_products,

        -- Q2: many slow movers -> more suitable -> no invert
        ROUND((slow_mover_count - MIN(slow_mover_count) OVER())
              / NULLIF(MAX(slow_mover_count) OVER() - MIN(slow_mover_count) OVER(), 0), 3) AS n_slow_movers,

        -- Q3: high dead stock % -> more suitable -> no invert
        ROUND((dead_stock_pct - MIN(dead_stock_pct) OVER())
              / NULLIF(MAX(dead_stock_pct) OVER() - MIN(dead_stock_pct) OVER(), 0), 3) AS n_dead_stock,

        -- Q4: high turnover -> less suitable -> invert
        ROUND(1 - (turnover_rate - MIN(turnover_rate) OVER())
              / NULLIF(MAX(turnover_rate) OVER() - MIN(turnover_rate) OVER(), 0), 3) AS n_turnover,

        -- Q5a: high margin -> less suitable -> invert
        ROUND(1 - (total_realized_margin - MIN(total_realized_margin) OVER())
              / NULLIF(MAX(total_realized_margin) OVER() - MIN(total_realized_margin) OVER(), 0), 3) AS n_total_margin,

        -- Q5b: high avg margin/unit -> less suitable -> invert
        ROUND(1 - (avg_realized_margin_per_unit - MIN(avg_realized_margin_per_unit) OVER())
              / NULLIF(MAX(avg_realized_margin_per_unit) OVER() - MIN(avg_realized_margin_per_unit) OVER(), 0), 3) AS n_avg_margin

    FROM combined 
)

-- Baseline weights: sum to 1.00
SELECT
    n.warehouseCode,
    w.warehouseName,
    n_critical_products,
    n_slow_movers,
    n_dead_stock,
    n_turnover,
    n_total_margin,
    n_avg_margin,
    ROUND(
        n_critical_products * 0.25 +   -- Q1
        n_slow_movers       * 0.15 +   -- Q2
        n_dead_stock        * 0.05 +   -- Q3
        n_turnover          * 0.25 +   -- Q4
        n_total_margin      * 0.20 +   -- Q5a
        n_avg_margin        * 0.10     -- Q5b
    , 3) AS level2_composite_score
FROM normalized n
LEFT JOIN warehouses w ON w.warehouseCode = n.warehouseCode 
ORDER BY level2_composite_score DESC;

-- WEIGHTS SELECTION:
-- Baseline weights [0.25, 0.15, 0.05, 0.25, 0.20, 0.10]: Critical product count gets the largest weight 
-- (0.25) — losing access to top-selling products is the highest-stakes risk in this level, more consequential 
-- than any single volume or margin metric alone. Turnover rate is the same (0.25) as the cleanest single efficiency 
-- signal — a direct ratio of sales velocity, unaffected by warehouse size. Slow mover count (15), and 
-- total margin share the mid-tier (0.20) — real but secondary signals, none individually decisive. Avg margin 
-- per unit gets smaller weight (0.10), since it's a secondary/quality cut on the same underlying data as total 
-- margin, not an independent signal. There was only a single dead stock and the number of its unit in quantity
-- is not extreme. It should be weighted the smallest (0.05).

-- Equal weighting [0.167 × 6]: Removes analyst judgment entirely — tests whether the baseline's emphasis on critical 
-- products is actually driving the ranking, or whether the result holds regardless. Serves as a neutral control case; 
-- agreement with baseline strengthens confidence, disagreement flags the baseline's weighting as consequential.

-- Margin Focused [0.15, 0.10, 0.05, 0.15, 0.30, 0.25]: Concentrates weight on total realized margin (0.30) and avg 
-- margin per unit (0.25), treating profitability as the dominant business signal over raw volume metrics.
-- Rationale: a warehouse can move a lot of product and still be a weak asset if none of it is profitable,
-- this scenario tests which warehouse holds the company's actual earnings, not just its throughput.
-- Critical product count and turnover are reduced to 0.15 each, slow movers stock drop to 0.10,and dead stock drop to 0.05,
-- so margin becomes the clear dominant driver in this run.


-- RESULTS
-- Composite scores: 
-- Baseline weights [0.25, 0.15, 0.05, 0.25, 0.20, 0.10]       :  West -> 0.815; North -> 0.603; South -> 0.548;  East-> 0.450

-- Sensitivity Analysis (Stress Test):
-- For equal weights [0.167, 0.167, 0.167, 0.167, 0.167, 0.167]:  West -> 0.722; North -> 0.519; East -> 0.501; South -> 0.497
-- Margin Focused [0.15, 0.10, 0.05, 0.15, 0.30, 0.25]         :  West -> 0.862; South -> 0.694; North -> 0.685; East -> 0.300

-- ===============================================================
-- ##### CONCLUSION FOR PRODUCT ANALYSIS #####
-- ===============================================================

-- Unlike the near-tie between South and West on Level 1, product-level analysis points clearly to 
-- West as the strongest closure candidate — it leads across all three weighting scenarios (0.815 
-- baseline, 0.722 equal, 0.862 margin-focused), with its lead widening substantially once margin 
-- is emphasized. South's position weakens considerably at Level 2: after nearly tying West on 
-- Level 1, it drops to a clear third under margin-focused weighting (0.548), suggesting South 
-- holds more profitable product margin than its Level 1 profile implied — a real reason for 
-- caution before finalizing South as a co-candidate. North and South stay closely clustered under 
-- baseline and equal weighting. East's suitability score drops sharply under margin-focus 
-- (0.300), indicating East houses disproportionately high-margin products worth protecting. 
-- Combined with Level 1, West is emerging as the more consistent closure candidate across levels, 
-- while South's case now depends more heavily on how Level 3–4 evidence (customer impact, 
-- feasibility) weighs in, and North showed a similar trend to that of South at this level.

