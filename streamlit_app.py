import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# ======================
# MongoDB Atlas Connection
# ======================
def get_data():
    try:
        # 1. Try MongoDB Atlas first
        client = MongoClient(st.secrets["MONGODB_URI"])
        db = client['book_database']
        books = list(db['books'].find({}))
        df = pd.DataFrame(books)
        st.success(f"✅ Loaded {len(df)} books from MongoDB Atlas")
        return df
        
    except Exception as e:
        st.error(f"❌ MongoDB Error: {str(e)}")
        
        # 2. Fallback to CSV if MongoDB fails
        try:
            df = pd.read_csv('cleaned_books.csv')
            st.warning("⚠️ Using local CSV data instead")
            return df
        except:
            st.error("No data available!")
            return pd.DataFrame()

# ======================
# Dashboard UI
# ======================
st.set_page_config(page_title="Book Dashboard", layout="wide")
st.title("📚 Book Analysis Dashboard")

# Load data
df = get_data()

if not df.empty:
    # Filters
    st.sidebar.header("Filters")
    selected_genres = st.sidebar.multiselect(
        "Select Genres",
        options=df['genre'].unique()
    )
    
    min_price, max_price = st.sidebar.slider(
        "Price Range",
        float(df['price'].min()),
        float(df['price'].max()),
        (float(df['price'].min()), float(df['price'].max()))
    )

    # Apply filters
    filtered_df = df[
        (df['genre'].isin(selected_genres) if selected_genres else True
    ].query("price >= @min_price and price <= @max_price")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Books", len(filtered_df))
    col2.metric("Avg Price", f"${filtered_df['price'].mean():.2f}")
    col3.metric("Top Genre", filtered_df['genre'].mode()[0])

    # Data & Visualizations
    with st.expander("View Raw Data"):
        st.dataframe(filtered_df)
    
    tab1, tab2 = st.tabs(["📊 Charts", "📈 Insights"])
    with tab1:
        st.plotly_chart(px.bar(filtered_df, x='genre', title='Books by Genre'))
        st.plotly_chart(px.box(filtered_df, x='genre', y='price', title='Price Analysis'))
    with tab2:
        st.write("### Genre Distribution")
        st.table(filtered_df['genre'].value_counts())
else:
    st.info("No data available. Please check your connection.")
