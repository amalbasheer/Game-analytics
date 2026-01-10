# pages/3_Competitor_Rankings.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from db_config import DatabaseConfig

st.set_page_config(
    page_title="Competitor Rankings Analysis",
    layout="wide"
)

st.title("🏆 Competitor Rankings Analysis")
st.markdown("Analyze doubles competitor rankings, find top players, and explore country-wise performance.")
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


# --- Competitor Rankings Analysis Sections ---

st.subheader("1. Search and Filter Competitors")
st.write("Use the filters below to find specific competitors or groups of players.")
competitor_name_search = st.text_input("Search Competitor by Name (partial match)", "",
                                       help="Enter full or partial name.")

col_filters_1, col_filters_2 = st.columns(2)
with col_filters_1:
    min_rank = st.number_input("Minimum Rank", min_value=1, value=1, help="Filter by minimum rank.")
    max_rank = st.number_input("Maximum Rank", min_value=1, value=10000, help="Filter by maximum rank.")
with col_filters_2:
    min_points = st.number_input("Minimum Points", min_value=0, value=0, help="Filter by minimum total points.")
    max_points = st.number_input("Maximum Points", min_value=0, value=1000000,
                                 help="Filter by maximum total points.")  # Adjusted max_value

competitor_countries_df = run_sql_query("SELECT DISTINCT country FROM competitors ORDER BY country;")
selected_country_competitor = st.selectbox(
    "Filter by Country",
    ['All'] + (competitor_countries_df['country'].tolist() if not competitor_countries_df.empty else []),
    index=0,
    help="Select a country to filter competitors."
)

search_query_base = """
                    SELECT c.name AS competitor_name, \
                           cr.rank, \
                           cr.movement, \
                           cr.points, \
                           cr.competitions_played, \
                           c.country, \
                           c.country_code
                    FROM competitor_rankings cr \
                             JOIN \
                         competitors c ON cr.competitor_id = c.competitor_id
                    WHERE 1 = 1 \
                    """
if competitor_name_search:
    search_query_base += f" AND c.name ILIKE '%{competitor_name_search}%'"  # ILIKE for case-insensitive search in PostgreSQL

search_query_base += f" AND cr.rank >= {min_rank} AND cr.rank <= {max_rank}"
search_query_base += f" AND cr.points >= {min_points} AND cr.points <= {max_points}"

if selected_country_competitor != 'All':
    search_query_base += f" AND c.country = '{selected_country_competitor}'"

search_query_base += " ORDER BY cr.rank;"

filtered_competitors_df = run_sql_query(search_query_base)
if not filtered_competitors_df.empty:
    st.dataframe(filtered_competitors_df, use_container_width=True)
else:
    st.info("No competitors found matching the selected filters.")

st.markdown("---")

st.subheader("2. Competitor Details Viewer")
st.write("Select a competitor from the filtered list above to view detailed information.")
if not filtered_competitors_df.empty:
    competitor_names = filtered_competitors_df['competitor_name'].tolist()
    selected_competitor_name = st.selectbox("Select a Competitor", competitor_names, index=0)

    if selected_competitor_name:
        competitor_details_df = run_sql_query(f"""
            SELECT
                c.name AS competitor_name,
                cr.rank,
                cr.movement,
                cr.points,
                cr.competitions_played,
                c.country,
                c.country_code,
                c.abbreviation
            FROM
                competitor_rankings cr
            JOIN
                competitors c ON cr.competitor_id = c.competitor_id
            WHERE
                c.name = '{selected_competitor_name}';
        """)
        if not competitor_details_df.empty:
            st.table(competitor_details_df.transpose())  # Transpose for better readability
else:
    st.info("No competitors to display details for based on current filters.")

st.markdown("---")

st.subheader("3. Leaderboards")
st.markdown("#### Top-Ranked Competitors")
top_ranked_df = run_sql_query("""
                              SELECT c.name AS competitor_name,
                                     cr.rank,
                                     cr.points,
                                     c.country
                              FROM competitor_rankings cr
                                       JOIN
                                   competitors c ON cr.competitor_id = c.competitor_id
                              ORDER BY cr.rank LIMIT 10;
                              """)
if not top_ranked_df.empty:
    st.dataframe(top_ranked_df, use_container_width=True)
else:
    st.info("No top-ranked competitors found.")

st.markdown("#### Competitors with Highest Points")
highest_points_df = run_sql_query("""
                                  SELECT c.name AS competitor_name,
                                         cr.points,
                                         cr.rank,
                                         c.country
                                  FROM competitor_rankings cr
                                           JOIN
                                       competitors c ON cr.competitor_id = c.competitor_id
                                  ORDER BY cr.points DESC LIMIT 10;
                                  """)
if not highest_points_df.empty:
    st.dataframe(highest_points_df, use_container_width=True)
else:
    st.info("No competitors with highest points found.")

st.markdown("---")

st.subheader("4. Country-Wise Analysis")
st.write("View the number of competitors and average points per country.")
country_analysis_df = run_sql_query("""
                                    SELECT c.country,
                                           COUNT(c.competitor_id) AS number_of_competitors,
                                           AVG(cr.points)         AS average_points
                                    FROM competitors c
                                             JOIN
                                         competitor_rankings cr ON c.competitor_id = cr.competitor_id
                                    GROUP BY c.country
                                    ORDER BY number_of_competitors DESC;
                                    """)
if not country_analysis_df.empty:
    st.dataframe(country_analysis_df, use_container_width=True)
else:
    st.info("No country-wise analysis data available.")