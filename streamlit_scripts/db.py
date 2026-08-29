# Database connection and query execution for the Warehouse Closure Analysis app.

import pandas as pd
import mysql.connector as mconn
import streamlit as st

from decimal import Decimal


@st.cache_resource
def init_connection():
    """Create (and cache) a single MySQL connection for the app's
    lifetime."""
    return mconn.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"],
        port=st.secrets.get("DB_PORT", 3306),
        auth_plugin='mysql_native_password',
        ssl_disabled = False,
    )


def get_connection():
    """Public entry point other modules should use to get a live
    connection, with a friendly Streamlit error + stop on failure.
    Also verifies the cached connection is still alive and
    transparently reconnects if MySQL dropped it (e.g. idle
    timeout, or the local server was restarted since the app
    started) — without this check, a stale cached connection
    would break every query for the rest of the session.
    """
    try:
        conn = init_connection()
        if not conn.is_connected():
            conn.reconnect(attempts=3, delay=2)
        return conn
    except Exception as e:
        st.error(f"Could not connect to MYSQL Server: {e}")
        st.stop()


def run_query(query):
    """Execute a SQL string against the app's MySQL connection and
    return the result as a DataFrame. Decimal columns (from SQL
    ROUND/SUM on DECIMAL types) are converted to float, since
    Python's Decimal type can't be multiplied with plain floats —
    which Altair/pandas do internally when building charts."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        result = cur.fetchall()
        df = pd.DataFrame(result, columns=columns)
        for col in df.columns:
            if df[col].apply(lambda v: isinstance(v, Decimal)).any():
                df[col] = df[col].astype(float)
        return df
    finally:
        cur.close()
