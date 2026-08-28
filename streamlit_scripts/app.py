import streamlit as st

from db import run_query
from queries import QUESTIONS, FINAL_SCORES_QUERY, MONTHLY_SALES_TREND_QUERY, COUNTRY_WAREHOUSE_MAP_QUERY, PRODUCT_LINE_REVENUE_QUERY, CAPACITY_HEADROOM_QUERY, LEVEL4_QUERY
from charts import (
    WAREHOUSE_ORDER,
    format_value,
    make_bullet_chart,
    make_treemap,
    make_simple_bar_chart,
    make_donut_chart,
    make_lollipop_chart,
    make_composite_score_chart,
    make_diverging_bar_chart,
    make_heatmap,
    make_trend_line_chart,
    make_country_warehouse_map,
    make_category_bar_chart
)

# ─────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Warehouse Closure Analysis Framework',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ─────────────────────────────────────────────────────────────
# Page-only styling constants (not needed anywhere else, so they
# stay local to this file rather than living in charts.py)
# ─────────────────────────────────────────────────────────────
NAVY_PRIMARY   = "#14213D"
NAVY_DARK      = "#0B1526"
NAVY_ACCENT    = "#F59E0B"   # unselected level buttons — coral color
NAVY_SELECTED  = "#2F7E8D"   # selected level button — soft mint
GOLD_HIGHLIGHT = "#E9C46A"   # Final Recommendation button — always gold
LIGHT_TEXT     = "#2D3748"

# ─────────────────────────────────────────────────────────────
# Custom CSS — navy sidebar, button-style navigation
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
    <style>
    section[data-testid="stSidebar"] {{
        background-color: {NAVY_PRIMARY};
    }}
    section[data-testid="stSidebar"] * {{
        color: {LIGHT_TEXT} !important;
    }}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {{
        color: white !important;
        font-weight: 700;
    }}

    /* Sidebar nav buttons — default (unselected), orange */
    section[data-testid="stSidebar"] button[kind="secondary"] {{
        background-color: {NAVY_ACCENT};
        color: {NAVY_DARK} !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 4px;
    }}
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background-color: #E08E4C;
        color: {NAVY_DARK} !important;
    }}

    /* Sidebar nav buttons — selected level, lime */
    section[data-testid="stSidebar"] button[kind="primary"] {{
        background-color: {NAVY_SELECTED} !important;
        color: {NAVY_DARK} !important;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        margin-bottom: 4px;
    }}
    section[data-testid="stSidebar"] button[kind="primary"]:hover {{
        background-color: #A8E000;
        color: {NAVY_DARK} !important;
    }}

    /* Final Recommendation button — always the last button in the
       sidebar, styled gold regardless of selection state so it
       reads as a distinct call-to-action, not just another level. */
    .st-key-final_rec_container button {{
        background-color: {GOLD_HIGHLIGHT} !important;
        color: {NAVY_DARK} !important;
        font-weight: 700 !important;
        border: none !important;
    }}
    .st-key-final_rec_container button:hover {{
        background-color: #F0D189 !important;
    }}

    /* Main-panel question buttons */
    div[data-testid="stButton"] button[kind="secondary"] {{
        border-radius: 8px;
    }}
    div[data-testid="stButton"] button[kind="primary"] {{
        background-color: {NAVY_PRIMARY};
        border-radius: 8px;
    }}

    h1 {{ color: {NAVY_PRIMARY}; }}
    div[data-testid="stMetric"] {{
        background-color: #F4F6FA;
        border: 1px solid #DCE2ED;
        border-radius: 10px;
        padding: 12px 16px;
    }}
    h2, h3 {{
        border-bottom: 2px solid {NAVY_PRIMARY};
        padding-bottom: 4px;
    }}

    /* Key Insights box — shown next to each chart */
    .st-key-insights_box, .st-key-insights_box_final {{
        background-color: #F4F6FA;
        border: 1px solid #DCE2ED;
        border-left: 4px solid {NAVY_PRIMARY};
        border-radius: 8px;
        padding: 16px 20px;
    }}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.title("🏭 Warehouse Closure Analysis")
st.caption("A SQL-Based Multi-Criteria Decision Framework")


def render_question(question_label, config):
    st.subheader(question_label)
    df = run_query(config["query"])

    if config["chart_type"] == "multi_metric":
        render_multi_metric(df, config, question_label)
    elif config["chart_type"] == "indicator_grid":
        render_indicator_grid(df, config, question_label)
    else:
        render_single_metric(df, config, question_label)


def render_single_metric(df, config, question_label):
    chart_type = config["chart_type"]

    if chart_type != "table":
        y_col = config["y_col"]
        y_label = config["y_label"]
        fmt = config["fmt"]

        # KPI row
        df_sorted = df.sort_values(y_col, ascending=False)
        top_row = df_sorted.iloc[0]
        bottom_row = df_sorted.iloc[-1]
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric(f"Highest — {top_row['warehouseName']}", format_value(top_row[y_col], fmt))
        kpi2.metric(f"Lowest — {bottom_row['warehouseName']}", format_value(bottom_row[y_col], fmt))
        kpi3.metric("Average", format_value(df[y_col].mean(), fmt))

    col1, col2 = st.columns([1.4, 1])

    with col1:
        if chart_type != "table":
            st.markdown(f"**{y_label} by Warehouse**")

        if chart_type == "bullet":
            st.altair_chart(make_bullet_chart(df, y_col, y_label, fmt),
                            use_container_width=True)
        elif chart_type == "treemap":
            st.plotly_chart(make_treemap(df, y_col, y_label),
                            use_container_width=True)
        elif chart_type == "bar":
            st.altair_chart(
                make_simple_bar_chart(df, "warehouseName", y_col, y_label),
                use_container_width=True)
        elif chart_type == "donut":
            st.plotly_chart(
                make_donut_chart(df, "warehouseName", y_col, y_label),
                use_container_width=True)
        elif chart_type == "lollipop":
            st.altair_chart(
                make_lollipop_chart(df, "warehouseName", y_col, y_label, fmt),
                use_container_width=True)
        elif chart_type == "diverging_bar":
            st.altair_chart(
                make_diverging_bar_chart(df, "warehouseName", y_col, y_label),
                use_container_width=True)
        elif chart_type == "heatmap":
            long_df = df.melt(
                id_vars="warehouseName",
                value_vars=config["value_cols"],
                var_name="indicator",
                value_name="score",
            )
            if "weight_labels" in config:
                long_df["indicator"] = long_df["indicator"].map(
                    config["weight_labels"]).fillna(long_df["indicator"])
            st.altair_chart(
                make_heatmap(long_df, "indicator", "warehouseName", "score",
                             y_label),
                use_container_width=True)
        elif chart_type == "table":
            st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("## 💡Key Insights")
        with st.container(key=f"insights_box_{question_label}"):
            st.markdown(config["conclusion"])


def render_multi_metric(df, config, question_label):
    metrics = config["metrics"]

    # 2x2 grid — one small chart per metric
    for row_start in range(0, len(metrics), 2):
        row_metrics = metrics[row_start:row_start + 2]
        cols = st.columns(len(row_metrics))
        for col, metric in zip(cols, row_metrics):
            with col:
                st.markdown(f"**{metric['label']}**")
                chart_kind = metric.get("chart", "bullet")
                if chart_kind == "bar":
                    chart = make_simple_bar_chart(df, "warehouseName", metric["col"], metric["label"])
                    st.altair_chart(chart, use_container_width=True)
                elif chart_kind == "donut":
                    chart = make_donut_chart(df, "warehouseName", metric["col"], metric["label"])
                    st.plotly_chart(chart, use_container_width=True)
                elif chart_kind == "lollipop":
                    chart = make_lollipop_chart(df, "warehouseName", metric["col"], metric["label"], metric["fmt"])
                    st.altair_chart(chart, use_container_width=True)
                else:
                    chart = make_bullet_chart(df, metric["col"], metric["label"], metric["fmt"])
                    st.altair_chart(chart, use_container_width=True)

    st.markdown("## 💡Key Insights")
    with st.container(key=f"insights_box_{question_label}"):
        st.markdown(config["conclusion"])


def render_indicator_grid(df, config, question_label):
    value_cols = config["value_cols"]
    weight_labels = config.get("weight_labels", {})

    # Grid of one small bar chart per normalized indicator, 3 per row
    for row_start in range(0, len(value_cols), 3):
        row_cols = value_cols[row_start:row_start + 3]
        cols = st.columns(len(row_cols))
        for col, indicator in zip(cols, row_cols):
            with col:
                label = weight_labels.get(indicator, indicator)
                st.markdown(f"**{label}**")
                chart = make_simple_bar_chart(df, "warehouseName", indicator, label)
                st.altair_chart(chart, use_container_width=True)

    st.markdown("**💡 Key Insights**")
    with st.container(key=f"insights_box_{question_label}"):
        st.markdown(config["conclusion"])

# ─────────────────────────────────────────────────────────────
# Sidebar navigation — buttons instead of radio/selectbox
# ─────────────────────────────────────────────────────────────
if "selected_level" not in st.session_state:
    st.session_state.selected_level = "Business Problem"

st.sidebar.title("The Problem")

biz_type = "primary" if st.session_state.selected_level == "Business Problem" else "secondary"
if st.sidebar.button("📋 Business Problem", key="nav_biz", type=biz_type, use_container_width=True):
    st.session_state.selected_level = "Business Problem"
    st.rerun()


st.sidebar.title("Multi-Level Assessment")
LEVEL_BUTTON_LABELS = {
    "Level 1": "📊L1 Current State Assessment",
    "Level 2": "📦L2 Product Analysis",
    "Level 3": "🤝🏼L3 Customer Impact Analysis",
    "Level 4": "🔁L4 Consolidation Feasibility",
}

for lvl in ["Level 1", "Level 2", "Level 3", "Level 4"]:
    btn_type = "primary" if st.session_state.selected_level == lvl else "secondary"
    if st.sidebar.button(LEVEL_BUTTON_LABELS[lvl], key=f"nav_{lvl}", type=btn_type, use_container_width=True):
        st.session_state.selected_level = lvl
        st.rerun()

st.sidebar.title("Decision")
final_type = "primary" if st.session_state.selected_level == "Final Recommendation" else "secondary"
with st.sidebar.container(key="final_rec_container"):
    if st.sidebar.button("🏆 Final Recommendation", key="nav_final", type=final_type, use_container_width=True):
        st.session_state.selected_level = "Final Recommendation"
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("@by Orhan Kaplan")

level = st.session_state.selected_level

# ─────────────────────────────────────────────────────────────
# LEVELS 1–4 — driven by the QUESTIONS registry
# ─────────────────────────────────────────────────────────────
LEVEL_ICONS = {"Level 1": "📊", "Level 2": "📦", "Level 3": "🤝", "Level 4": "🔁"}
LEVEL_TITLES = {
    "Level 1": "Current State Assessment",
    "Level 2": "Product Analysis",
    "Level 3": "Customer Impact",
    "Level 4": "Consolidation Feasibility",
}
# Shown on the "Overview" tab for each level, before the viewer
# drills into individual questions. Edit these to match what each
# level actually covers as you build out Levels 2-4.
LEVEL_OVERVIEWS = {
    "Level 1": "This section assesses each warehouse's current state — capacity utilization and inventory value — to establish the baseline before deeper analysis.",
    "Level 2": "This chart shows total revenue by product line company-wide, before breaking things "
        "down by warehouse. It's the backdrop for the questions that follow — **Q1** and **Q2** "
        "look at which specific products (not just lines) are top performers vs. slow movers per "
        "warehouse, and **Q5** looks at where the actual profit margin sits.",
    "Level 3": "This map shows each country's primary warehouse and flags which ones are served by "
        "only a single warehouse — Switzerland is the only country where the customers most exposed if that warehouse closes. "
        "**Q3** covers this same regional-dependency question in table form with the "
        "underlying numbers; **Q1** and **Q2** look at customer concentration and spending more broadly.",
    "Level 4": f"This chart shows how much spare capacity the other warehouses have to absorb "
        f"**West**'s inventory if it were closed. The **Closure Feasibility "
        f"Indicators** tab breaks down the raw metrics behind this decision, and **Level 4 Result** "
        f"shows the full weighted composite score.",
}

if level == "Business Problem":
    st.header("📋 Business Problem")
    st.markdown("""
    **Mint Classics operates four warehouses with uneven utilization — from 50% to 75% of capacity.** Underused space still carries full fixed costs (lease, staffing, utilities) without proportional sales return.

    **The question:** Can one warehouse close without materially harming sales, service levels, or high-margin product availability — and if so, which one?

    **Why this isn't a single-query answer:**

    ◆ A warehouse can look weak on raw sales volume yet hold the highest-margin products

    ◆ It may serve a geographically isolated customer base with no easy fallback

    ◆ It could already be running near capacity, making closure infeasible regardless of sales

    Each of these would turn a volume-based decision into a costly mistake. This project systematically rules each risk in or out with data — rather than closing a warehouse on the most visible metric alone.
    """)

elif level in QUESTIONS:
    st.header(f"{LEVEL_ICONS[level]} {level}: {LEVEL_TITLES[level]}")

    if QUESTIONS[level]:
        question_keys = list(QUESTIONS[level].keys())
        state_key = f"selected_question_{level}"
        if state_key not in st.session_state:
            st.session_state[state_key] = "Overview"
            st.rerun()

        nav_options = ["Overview"] + question_keys
        q_cols = st.columns(len(nav_options))
        for i, q_label in enumerate(nav_options):
            q_type = "primary" if st.session_state[state_key] == q_label else "secondary"
            if q_cols[i].button(q_label, key=f"qbtn_{level}_{q_label}", type=q_type, use_container_width=True):
                st.session_state[state_key] = q_label
                st.rerun()

        st.markdown("---")
        selected_question = st.session_state[state_key]

        if selected_question == "Overview":
            st.markdown(LEVEL_OVERVIEWS.get(level, ""))
            st.markdown(
                "Use the buttons above to individually explore each question in this level.")

            if level == "Level 1":
                trend_df = run_query(MONTHLY_SALES_TREND_QUERY)
                st.markdown("**📈 Monthly Sales Trend by Warehouse**")
                st.altair_chart(
                    make_trend_line_chart(trend_df, "order_month",
                                          "monthly_sales_value",
                                          "Monthly Sales Value ($)"),
                    use_container_width=True)
                st.markdown("""
                - Warehouse sales show a strong seasonal pattern rather than a steady trend — 
                volume stays fairly flat for most of the year, then spikes sharply each 
                November before dropping back down. \n
                - **East** consistently leads in raw 
                sales volume and swings the hardest during the seasonal peak, while 
                **North**, **South**, and **West** track closer together for most of the year.
                - This chart shows sales volume alone, though — it doesn't capture other factors. \n 
                - A warehouse that spikes highest isn't automatically the 
                one to keep, and one that stays flat isn't automatically a closure 
                candidate — that's exactly what the deeper questions in this section, 
                and the levels that follow, are for: **A data-driven multi-criteria decision making**
                """)
            if level == "Level 2":
                pl_df = run_query(PRODUCT_LINE_REVENUE_QUERY)
                st.markdown("**📦 Revenue by Product Line (Company-Wide)**")
                st.altair_chart(
                    make_category_bar_chart(pl_df, "productLine",
                                            "total_sales_value",
                                            "Total Sales Value ($)"),
                    use_container_width=True)
            if level == "Level 3":
                map_df = run_query(COUNTRY_WAREHOUSE_MAP_QUERY)
                st.markdown("**🌍 Warehouse Coverage by Country**")
                st.plotly_chart(
                    make_country_warehouse_map(map_df, "country",
                                               "primary_warehouse",
                                               "dependency_status"),
                    use_container_width=True)
            if level == "Level 4":
                candidate_df = run_query(LEVEL4_QUERY)
                top_candidate_name = candidate_df.iloc[0]["warehouseName"]

                headroom_df = run_query(CAPACITY_HEADROOM_QUERY)
                headroom_df = headroom_df[
                    headroom_df["warehouseName"] != top_candidate_name]

                st.markdown(
                    f"**📦 Available Capacity Headroom (Excluding {top_candidate_name})**")
                st.altair_chart(
                    make_simple_bar_chart(headroom_df, "warehouseName",
                                          "available_headroom_pct",
                                          "Available Headroom (%)"),
                    use_container_width=True)
                st.markdown(
                    f"Shows how much spare capacity the remaining warehouses have to absorb "
                    f"**{top_candidate_name}**'s inventory if it were closed."
                )

        else:
            config = QUESTIONS[level][selected_question]
            render_question(selected_question, config)
    else:
        st.info(f"No questions wired up yet for {level}. Add entries to the QUESTIONS dict in queries.py following the Level 1 pattern.")

# ─────────────────────────────────────────────────────────────
# LEVEL 5 — Final weighted recommendation with interactive sliders
# ─────────────────────────────────────────────────────────────
elif level == "Final Recommendation":
    st.header("🏆 Final Weighted Recommendation")
    st.caption("Adjust the level weights below to see how the closure ranking responds.")

    scores_df = run_query(FINAL_SCORES_QUERY)

    st.markdown("##### Level Weights")
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        weight_l1 = st.slider("Level 1", 0.0, 1.0, 0.15, 0.05)
    with w2:
        weight_l2 = st.slider("Level 2", 0.0, 1.0, 0.35, 0.05)
    with w3:
        weight_l3 = st.slider("Level 3", 0.0, 1.0, 0.30, 0.05)
    with w4:
        weight_l4 = st.slider("Level 4", 0.0, 1.0, 0.20, 0.05)

    total_weight = weight_l1 + weight_l2 + weight_l3 + weight_l4
    if abs(total_weight - 1.0) > 0.001:
        st.warning(f"Weights currently sum to {total_weight:.2f} — normalizing to 1.0 for the score below.")

    scores_df['final_score'] = (
        scores_df['level1_score'] * weight_l1 +
        scores_df['level2_score'] * weight_l2 +
        scores_df['level3_score'] * weight_l3 +
        scores_df['level4_score'] * weight_l4
    ) / total_weight

    ranked_df = scores_df.sort_values('final_score', ascending=False).reset_index(drop=True)

    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.markdown("**Composite Score by Warehouse**")
        st.altair_chart(make_composite_score_chart(ranked_df), use_container_width=True)

    with col2:
        st.markdown("## 💡Key Insights")
        top_candidate = ranked_df.iloc[0]
        bottom_candidate = ranked_df.iloc[-1]
        conclusion_lines = [
            f"- **Note:** For alternative weighting options and the justification for the weights (for this and individual levels), read 'results.md' file on https://github.com/nalpako2027/warehouse-closure-sql-analysis.git",
            f"- Under these weights, **{top_candidate['warehouseName']}** ranks highest as the closure candidate (score: {top_candidate['final_score']:.3f}). ✅🔻",
            f"- 🏆 **{bottom_candidate['warehouseName']}** ranks lowest under this weighting, reinforcing it as the warehouse to protect.",

        ]
        default_conclusion = "\n".join(conclusion_lines)
        with st.container(key="insights_box_final"):
            st.markdown(default_conclusion)