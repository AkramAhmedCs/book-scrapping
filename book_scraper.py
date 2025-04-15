import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from pymongo import MongoClient
import time
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from tqdm import tqdm  # For progress bar
import sys
import io

# ----------------------
# STEP 1: Web Scraping with Progress
# ----------------------
def scrape_books():
    base_url = "http://books.toscrape.com/"
    all_books = []
    
    try:
        # Get main page
        print("🌐 Connecting to website...")
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract categories (skip "Books" category)
        categories = [cat.text.strip() for cat in soup.select('.nav-list a')[1:]]
        category_links = [base_url + cat['href'] for cat in soup.select('.nav-list a')[1:]]
        
        print(f"📚 Found {len(categories)} categories to scrape")
        
        # Initialize progress bar
        pbar = tqdm(total=len(category_links), desc="Scraping Categories", unit="cat")
        
        for category, link in zip(categories, category_links):
            pbar.set_postfix({'current': category[:15] + "..."})
            
            while True:
                try:
                    response = requests.get(link, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    books = soup.find_all('article', class_='product_pod')
                    
                    # Book-level progress
                    book_pbar = tqdm(books, desc=f"Books in {category[:15]}", leave=False)
                    
                    for book in book_pbar:
                        try:
                            title = book.h3.a['title']
                            price = float(book.find('p', class_='price_color').text[1:])
                            
                            # Get book details
                            book_url = base_url + 'catalogue/' + book.h3.a['href'].replace('../', '')
                            book_response = requests.get(book_url)
                            book_soup = BeautifulSoup(book_response.content, 'html.parser')
                            
                            description = book_soup.find('meta', attrs={'name': 'description'})['content'].strip()
                            isbn = re.search(r'ISBN[-\s:]*([0-9X-]+)', description).group(1) if re.search(r'ISBN[-\s:]*([0-9X-]+)', description) else None
                            
                            all_books.append({
                                'title': title,
                                'price': price,
                                'genre': category,
                                'isbn': isbn,
                                'description': description
                            })
                            time.sleep(0.5)  # Polite delay
                            
                        except Exception as e:
                            continue
                            
                    book_pbar.close()
                    
                    # Pagination
                    next_button = soup.find('li', class_='next')
                    if next_button:
                        link = '/'.join(link.split('/')[:-1]) + '/' + next_button.a['href']
                    else:
                        break
                        
                except Exception as e:
                    break
            
            pbar.update(1)
            
        pbar.close()
        return pd.DataFrame(all_books)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return pd.DataFrame()

# ----------------------
# STEP 2: Data Cleaning
# ----------------------
def clean_data(df):
    if df.empty:
        return df
        
    print("\n🧹 Cleaning data...")
    # Handle missing values
    df['price'] = df['price'].fillna(df['price'].median())
    
    # Clean genres
    df['genre'] = df['genre'].str.replace(r'\s+', ' ', regex=True)
    
    # Clean ISBN
    df['isbn'] = df['isbn'].str.replace(r'[^0-9X-]', '', regex=True) if 'isbn' in df.columns else None
    
    return df

# ----------------------
# STEP 3: MongoDB Storage
# ----------------------
def store_in_mongodb(df):
    if df.empty:
        return
        
    try:
        print("\n💾 Saving to MongoDB...")
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        db = client['book_database']
        collection = db['books']
        
        # Clear old data
        collection.delete_many({})
        
        # Insert with progress
        records = df.to_dict('records')
        for i in tqdm(range(0, len(records), 100), desc="Inserting to MongoDB"):
            collection.insert_many(records[i:i+100])
            
        print(f"✅ Saved {len(df)} books to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB error: {str(e)}")

# ----------------------
# STEP 4: Analysis & Visualization
# ----------------------
def analyze_data(df):
    if df.empty:
        return {}
        
    print("\n📊 Analyzing data...")
    # Save files
    df.to_csv('raw_books.csv', index=False)
    cleaned_df = clean_data(df)
    cleaned_df.to_csv('cleaned_books.csv', index=False)
    
    # Basic stats
    stats = {
        'total_books': len(cleaned_df),
        'avg_price': cleaned_df['price'].mean(),
        'top_genre': cleaned_df['genre'].mode()[0] if not cleaned_df['genre'].empty else None
    }
    
    # Visualizations
    if not cleaned_df.empty:
        plt.figure(figsize=(10, 6))
        sns.countplot(data=cleaned_df, y='genre', 
                     order=cleaned_df['genre'].value_counts().iloc[:10].index)
        plt.title('Top 10 Genres by Book Count')
        plt.tight_layout()
        plt.savefig('top_genres.png')
        plt.close()
        
        fig = px.box(cleaned_df, x='genre', y='price', 
                    title='Price Distribution by Genre')
        fig.write_html('price_distribution.html')
    
    return stats

# ----------------------
# STEP 5: Streamlit Dashboard (Fixed Encoding)
# ----------------------
def create_streamlit_app():
    print("\n🖥️ Creating Streamlit app...")
    content = '''import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# Connect to MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    db = client['book_database']
    df = pd.DataFrame(list(db['books'].find({})))
except Exception as e:
    st.error(f"Database connection failed: {e}")
    df = pd.DataFrame()

st.title("📚 Book Analysis Dashboard")

if not df.empty:
    # Filters
    genre_filter = st.sidebar.multiselect('Filter by Genre', df['genre'].unique())
    price_range = st.sidebar.slider('Price Range', 
                                  float(df['price'].min()), 
                                  float(df['price'].max()),
                                  (float(df['price'].min()), float(df['price'].max())))

    # Apply filters
    filtered_df = df[
        (df['genre'].isin(genre_filter) if genre_filter else True) &
        (df['price'].between(price_range[0], price_range[1]))
    ]

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Books", len(filtered_df))
    col2.metric("Average Price", f"${filtered_df['price'].mean():.2f}")

    # Visualizations
    if not filtered_df.empty:
        st.plotly_chart(px.bar(filtered_df, x='genre', title='📊 Books by Genre'))
        st.plotly_chart(px.box(filtered_df, x='genre', y='price', title='💰 Price Distribution'))
    
    # Raw data
    if st.checkbox('Show Raw Data'):
        st.dataframe(filtered_df)
else:
    st.warning("No book data available. Please run the scraper first.")
'''

    with io.open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Streamlit app created successfully!")

# ----------------------
# MAIN EXECUTION
# ----------------------
if __name__ == '__main__':
    print("="*50)
    print("📖 BOOK SCRAPER & ANALYZER")
    print("="*50)
    
    # Step 1: Scraping
    df = scrape_books()
    
    if not df.empty:
        # Step 2-4: Processing
        cleaned_df = clean_data(df)
        store_in_mongodb(cleaned_df)
        stats = analyze_data(df)
        
        print("\n📈 Analysis Results:")
        print(f"- Total books: {stats['total_books']}")
        print(f"- Average price: ${stats['avg_price']:.2f}")
        print(f"- Top genre: {stats['top_genre']}")
        
        # Step 5: Dashboard
        create_streamlit_app()
        
        print("\n✅ All done! Here's how to view your results:")
        print("1. CSV Files:")
        print("   - raw_books.csv (original data)")
        print("   - cleaned_books.csv (processed data)")
        print("2. Visualizations:")
        print("   - top_genres.png (image)")
        print("   - price_distribution.html (interactive)")
        print("3. Dashboard:")
        print("   Run: streamlit run streamlit_app.py")
        print("   Then open http://localhost:8501 in your browser")
    else:
        print("\n❌ No data was scraped. Please check your internet connection and try again.")
    
    input("\nPress Enter to exit...")