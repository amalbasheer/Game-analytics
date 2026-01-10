# pages/2_Complexes_Venues.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from db_config import DatabaseConfig

st.set_page_config(
    page_title="Complexes & Venues Analysis",
    layout="wide"
)

st.title("🏟️ Complexes and Venues Analysis")
st.markdown("Discover sports complexes and the venues they host, with geographical insights.")
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


# --- Complexes & Venues Analysis Sections ---

st.subheader("1. All Venues and Associated Complexes")
st.write("A listing of all tennis venues and the complexes they belong to.")
venues_complexes_df = run_sql_query("""
                                    SELECT v.venue_name,
                                           c.complex_name,
                                           v.city_name,
                                           v.country_name,
                                           v.timezone
                                    FROM venues v
                                             JOIN
                                         complexes c ON v.complex_id = c.complex_id
                                    ORDER BY c.complex_name, v.venue_name;
                                    """)
st.dataframe(venues_complexes_df, use_container_width=True)

st.subheader("2. Number of Venues per Complex")
st.write("Count of venues hosted by each sports complex.")
venues_per_complex_df = run_sql_query("""
                                      SELECT c.complex_name,
                                             COUNT(v.venue_id) AS number_of_venues
                                      FROM complexes c
                                               LEFT JOIN
                                           venues v ON c.complex_id = v.complex_id
                                      GROUP BY c.complex_name
                                      ORDER BY number_of_venues DESC;
                                      """)
st.dataframe(venues_per_complex_df, use_container_width=True)
if not venues_per_complex_df.empty:
    st.bar_chart(venues_per_complex_df.set_index('complex_name'))

st.subheader("3. Venues in a Specific Country")
countries_venues = run_sql_query("SELECT DISTINCT country_name FROM venues ORDER BY country_name;")
if not countries_venues.empty:
    selected_country_venue = st.selectbox("Select a Country", countries_venues['country_name'].tolist(), index=0)
    venues_by_country_df = run_sql_query(f"""
        SELECT
            venue_name,
            city_name,
            country_name,
            timezone,
            c.complex_name
        FROM
            venues v
        LEFT JOIN
            complexes c ON v.complex_id = c.complex_id
        WHERE
            v.country_name = '{selected_country_venue}'
        ORDER BY venue_name;
    """)
    st.dataframe(venues_by_country_df, use_container_width=True)
else:
    st.info("No venue countries available in the database.")

st.subheader("4. Complexes with Multiple Venues")
st.write("Identifies complexes that host more than one venue.")
multi_venue_complexes_df = run_sql_query("""
                                         SELECT c.complex_name,
                                                COUNT(v.venue_id)                                    AS number_of_venues,
                                                STRING_AGG(v.venue_name, ', ' ORDER BY v.venue_name) AS venue_list
                                         FROM complexes c
                                                  JOIN
                                              venues v ON c.complex_id = v.complex_id
                                         GROUP BY c.complex_name
                                         HAVING COUNT(v.venue_id) > 1
                                         ORDER BY number_of_venues DESC;
                                         """)
st.dataframe(multi_venue_complexes_df, use_container_width=True)