# To run the app, run this on terminal: /opt/anaconda3/bin/streamlit run /Users/orhankaplan/PROJECTS/Github_Projects/Mint_Classic_SQL/app.py
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import mysql.connector as mconn

# ─────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Warehouse Closure Analysis Framework',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ─────────────────────────────────────────────────────────────
# Global color palette
# One dictionary as the single source of truth for warehouse
# colors — every chart in the app pulls from this so a given
# warehouse is always the same color everywhere.
# ─────────────────────────────────────────────────────────────
WAREHOUSE_COLORS = {
    "North": "#264653",   # dark slate teal
    "South": "#2A9D8F",   # teal
    "East":  "#E9C46A",   # gold
    "West":  "#E76F51",   # burnt orange
}
WAREHOUSE_ORDER = list(WAREHOUSE_COLORS.keys())

NAVY_PRIMARY   = "#14213D"
NAVY_DARK      = "#0B1526"
NAVY_ACCENT    = "#F4A261"   # unselected level buttons — orange
NAVY_SELECTED  = "#BFFF00"   # selected level button — lime
GOLD_HIGHLIGHT = "#E9C46A"   # Final Recommendation button — always gold
LIGHT_TEXT     = "#F5F7FA"

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
        background-color: {NAVY_SELECTED};
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
    section[data-testid="stSidebar"] div[data-testid="stButton"]:last-of-type button {{
        background-color: {GOLD_HIGHLIGHT} !important;
        color: {NAVY_DARK} !important;
        font-weight: 700 !important;
        border: none !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stButton"]:last-of-type button:hover {{
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
    .conclusion-box textarea {{
        background-color: #F4F6FA;
        border: 1px solid #DCE2ED;
    }}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.title("🏭 Warehouse Closure Analysis")
st.caption("A SQL-Based Multi-Criteria Decision Framework")

# ─────────────────────────────────────────────────────────────
# Database connection
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def init_connection():
    return mconn.connect(
        host='localhost',
        user='root',
        password='password',
        database='mintclassics',
        auth_plugin='mysql_native_password'
    )

try:
    conn = init_connection()
except Exception as e:
    st.error(f"Could not connect to MYSQL Server: {e}")
    st.stop()

def run_query(query):
    cur = conn.cursor()
    try:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        result = cur.fetchall()
        return pd.DataFrame(result, columns=columns)
    finally:
        cur.close()

# ─────────────────────────────────────────────────────────────
# Question registry
# Each level maps question labels -> config. "chart_type" picks
# which chart function render_question() calls below. To add a
# new question: add one entry here with a query, a y-axis column,
# a chart_type, and a starting conclusion sentence.
# ─────────────────────────────────────────────────────────────
QUESTIONS = {
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
            "chart_type": "bullet",
            "conclusion": "Add your interpretation of the capacity utilization results here.",
        },
        "Q2: Total Inventory Value": {
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
            "conclusion": "Add your interpretation of the inventory value results here.",
        },
    },
    "Level 2": {},
    "Level 3": {},
    "Level 4": {},
}

def format_value(value, fmt):
    if fmt == "%":
        return f"{value:.1f}%"
    if fmt == "$":
        return f"${value:,.0f}"
    return f"{value:.2f}"

# ─────────────────────────────────────────────────────────────
# Chart builders
# ─────────────────────────────────────────────────────────────
def make_bullet_chart(df, y_col, y_label, fmt):
    """Horizontal bullet chart: light track = full range, colored
    bar = actual value, dark tick = the cross-warehouse average
    as a reference point."""
    max_domain = 100 if fmt == "%" else df[y_col].max() * 1.15

    track_df = df.copy()
    track_df["_track"] = max_domain
    track = alt.Chart(track_df).mark_bar(color="#E2E6EF", size=26).encode(
        y=alt.Y("warehouseName:N", sort=WAREHOUSE_ORDER, title=None),
        x=alt.X("_track:Q", title=y_label, scale=alt.Scale(domain=[0, max_domain])),
    )

    measure = alt.Chart(df).mark_bar(size=11).encode(
        y=alt.Y("warehouseName:N", sort=WAREHOUSE_ORDER),
        x=alt.X(f"{y_col}:Q"),
        color=alt.Color(
            "warehouseName:N",
            scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
            legend=None,
        ),
        tooltip=["warehouseName", y_col],
    )

    avg_val = df[y_col].mean()
    avg_df = df[["warehouseName"]].copy()
    avg_df["_avg"] = avg_val
    avg_tick = alt.Chart(avg_df).mark_tick(color=NAVY_DARK, thickness=3, size=26).encode(
        y=alt.Y("warehouseName:N", sort=WAREHOUSE_ORDER),
        x=alt.X("_avg:Q"),
        tooltip=[alt.Tooltip("_avg:Q", title="Average", format=".1f")],
    )

    return (track + measure + avg_tick).properties(height=260)

def make_treemap(df, y_col, y_label):
    fig = px.treemap(
        df,
        path=["warehouseName"],
        values=y_col,
        color="warehouseName",
        color_discrete_map=WAREHOUSE_COLORS,
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
        textfont_size=16,
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=380)
    return fig

def render_question(question_label, config):
    st.subheader(question_label)

    df = run_query(config["query"])
    y_col = config["y_col"]
    y_label = config["y_label"]
    fmt = config["fmt"]
    chart_type = config["chart_type"]

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
        st.markdown(f"**{y_label} by Warehouse**")
        if chart_type == "bullet":
            st.altair_chart(make_bullet_chart(df, y_col, y_label, fmt), use_container_width=True)
        elif chart_type == "treemap":
            st.plotly_chart(make_treemap(df, y_col, y_label), use_container_width=True)

    with col2:
        st.markdown("**Conclusion**")
        st.text_area(
            label="Conclusion",
            value=config["conclusion"],
            height=280,
            key=f"conclusion_{question_label}",
            label_visibility="collapsed",
        )

# ─────────────────────────────────────────────────────────────
# Sidebar navigation — buttons instead of radio/selectbox
# ─────────────────────────────────────────────────────────────
if "selected_level" not in st.session_state:
    st.session_state.selected_level = "Level 1"

st.sidebar.title("Navigation")

for lvl in ["Level 1", "Level 2", "Level 3", "Level 4"]:
    btn_type = "primary" if st.session_state.selected_level == lvl else "secondary"
    if st.sidebar.button(lvl, key=f"nav_{lvl}", type=btn_type, use_container_width=True):
        st.session_state.selected_level = lvl

st.sidebar.markdown("---")

final_type = "primary" if st.session_state.selected_level == "Level 5: Final Recommendation" else "secondary"
if st.sidebar.button("🏆 Final Recommendation", key="nav_final", type=final_type, use_container_width=True):
    st.session_state.selected_level = "Level 5: Final Recommendation"

level = st.session_state.selected_level

# ─────────────────────────────────────────────────────────────
# LEVELS 1–4 — driven by the QUESTIONS registry above
# ─────────────────────────────────────────────────────────────
LEVEL_ICONS = {"Level 1": "📊", "Level 2": "📦", "Level 3": "🤝", "Level 4": "🔁"}
LEVEL_TITLES = {
    "Level 1": "Current State Assessment",
    "Level 2": "Product Analysis",
    "Level 3": "Customer Impact",
    "Level 4": "Consolidation Feasibility",
}

if level in QUESTIONS:
    st.header(f"{LEVEL_ICONS[level]} {level}: {LEVEL_TITLES[level]}")

    if QUESTIONS[level]:
        question_keys = list(QUESTIONS[level].keys())
        state_key = f"selected_question_{level}"
        if state_key not in st.session_state:
            st.session_state[state_key] = question_keys[0]

        q_cols = st.columns(len(question_keys))
        for i, q_label in enumerate(question_keys):
            q_type = "primary" if st.session_state[state_key] == q_label else "secondary"
            if q_cols[i].button(q_label, key=f"qbtn_{level}_{q_label}", type=q_type, use_container_width=True):
                st.session_state[state_key] = q_label

        st.markdown("---")
        selected_question = st.session_state[state_key]
        config = QUESTIONS[level][selected_question]
        render_question(selected_question, config)
    else:
        st.info(f"No questions wired up yet for {level}. Add entries to the QUESTIONS dict following the Level 1 pattern.")

# ─────────────────────────────────────────────────────────────
# LEVEL 5 — Final weighted recommendation with interactive sliders
# ─────────────────────────────────────────────────────────────
elif level == "Level 5: Final Recommendation":
    st.header("🏆 Level 5: Final Weighted Recommendation")
    st.caption("Adjust the level weights below to see how the closure ranking responds.")

    mysql_query = """SELECT * FROM warehouse_scores;"""
    scores_df = run_query(mysql_query)

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
        chart = (
            alt.Chart(ranked_df)
            .mark_bar()
            .encode(
                x=alt.X("warehouseName:N", sort=WAREHOUSE_ORDER, title="Warehouse"),
                y=alt.Y("final_score:Q", title="Composite Score"),
                color=alt.Color(
                    "warehouseName:N",
                    scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
                    legend=None,
                ),
                tooltip=["warehouseName", "final_score"],
            )
            .properties(height=380)
        )
        st.altair_chart(chart, use_container_width=True)

    with col2:
        st.markdown("**Conclusion**")
        top_candidate = ranked_df.iloc[0]
        default_conclusion = f"Under these weights, {top_candidate['warehouseName']} ranks highest as the closure candidate (score: {top_candidate['final_score']:.3f})."
        st.text_area(
            label="Conclusion",
            value=default_conclusion,
            height=280,
            key="conclusion_final",
            label_visibility="collapsed",
        )