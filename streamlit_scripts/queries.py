# SQL and question metadata for the Warehouse Closure Analysis app.
PRODUCT_LINE_REVENUE_QUERY = """
    SELECT
        p.productLine,
        ROUND(SUM(od.quantityOrdered * od.priceEach), 2) AS total_sales_value
    FROM products p
    JOIN orderdetails od ON od.productCode = p.productCode
    JOIN orders o ON o.orderNumber = od.orderNumber
    WHERE o.status NOT IN ('Cancelled', 'Disputed')
    GROUP BY p.productLine
    ORDER BY total_sales_value DESC;
"""

COUNTRY_WAREHOUSE_MAP_QUERY = """
    WITH country_warehouse_spend AS (
        SELECT
            c.country,
            p.warehouseCode,
            w.warehouseName,
            SUM(od.quantityOrdered * od.priceEach) AS total_spent
        FROM customers c
        JOIN orders o ON o.customerNumber = c.customerNumber
        JOIN orderdetails od ON od.orderNumber = o.orderNumber
        JOIN products p ON p.productCode = od.productCode
        JOIN warehouses w ON w.warehouseCode = p.warehouseCode
        WHERE o.status NOT IN ('Cancelled', 'Disputed')
        GROUP BY c.country, p.warehouseCode, w.warehouseName
    ),
    warehouse_count AS (
        SELECT country, COUNT(DISTINCT warehouseCode) AS warehouse_count
        FROM country_warehouse_spend
        GROUP BY country
    ),
    primary_warehouse AS (
        SELECT
            country, warehouseName, total_spent,
            ROW_NUMBER() OVER (PARTITION BY country ORDER BY total_spent DESC) AS rn
        FROM country_warehouse_spend
    )
    SELECT
        pw.country,
        pw.warehouseName AS primary_warehouse,
        wc.warehouse_count,
        CASE WHEN wc.warehouse_count = 1 THEN 'Single-Warehouse' ELSE 'Multi-Warehouse' END AS dependency_status
    FROM primary_warehouse pw
    JOIN warehouse_count wc ON wc.country = pw.country
    WHERE pw.rn = 1
    ORDER BY pw.country;
"""

CAPACITY_HEADROOM_QUERY = """
    SELECT
        warehouseName,
        warehousePctCap,
        ROUND(100 - warehousePctCap, 1) AS available_headroom_pct
    FROM warehouses
    WHERE warehouseCode IS NOT NULL
    ORDER BY available_headroom_pct DESC;
"""

LEVEL4_QUERY = """
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
                ROUND(1 - (total_sales_value - MIN(total_sales_value) OVER())
                      / NULLIF(MAX(total_sales_value) OVER() - MIN(total_sales_value) OVER(), 0), 3) AS n_sales,
                ROUND(1 - (total_inventory_value - MIN(total_inventory_value) OVER())
                      / NULLIF(MAX(total_inventory_value) OVER() - MIN(total_inventory_value) OVER(), 0), 3) AS n_inventory,
                ROUND(1 - (distinct_products - MIN(distinct_products) OVER())
                      / NULLIF(MAX(distinct_products) OVER() - MIN(distinct_products) OVER(), 0), 3) AS n_products,
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
"""


LEVEL4_RAW_QUERY = """
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
        )

    SELECT
        s.warehouseCode,
        s.warehouseName,
        s.total_sales_value,
        i.total_inventory_value,
        pc.distinct_products,
        t.turnover_rate
    FROM sales s
    JOIN inventory i ON i.warehouseCode = s.warehouseCode
    JOIN products_count pc ON pc.warehouseCode = s.warehouseCode
    JOIN turnover t ON t.warehouseCode = s.warehouseCode
    ORDER BY s.warehouseName;
"""

#########################################################
###################### ALL LEVELS #######################
#########################################################


QUESTIONS = {
###################### LEVEL 1 #########################
    "Level 1": {
        "Q1: Capacity Utilization": {
            "query": """
                SELECT
                    warehouseName,
                    CAST(REPLACE(warehousePctCap, '%', '') AS SIGNED) as warehousePctCap
                FROM warehouses
                WHERE warehouseCode IS NOT NULL
                ORDER BY warehousePctCap DESC;
            """,
            "y_col": "warehousePctCap",
            "y_label": "Capacity Utilization (%)",
            "fmt": "%",
            "chart_type": "lollipop",
            "conclusion": (
                "#### - There are 4 warehouses; three use 67%–75% of storage capacity.\n"
                "#### - **West** uses only 50% of capacity — the clear outlier\n"
                "#### - West has the greatest amount of unused capacity of any warehouse\n"
            ),
        },
        "Q2: Inventory Value": {
            "query": """
                SELECT w.warehouseCode, w.warehouseName,
                       SUM(quantityInStock*buyPrice) AS total_inventory_value
                FROM warehouses w
                JOIN products p ON w.warehouseCode = p.warehouseCode
                GROUP BY w.warehouseCode, w.warehouseName
                ORDER BY total_inventory_value DESC;
            """,
            "y_col": "total_inventory_value",
            "y_label": "Total Inventory Value ($)",
            "fmt": "$",
            "chart_type": "treemap",
            "conclusion": (
                "#### - Total inventory value is the lowest in the South branch. Warehouse West is the second lowest.\n"
                "#### - The East branch holds the greatest financial value ($14.1M). It would cost the most logistical and financial impact if closed.\n"
                "#### - The lowest relocation cost would occur if South (\$4.1M) or West(\$5.7) was relocated.\n"
            ),
        },
        "Q3: Product Diversity": {
            "query": """
                SELECT warehouseName, COUNT(DISTINCT p.productCode) AS distinct_products
                FROM products p
                JOIN warehouses w ON w.warehouseCode = p.warehouseCode
                GROUP BY warehouseName
                ORDER BY distinct_products DESC;
            """,
            "y_col": "distinct_products",
            "y_label": "Distinct Products",
            "fmt": "",
            "chart_type": "bar",
            "conclusion": (
                "#### - Warehouses South (23), West (24) and North (25) almost have the same number of distinct products.\n"
                "#### - They have considerably lower distinct products than the East branch (38).\n"
            ),
        },
        "Q4: Sales Performance": {
            "query": """
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
                    AND o.status IN ('Shipped', 'Resolved') 
                GROUP BY 
                    w.warehouseCode, w.warehouseName
                ORDER BY total_sales_value DESC;
            """,
            "chart_type": "multi_metric",
            "metrics": [
                {"col": "total_unit_sold", "label": "Total Units Sold",
                 "fmt": "", "chart": "bar"},
                {"col": "total_sales_value", "label": "Total Sales Value",
                 "fmt": "$", "chart": "donut"},
                {"col": "avg_order_value", "label": "Avg Order Value",
                 "fmt": "$", "chart": "lollipop"},
                {"col": "unique_products_sold", "label": "Unique Products Sold",
                 "fmt": "", "chart": "bar"},
            ],
            "conclusion": (
                "- East is the undisputed sales leader, the revenue engine.\n"
                "- It dominates across every single metric: the highest order volume (101), the highest total unit sales (16,595), and the broadest product assortment sold (37 unique products).\n"
                "- North and South form a competitive middle tier.\n"
                "- North generates the second-highest revenue and unit sales, while South has slightly more orders (71 vs. 60) and trails closely in average order value (\$2,893 vs. \$2,977). Both are stable performers but not exceptional.\n"
                "- West has the weakest fundamentals. Despite having the second-highest number of orders (90), it generates the lowest total revenue and the lowest average order value (\$2,751). This indicates a high volume of small, low-value transactions, which is a classic sign of low-margin.\n"
            ),
        },
        "Q5: Capacity Efficiency": {
            "query": """
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
    """,
            "y_col": "sales_per_pct_capacity",
            "y_label": "Sales per % of Capacity Utilization",
            "fmt": "",
            "chart_type": "bar",
            "conclusion": (
                "Note: The values are total sales revenue for every percentage point of the utilized capacity of the warehouse.\n"
                "- West is the third in this metric. Its capacity efficiency in terms of revenue is better than South and North.\n"
                "- South has the lowest sales_per_pct_capacity (\$25,021.93). So there is an efficiency issue.\n"
                "- The sales per % of capacity is the highest for East. East is the strongest warehouse in efficiency.\n"
                "- North has the second lowest capacity efficiency, very close to South. However, considering its total sales revenue ($1.02) was greater that of South (0.88M) in the last year, South is the least efficient warehouse according to this metric. \n"
            ),
        },
        "Q6: Growth Percentage": {
            "query": """
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
    """,
            "y_col": "growth_percentage",
            "y_label": "Growth (%)",
            "fmt": "%",
            "chart_type": "diverging_bar",
            "conclusion": (
                "- The East branch has the lowest growth percentage (16.65%), while the West branch has the highest (31.70%). However, the East branch has the highest year-over-year increase in total sales, with sales increasing by approximately \$257K. This difference is largely related to the East branch's much larger sales base. Its recent-year sales are approximately $1.54M, substantially higher than the other branches.\n"
                "- The West branch shows the strongest relative growth, increasing its sales by 31.70%, despite having one of the lowest total sales volumes.\n"
                "- The North branch's 34.84% growth rate is relatively strong, but its sales growth appears more modest when considered alongside its overall sales volume.\n"
                "- Overall, all four branches experienced positive year-over-year sales growth, so none currently shows an absolute decline in sales.\n"
                "- The East branch's combination of high sales volume and comparatively lower growth suggests a more mature sales base, whereas the West branch shows stronger relative expansion from a smaller base.\n"
            ),
        },
        "Level 1 Result": {
            "query": """
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
        """,
            "y_col": "level1_composite_score",
            "value_cols": [
                "n_utilization",
                "n_inventory_value",
                "n_product_diversity",
                "n_sales_value",
                "n_avg_order_value",
                "n_capacity_efficiency",
                "n_growth"
            ],
            "weight_labels": {
                "n_utilization": "Utilization (10%)",
                "n_inventory_value": "Inventory (20%)",
                "n_product_diversity": "Diversity (10%)",
                "n_sales_value": "Sales (25%)",
                "n_avg_order_value": "Avg Order (10%)",
                "n_capacity_efficiency": "Capacity Eff. (15%)",
                "n_growth": "Growth (10%)"
            },
            "y_label": "Level 1 Composite Score",
            "fmt": " ",
            "chart_type": "heatmap",
            "conclusion": (
                "Note: The higher normalized scores (closest to 1) means a candidate with higher probability for closure.\n"
                "- Across three weighting scenarios, East is consistently the strongest performer (lowest closure suitability, 0.13–0.19) and North sits comfortably in the middle (0.62–0.68), so neither is a viable closure candidate under any weighting scenario tested.\n"
                "- South and West trade the top spot depending on the weighting scheme — South leads under baseline and efficiency-focused weights (0.82 and 0.79) by leaning on its low relocation cost and poor capacity efficiency, while West leads under equal weighting (0.78) on the strength of its low utilization and weak raw sales — indicating the final recommendation between these two should rely on Level 2–4 evidence (product margin, customer impact, consolidation feasibility) rather than Level 1 alone.\n"
            ),
        },
    },

###################### LEVEL 2 #########################


    "Level 2": {
        "Q1: Best-Selling/Critical Products": {
            "query": """
            WITH product_sales AS (
                SELECT
                    p.warehouseCode,
                    p.productCode,
                    p.productName,
                    p.productLine,
                    SUM(od.quantityOrdered) AS total_units_sold,
                    ROUND(SUM(od.quantityOrdered * od.priceEach), 2) AS total_sales_value
                FROM products p
                JOIN orderdetails od ON p.productCode = od.productCode
                JOIN orders o ON od.orderNumber = o.orderNumber
                WHERE o.status IN ('Shipped', 'Resolved')
                GROUP BY p.productCode, p.productName, p.productLine
            ),
            ranked AS (
                SELECT
                    *,
                    PERCENT_RANK() OVER (ORDER BY total_sales_value DESC) AS pct_rank
                FROM product_sales
            )
            SELECT
                warehouseName,
                productName,
                productLine,
                total_units_sold,
                total_sales_value
            FROM ranked r
            JOIN warehouses w ON w.warehouseCode = r.warehouseCode
            WHERE pct_rank <= 0.10
            ORDER BY total_sales_value DESC;
        """,
        "chart_type": "table",
        "conclusion": "- East (b) dominates with 6 of 7 top-selling products — highest concentration of best-sellers. \n"
            "- In top 10% total sale volume of products (of the total 110 distinct products), East holds 6, North holds 3, and West holds 2 products. Including top 10% total units sale into consideration, of the 21 products, East holds 8, North holds 5, West and South holds 4 products each.\n"
            "- 1992 Ferrari 360 Spider red (#1) generates \$271K in sales — nearly more than half of 2001 Ferrari Enzo (#2)\n"
            "- Top 3 products (all in East) account for \$643K combined. East warehouse best-sellers generate \$1.35M total. It is the best performer.\n",
        },
        "Q2: Slow-Moving Products": {
            "query": """
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
        """,
            "chart_type": "table",
            "conclusion": (
                "- East (b) holds 9 of 22 slowest-moving products — highest concentration of slow stock.\n"
                "- West (c) holds 7 of 22 — significant concentration.\n"
                "- North (a) holds 3 of 22 — minimal.\n"
                "- South (d) holds 3 of 22 — minimal.\n"
                "- 1985 Toyota Supra has 0 units sold — complete dead stock. Located in East warehouse, it should be liquidated.\n"
                "- Overall, East dominates slowest-moving products but it also had the highest concentration of best selling product.\n"
                "- West had one of the lowest representation in high best-selling products in volume and sales value and it holds a significant amount of low-selling products.\n"
            ),
        },
        "Q3: Dead Stocks": {
            "query": """
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
        """,
            "chart_type": "table",
            "conclusion": (
                "- Similar to the previous result, the 1985 Toyota Supra unit sold 0 within the last six-month. It is the only dead stock.\n"
                "- Located in East warehouse, it should be liquidated immediately.\n"
                "- A further exploration showed that 25 more products have higher number of units; thus, not an extreme outlier.\n"
            ),
        },
        "Q4: Turnover Rate": {
            "query": """
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
            """,
            "y_col": "turnover_rate",
            "y_label": "Turnover Rate",
            "fmt": " ",
            "chart_type": "bullet",
            "conclusion": (
                "- All warehouses have very low turnover rates.\n"
                "- Turnover rate is the highest in South (0.282), relatively more efficient one; and it is lower in North (0.187), West (0.184) and East(0.162) branches.\n"
                "- The time range is 2.5 years for Mint Classic data. For these turnover rates, it will approximately take 9 years for South branch, 13 years for North, 14 years for West and 15 years for East branch to sell all of their stocks.\n"
            ),
        },
        "Q5: Product Profit Margin": {
            "query": """
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
            """,
            "chart_type": "table",
            "conclusion": (
                "- *For reference:* Minimum price is \$26.55 and maximum is \$214.3 and minimum MSRP is \$33.19 and maximum MSRP is \$214.30.\n"
                "- Total realized margin is highest for 1992 Ferrari 360 Spider. Similarly, 1952 Alpine Renault and 2001 Ferrari Enzo are other products with higher profit margin.\n"
                "- Average profit margin per unit is \$42.66 for East, the highest. Other warehouses have similar averages: \$33.66 for North, \$32.35 for West, \$32.59 for South.\n"
            ),
        },
        "Level 2 Result": {
            "query": """
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
            """,
            "value_cols": [
                "n_critical_products",
                "n_slow_movers",
                "n_dead_stock",
                "n_turnover",
                "n_total_margin",
                "n_avg_margin",
            ],
            "weight_labels": {
                "n_critical_products": "Crtcl Products(25%)",
                "n_slow_movers": "Slow Movers (15%)",
                "n_dead_stock": "Dead Stock (5%)",
                "n_turnover": "Turnover (25%)",
                "n_total_margin": "Total Margin (20%)",
                "n_avg_margin": "AvgMarg/Unt (10%)",
            },
            "y_col": "level2_composite_score",
            "y_label": "Level 2 Composite Score",
            "fmt": "",
            "chart_type": "heatmap",
            "conclusion": (
                "- Unlike the near-tie between South and West on Level 1, product-level analysis points clearly to West as the strongest closure candidate — it leads across all three weighting scenarios (0.815 baseline, 0.722 equal, 0.862 margin-focused), with its lead widening substantially once margin is emphasized.\n"
                "- South's position weakens considerably at Level 2: after nearly tying West on Level 1, it drops to a clear third under margin-focused weighting (0.548), suggesting South holds more profitable product margin than its Level 1 profile implied — a real reason for caution before finalizing South as a co-candidate.\n"
                "- North and South stay closely clustered under baseline and equal weighting.\n"
                "- East's suitability score drops sharply under margin-focus (0.300), indicating East houses disproportionately high-margin products worth protecting.\n"
                "- Combined with Level 1, West is emerging as the more consistent closure candidate across levels, while South's case now depends more heavily on how Level 3–4 evidence (customer impact, feasibility) weighs in, and North showed a similar trend to that of South at this level.\n"
            ),
        },

    },


###################### LEVEL 3 #########################
    "Level 3": {
        "Q1: Customer Total Spending": {
            "query": """
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
        """,
            "chart_type": "table",
            "conclusion": (
                "- In North branch, one customer (La Rochelle Gifts) has a large total spending (\$81.559) relative to other customers.\n"
                "- In the East branch, two customers with very large purchases (\$217.758 and \$163.060) could be affected. There are more customers with large sales volumes in this branch relative to others.\n"
                "- In the West branch, one customer with large volume (\$102.628) could be affected.\n"
                "- In the South branch, two customers (\$212.417 and \$102.728) could be affected from the closure of its warehouse.\n"
                "- In summary, the East Branch has more customers with large volume of sales that could cost the company the most. The West branch have customers that comparatively have lower total purchases.\n"
            ),
        },
        "Q2: Customer Spending": {
            "query": """
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
        """,

            "chart_type": "table",
            "conclusion": (
                "- Only 12 customers are exclusively served by a single warehouse.\n"
                "- Their collective purchasing volume is generally insignificant (less than 10%) relative to overall sales.\n"
                "- In general, the impact of closing a branch on dependent customers and their sales would be small.\n"
            ),
        },
        "Q3: Regional Dependency": {
            "query": """
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
        """,

            "chart_type": "table",
            "conclusion": (
                "- Only Switzerland depends on a single warehouse, which is the b (East) branch.\n"
                "- The East branch is already the least likely candidate based on previous anlayses.\n"
            ),
        },
        "Q4: Order Fulfillment": {
            "query": """
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
            """,
            "y_col": "avg_fulfillment_days",
            "y_label": "Average Fulfillment Days",
            "fmt": "",
            "chart_type": "lollipop",
            "conclusion": (
                "- Average shipment speed is satisfactory in all branches.\n"
                "- The average fulfillment time is 3.87 days for the South, 3.83 days for the North, 3.79 days for the East and 3.55 days for the West.\n"
                "- Customers are the most satisfied with the fast shipping in the West branch and relatively the least satisfied in the South branch. However, they are very close.\n"
                "- The distinctively long shipment days experienced by some customers could be analysed in terms of employee efficiency, but this is beyond the scope of the objectives of this level.\n"
                "- Excluded cases are quite low, they are unlikely to change the decision based on available cases.\n"
            ),
        },
        "Q5: Problematic Orders": {
            "query": """
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
            """,
            "y_col": "pct_problem_order",
            "y_label": "Problematic Orders (%)",
            "fmt": "%",
            "chart_type": "lollipop",
            "conclusion": (
                "- All warehouses have acceptable and similar problematic orders rate, ranging from 3.83% to 5.17%.\n"
                "- The East branch has the least and the North has the highest rate of problematic orders, but differences are low related to order accuracy. They are similar to the baseline problem rate. No significant deviation/outlier.\n"
            ),
        },
        "Level 3 Result": {
            "query": """
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
            """,
            "value_cols": [
                "n_concentration",
                "n_exclusive_spend",
                "n_unique_regions",
                "n_fulfillment",
                "n_problem_rate",
            ],
            "weight_labels": {
                "n_concentration": "Cust. Concentration(15%)",
                "n_exclusive_spend": "Exclusive Spend(15%)",
                "n_unique_regions": "Unique Regions(15%)",
                "n_fulfillment": "Fulfillment Risk(30%)",
                "n_problem_rate": "Problematic Orders(25%)",
            },
            "y_col": "level3_composite_score",
            "y_label": "Level 3 Composite Score by Warehouse",
            "fmt": "",
            "chart_type": "heatmap",
            "conclusion": (
                "- Level 3 analysis tells a very different story from Levels 1–2: South and North are the top closure candidates on customer-impact grounds — consistently in the top two across all four weighting scenarios (South 0.75–0.81, North 0.68–0.83), while West and East are both low-suitability here, with East the clear standout as the warehouse customers most depend on (0.17–0.29 across every scenario).\n"
                "- This is a meaningful pivot: West, which looked like the strongest closure candidate on Level 1 and Level 2 evidence, now shows real customer-impact risk (0.43–0.61) likely reflecting a concentrated or region-exclusive customer base uncovered in Q1–Q3 that its weaker sales/margin numbers alone didn't capture.\n"
                "- North and South's ranking order swaps depending on the scenario (North edges ahead under equal, geographic, and service weighting; South leads only under baseline), but the gap between them stays narrow throughout, so they are comparably low-risk from a customer standpoint rather than a definitive choice.\n"
                "- The Key Takeaway: West's Level 1–2 case for closure now needs to be weighed against a real customer-retention risk that didn't show up until this level, while East is reinforced as the warehouse to protect across every dimension analyzed so far.\n"
            ),
        },
    },

###################### LEVEL 4 #########################
    "Level 4": {
        "Closure Feasibility Indicators": {
            "query": LEVEL4_RAW_QUERY,
            "chart_type": "multi_metric",
            "metrics": [
                {"col": "total_sales_value", "label": "Total Sales Value",
                 "fmt": "$", "chart": "bar"},
                {"col": "total_inventory_value", "label": "Total Inventory Value",
                 "fmt": "$", "chart": "donut"},
                {"col": "distinct_products", "label": "Distinct Products",
                 "fmt": "", "chart": "bar"},
                {"col": "turnover_rate", "label": "Turnover Rate",
                 "fmt": "", "chart": "lollipop"},
            ],
            "conclusion": (
                "- **Sales Value:** East dominates with ~\$3.8M in sales, more than double any other warehouse — North, South, and West cluster closely together between \$1.75M–\$2.0M.\n"
                "- **Inventory Value:** East also holds the largest share of inventory value (46%), followed by North (21.8%); South carries the least (13.4%), which matters for relocation cost if it were ever considered for closure.\n"
                "- **Distinct Products:** East again leads with the widest assortment (38 products), while North, South, and West are all fairly similar (23–25) — East's breadth reinforces its position as the least suitable closure candidate.\n"
                "- **Turnover Rate:** South has the highest turnover (0.011), meaning its inventory moves fastest relative to stock on hand; East, despite its size, has the lowest turnover (0.006) — high volume but comparatively slower-moving inventory.\n"
            ),
        },
        "Level 4 Result": {
            "query": LEVEL4_QUERY,
            "value_cols": [
                "n_sales",
                "n_inventory",
                "n_products",
                "n_turnover",
            ],
            "weight_labels": {
                "n_sales": "Sales Value (15%)",
                "n_inventory": "Inventory Value (40%)",
                "n_products": "Product Count (30%)",
                "n_turnover": "Turnover Rate (15%)",
            },
            "y_col": "level4_composite_score",
            "y_label": "Level 4 Composite Score",
            "fmt": "",
            "chart_type": "heatmap",
            "conclusion": (
                "- West is the clearest and most consistent closure candidate at Level 4, scoring highest across all three weighting scenarios (0.878–0.883) with almost no variation — a strong signal that West's feasibility case doesn't depend on how the metrics are weighted.\n"
                "- East is consistently the strongest performer and least suitable to close (0.15–0.30), reinforcing its protected status from Levels 1, 2, and 3.\n"
                "- South and North swap order depending on the scenario — North edges ahead under baseline and equal weighting, but South overtakes it under the relocation-burden focus (0.845 vs. 0.802), suggesting South is comparatively easier to physically close (lower inventory value/product count) even though it isn't the weakest overall performer.\n"
                "- This is West's fourth consecutive level as the top or near-top closure candidate (alongside its strong showing in Levels 1 and 2), making it the most robust candidate heading into the final Level 5 recommendation — the remaining open question is whether Level 3's customer-impact risk for West is significant enough to override this consistency.\n"
            ),
        },
    },
}

# "Level 1": {
#     "Q1: Capacity Utilization": {
#         "query": """
#             SELECT warehouseName FROM warehouses;
#         """,
#         "y_col": "warehousePctCap",
#         "y_label": "Capacity Utilization (%)",
#         "fmt": "%",
#         "chart_type": "lollipop",
#         "conclusion": (
#             "here"
#         ),
#     },

# Monthly sales trend per warehouse, across the full order history —
# shown on the Level 1 Overview tab.
MONTHLY_SALES_TREND_QUERY = """
    SELECT
        w.warehouseName,
        DATE_FORMAT(o.orderDate, '%Y-%m-01') AS order_month,
        SUM(od.quantityOrdered * od.priceEach) AS monthly_sales_value
    FROM warehouses w
    JOIN products p ON w.warehouseCode = p.warehouseCode
    JOIN orderdetails od ON p.productCode = od.productCode
    JOIN orders o ON od.orderNumber = o.orderNumber
    WHERE o.status IN ('Shipped', 'Resolved')
    GROUP BY w.warehouseName, order_month
    ORDER BY order_month, w.warehouseName;
"""



# Level 5 pulls from a pre-computed scores table rather than the
# QUESTIONS registry, since it's a composite across all levels.
FINAL_SCORES_QUERY = "SELECT * FROM warehouse_scores;"
