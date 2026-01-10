# pages/1_Competitions.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from db_config import DatabaseConfig

st.set_page_config(
    page_title="Competitions Analysis",
    layout="wide"
)

st.title("📊 Competition Analysis")
st.markdown("Explore various tennis competitions, their categories, types, and hierarchies.")
st.markdown("---")


# --- Database Connection ---

@st.cache_resource
def get_db_connection():
    conn_string = DatabaseConfig.get_connection_string()
    try:
        engine = create_engine(conn_string)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return engine
    except Exception:

        return None


engine = get_db_connection()


# --- Function to run SQL queries ---
def run_sql_query(query: str, engine_obj=engine) -> pd.DataFrame:
    if engine_obj is None:
        st.warning("Database connection not established. Some features may not work.")
        return pd.DataFrame()
    try:
        with engine_obj.connect() as connection:
            result = connection.execute(text(query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()


# --- Competition Analysis Sections ---

st.subheader("1. Filter Competitions")
st.write("Use the filters below to refine your view of the competitions.")

# Fetch unique values for filters
all_categories_df = run_sql_query("SELECT DISTINCT category_name FROM categories ORDER BY category_name;")
all_types_df = run_sql_query("SELECT DISTINCT type FROM competitions ORDER BY type;")
all_genders_df = run_sql_query("SELECT DISTINCT gender FROM competitions ORDER BY gender;")
all_levels_df = run_sql_query("SELECT DISTINCT level FROM competitions WHERE level IS NOT NULL ORDER BY level;")

col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)

with col_filter1:
    selected_category = st.selectbox(
        "Category",
        ['All'] + (all_categories_df['category_name'].tolist() if not all_categories_df.empty else []),
        index=0,  # Default to 'All'
        help="Filter competitions by category."
    )
with col_filter2:
    selected_type = st.selectbox(
        "Type",
        ['All'] + (all_types_df['type'].tolist() if not all_types_df.empty else []),
        index=0,  # Default to 'All'
        help="Filter competitions by type (e.g., singles, doubles, mixed)."
    )
with col_filter3:
    selected_gender = st.selectbox(
        "Gender",
        ['All'] + (all_genders_df['gender'].tolist() if not all_genders_df.empty else []),
        index=0,  # Default to 'All'
        help="Filter competitions by gender (e.g., men, women, mixed)."
    )
with col_filter4:
    selected_level = st.selectbox(
        "Level",
        ['All'] + (all_levels_df['level'].tolist() if not all_levels_df.empty else []),
        index=0,  # Default to 'All'
        help="Filter competitions by level (e.g., atp_250, wta_premier)."
    )

# Build dynamic WHERE clause
where_clauses = []
if selected_category != 'All':
    where_clauses.append(f"cat.category_name = '{selected_category}'")
if selected_type != 'All':
    where_clauses.append(f"c.type = '{selected_type}'")
if selected_gender != 'All':
    where_clauses.append(f"c.gender = '{selected_gender}'")
if selected_level != 'All':
    where_clauses.append(f"c.level = '{selected_level}'")

where_condition = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

filtered_competitions_query = f"""
    SELECT
        c.competition_name,
        cat.category_name,
        c.type,
        c.gender,
        c.level,
        CASE WHEN c.parent_id IS NULL THEN 'Yes' ELSE 'No' END AS is_top_level
    FROM
        competitions c
    JOIN
        categories cat ON c.category_id = cat.category_id
    {where_condition}
    ORDER BY cat.category_name, c.competition_name;
"""
filtered_competitions_df = run_sql_query(filtered_competitions_query)

if not filtered_competitions_df.empty:
    st.dataframe(filtered_competitions_df, use_container_width=True)
else:
    st.info("No competitions found matching the selected filters.")

st.markdown("---")

st.subheader("2. Competitions per Category (Bar Chart)")
st.write("Distribution of competitions across different categories.")
competitions_per_category_df = run_sql_query("""
                                             SELECT cat.category_name,
                                                    COUNT(c.competition_id) AS number_of_competitions
                                             FROM categories cat
                                                      LEFT JOIN
                                                  competitions c ON cat.category_id = c.category_id
                                             GROUP BY cat.category_name
                                             ORDER BY number_of_competitions DESC;
                                             """)
st.dataframe(competitions_per_category_df, use_container_width=True)
if not competitions_per_category_df.empty:
    st.bar_chart(competitions_per_category_df.set_index('category_name'))

st.subheader("3. Competition Hierarchy Viewer")
st.write("View parent and sub-competition relationships.")
hierarchy_query = """
                  SELECT COALESCE(p.competition_name, '--- Top Level ---') AS parent_competition, \
                         s.competition_name                                AS sub_competition, \
                         s.type, \
                         s.gender, \
                         s.level
                  FROM competitions s \
                           LEFT JOIN \
                       competitions p ON s.parent_id = p.competition_id
                  ORDER BY parent_competition, sub_competition; \
                  """
competition_hierarchy_df = run_sql_query(hierarchy_query)
st.dataframe(competition_hierarchy_df, use_container_width=True)