-- ===============================================================
-- ############## FINAL WEIGHTED DECISION TABLE ##################
-- ===============================================================

-- Create a table so final weighted scores of earlier results can be combined into a single table.
CREATE TABLE warehouse_scores(
	warehouseName VARCHAR(50) PRIMARY KEY,
    level1_score DECIMAL(5,3),
    level2_score DECIMAL(5,3),
    level3_score DECIMAL(5,3),
    level4_score DECIMAL(5,3)
);
TRUNCATE TABLE warehouse_scores; -- Some values changed after the review. 
-- It is safe to keep TRUNCATE it here for filling in with the changed values

INSERT INTO warehouse_scores(warehouseName, level1_score, level2_score, level3_score,level4_score)
VALUES
('West',  0.811, 0.815, 0.477, 0.883),
('South', 0.816, 0.548, 0.762, 0.689),
('North', 0.676, 0.603, 0.681, 0.812),
('East',  0.132, 0.450, 0.209, 0.300);

-- Validation check against multiple insertions
SELECT * FROM warehouse_scores;



SELECT 
	warehouseName, 
    level1_score, 
    level2_score, 
    level3_score,
    level4_score,
    ROUND(
		level1_score*0.30 +
        level2_score*0.30 +
        level3_score*0.30 +
        level4_score*0.10        
    , 3) AS final_composite_score
FROM warehouse_scores
ORDER BY final_composite_score DESC;

-- Results: 
-- For Baseline weights [0.15, 0.35, 0.30, 0.20]                  : West -> 0.727; South -> 0.681; North -> 0.679; East -> 0.300

-- For Equal Weights [0.25, 0.25, 0.25, 0.25]                     : West -> 0.724; South -> 0.704; North -> 0.693; East -> 0.273

-- For Growth-protective [0.10, 0.20, 0.50, 0.20]                 : South -> 0.710; North -> 0.676; West -> 0.659; East -> 0.268

-- For Cost-cutting/operationally driven [0.20, 0.30, 0.10, 0.40] : West -> 0.808; North -> 0.709; South -> 0.679; East -> 0.302

-- Status-quo Conservative [0.30, 0.30, 0.30, 0.10]               : West -> 0.719; South -> 0.707; North -> 0.669; East -> 0.267