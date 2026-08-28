# Color palette, formatting, and chart builders for the Warehouse Closure Analysis app.

import altair as alt
import plotly.express as px

WAREHOUSE_COLORS = {
    "North": "#264653",   # dark slate teal
    "South": "#2A9D8F",   # teal
    "East":  "#E9C46A",   # gold
    "West":  "#E76F51",   # burnt orange
}
WAREHOUSE_ORDER = list(WAREHOUSE_COLORS.keys())

NAVY_DARK = "#0B1526"


def format_value(value, fmt):
    if fmt == "%":
        return f"{value:.1f}%"
    if fmt == "$":
        return f"${value:,.0f}"
    return f"{value:.2f}"


def make_simple_bar_chart(df, category_col, value_col, value_label):
    """Plain ranked bar chart — for a single count/value per
    warehouse with no need for a reference line or track (that's
    what make_bullet_chart is for). Use for straightforward
    comparisons like total units sold or unique products sold.
    """
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{category_col}:N", sort=WAREHOUSE_ORDER, title=None),
            y=alt.Y(f"{value_col}:Q", title=value_label),
            color=alt.Color(
                f"{category_col}:N",
                scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
                legend=None,
            ),
            tooltip=[category_col, value_col],
        )
        .properties(height=300)
    )


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


def make_donut_chart(df, category_col, value_col, value_label):
    """Donut chart showing each warehouse's share of a total —
    e.g. share of total revenue. Better than a bar chart when the
    question is 'how much of the whole pie' rather than 'who's
    highest'.
    """
    fig = px.pie(
        df,
        names=category_col,
        values=value_col,
        color=category_col,
        color_discrete_map=WAREHOUSE_COLORS,
        hole=0.5,
    )
    fig.update_traces(textinfo="label+percent", textfont_size=13)
    fig.update_layout(showlegend=False, margin=dict(t=20, l=20, r=20, b=20), height=340)
    return fig


def make_lollipop_chart(df, category_col, value_col, value_label, fmt=""):
    """Lollipop chart — a thin stem + dot per warehouse. Reads more
    precisely than a bar chart when values are close together
    (e.g. average order values within a few hundred dollars of
    each other), since the eye compares dot positions rather than
    bar-area differences.
    """
    stems = alt.Chart(df).mark_rule(color="#C7CEDB", size=2).encode(
        x=alt.X(f"{category_col}:N", sort=WAREHOUSE_ORDER, title=None),
        y=alt.Y(f"{value_col}:Q", title=value_label),
        y2=alt.value(0),
    )
    dots = alt.Chart(df).mark_circle(size=220).encode(
        x=alt.X(f"{category_col}:N", sort=WAREHOUSE_ORDER),
        y=alt.Y(f"{value_col}:Q"),
        color=alt.Color(
            f"{category_col}:N",
            scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
            legend=None,
        ),
        tooltip=[category_col, value_col],
    )
    return (stems + dots).properties(height=300)


def make_composite_score_chart(ranked_df):
    """Level 5 bar chart of final weighted composite score per warehouse."""
    return (
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


def make_diverging_bar_chart(df, category_col, value_col, value_label):
    """Diverging bar chart — bars extend right (positive, growth)
    or left (negative, decline) from a zero baseline. Best for
    growth percentages or any metric that can be positive or
    negative, where the sign matters as much as the magnitude.
    """
    df = df.copy()
    df["_direction"] = df[value_col].apply(
        lambda v: "Growth" if v >= 0 else "Decline")

    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y(f"{category_col}:N", sort=WAREHOUSE_ORDER, title=None),
            x=alt.X(f"{value_col}:Q", title=value_label),
            color=alt.Color(
                "_direction:N",
                scale=alt.Scale(domain=["Growth", "Decline"],
                                range=[WAREHOUSE_COLORS["South"],
                                       WAREHOUSE_COLORS["West"]]),
                legend=alt.Legend(title=None),
            ),
            tooltip=[category_col, value_col],
        )
        .properties(height=280)
    )



def make_radar_chart(df, category_col, value_cols, value_labels=None):
    """Radar/spider chart comparing warehouses across several
    normalized dimensions at once. Best for a composite view —
    e.g. Level 5's per-level scores for each warehouse.

    df must have one row per warehouse, with value_cols already
    on a comparable scale (0-1 or 0-100) — radar charts distort
    badly if axes have wildly different ranges.
    """
    value_labels = value_labels or value_cols
    fig = px.line_polar(
        df.melt(id_vars=category_col, value_vars=value_cols,
                var_name="metric", value_name="score"),
        r="score",
        theta="metric",
        color=category_col,
        line_close=True,
        color_discrete_map=WAREHOUSE_COLORS,
    )
    fig.update_traces(fill="toself", opacity=0.4)
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, df[value_cols].values.max() * 1.1])),
        height=420,
        margin=dict(t=40, l=40, r=40, b=40),
    )
    return fig


def make_indicator_radar_chart(df, category_col, indicator_cols, indicator_labels=None):
    """Radar chart with warehouses at the corners and one line per
    indicator — the mirror image of make_radar_chart (which puts
    warehouses as lines and metrics as corners). Use this when the
    story is 'does one warehouse consistently score low across
    every indicator', since a warehouse dipping on every line reads
    immediately, whereas make_radar_chart would spread that same
    story across several separate warehouse-shaped blobs.

    df must have one row per category_col value (e.g. one row per
    warehouse), with indicator_cols already normalized to the same
    scale (0-1 or 0-100).
    """
    indicator_labels = indicator_labels or indicator_cols
    long_df = df.melt(id_vars=category_col, value_vars=indicator_cols,
                       var_name="indicator", value_name="score")

    fig = px.line_polar(
        long_df,
        r="score",
        theta=category_col,
        color="indicator",
        line_close=True,
        category_orders={category_col: WAREHOUSE_ORDER},
    )
    fig.update_traces(fill="toself", opacity=0.25)
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, long_df["score"].max() * 1.1])),
        height=460,
        margin=dict(t=40, l=40, r=40, b=40),
        legend=dict(title=None),
    )
    return fig

def make_histogram(df, value_col, value_label, color_col="warehouseName", bins=20):
    """Histogram showing the distribution/spread of a continuous
    variable, optionally colored by warehouse (overlapping or
    faceted). Good for order-value spread, delivery times, etc. —
    anything where the *shape* of the distribution matters, not
    just a single summary number per warehouse.
    """
    return (
        alt.Chart(df)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X(f"{value_col}:Q", bin=alt.Bin(maxbins=bins), title=value_label),
            y=alt.Y("count():Q", title="Count"),
            color=alt.Color(
                f"{color_col}:N",
                scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
                legend=alt.Legend(title=None),
            ),
        )
        .properties(height=340)
    )


def make_grouped_bar_chart(df, category_col, value_cols, value_labels=None):
    """Grouped bar chart comparing 2+ metrics side-by-side per
    warehouse — e.g. revenue vs. quantity sold per warehouse.
    """
    value_labels = value_labels or value_cols
    long_df = df.melt(id_vars=category_col, value_vars=value_cols,
                       var_name="metric", value_name="value")
    return (
        alt.Chart(long_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{category_col}:N", sort=WAREHOUSE_ORDER, title=None),
            y=alt.Y("value:Q", title="Value"),
            color=alt.Color(f"{category_col}:N",
                             scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
                             legend=None),
            column=alt.Column("metric:N", title=None),
            tooltip=[category_col, "metric", "value"],
        )
        .properties(height=280, width=120)
    )


def make_heatmap(df, x_col, y_col, value_col, value_label):
    """Heatmap for cross-tabulated intensity — e.g. warehouse x
    product-category, colored by revenue or unit count. Good for
    spotting concentration patterns a bar chart would hide.
    """
    return (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X(f"{x_col}:N", title=None),
            y=alt.Y(f"{y_col}:N", sort=WAREHOUSE_ORDER, title=None),
            color=alt.Color(f"{value_col}:Q", title=value_label, scale=alt.Scale(scheme="reds")),
            tooltip=[x_col, y_col, value_col],
        )
        .properties(height=300)
    )


def make_trend_line_chart(df, date_col, value_col, value_label, color_col="warehouseName"):
    """Line chart showing a metric's trend over time, one line per
    warehouse. Good for monthly order volume, sales trend, etc.
    """
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{date_col}:T", title="Date"),
            y=alt.Y(f"{value_col}:Q", title=value_label),
            color=alt.Color(
                f"{color_col}:N",
                scale=alt.Scale(domain=WAREHOUSE_ORDER, range=[WAREHOUSE_COLORS[w] for w in WAREHOUSE_ORDER]),
                legend=alt.Legend(title=None),
            ),
            tooltip=[color_col, date_col, value_col],
        )
        .properties(height=340)
    )

def make_country_warehouse_map(df, country_col, warehouse_col, dependency_col):
    """Choropleth map coloring each country by its primary
    (highest-spend) warehouse. Countries served by only one
    warehouse get a solid, saturated color; multi-warehouse
    countries are shown in a muted grey so the single-warehouse
    ones — the actual risk story — visually pop out.
    """
    df = df.copy()
    df["_map_color"] = df.apply(
        lambda r: r[warehouse_col] if r[dependency_col] == "Single-Warehouse" else "Multi-Warehouse",
        axis=1,
    )
    color_map = {**WAREHOUSE_COLORS, "Multi-Warehouse": "#2761F5"}

    fig = px.choropleth(
        df,
        locations=country_col,
        locationmode="country names",
        color="_map_color",
        color_discrete_map=color_map,
        hover_name=country_col,
        hover_data={warehouse_col: True, dependency_col: True, "_map_color": False},
    )
    fig.update_layout(
        margin=dict(t=20, l=0, r=0, b=0),
        height=440,
        legend=dict(title=None),
    )
    return fig


def make_category_bar_chart(df, category_col, value_col, value_label):
    """Plain bar chart for categories that aren't warehouses (e.g.
    product lines) — same idea as make_simple_bar_chart, but uses
    a standard qualitative palette instead of WAREHOUSE_COLORS.
    """
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(f"{category_col}:N", sort="-y", title=None),
            y=alt.Y(f"{value_col}:Q", title=value_label),
            color=alt.Color(f"{category_col}:N", scale=alt.Scale(scheme="tableau10"), legend=None),
            tooltip=[category_col, value_col],
        )
        .properties(height=340)
    )