import streamlit as st
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import time
from fake_useragent import UserAgent

def get_glassdoor_reviews(company_name):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    
    company_url = company_name.lower().replace(' ', '-')
    url = f'https://www.glassdoor.com/Reviews/{company_url}-reviews-SRCH_KE0,{len(company_name)}.htm'
    
    reviews = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find review containers
        review_elements = soup.find_all('div', {'class': 'gdReview'})
        
        for review in review_elements[:5]:
            pros = review.find('span', {'data-test': 'pros'})
            cons = review.find('span', {'data-test': 'cons'})
            
            if pros and cons:
                review_text = f"Pros: {pros.text} Cons: {cons.text}"
                reviews.append(review_text)
                
        return reviews
    except Exception as e:
        return []

def analyze_reviews(reviews):
    if not reviews:
        return "No reviews found", 0, []
    
    sentiments = []
    for review in reviews:
        analysis = TextBlob(review)
        sentiments.append(analysis.sentiment.polarity)
    
    avg_sentiment = sum(sentiments) / len(sentiments)
    
    if avg_sentiment > 0.3:
        culture = "Very Positive"
    elif avg_sentiment > 0:
        culture = "Positive"
    elif avg_sentiment > -0.3:
        culture = "Neutral"
    else:
        culture = "Negative"
        
    return culture, avg_sentiment, reviews

st.set_page_config(page_title="Company Culture Analyzer", layout="wide")

st.title("Company Culture Analyzer")
st.markdown("""
This app analyzes company culture based on Glassdoor reviews using sentiment analysis.
""")

company_name = st.text_input("Enter Company Name:")

if st.button("Analyze Culture"):
    if company_name:
        with st.spinner("Analyzing company reviews..."):
            reviews = get_glassdoor_reviews(company_name)
            culture, sentiment_score, sample_reviews = analyze_reviews(reviews)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Company Culture", culture)
                st.metric("Sentiment Score", f"{sentiment_score:.2f}")
                
            with col2:
                if sample_reviews:
                    st.subheader("Sample Reviews")
                    for i, review in enumerate(sample_reviews, 1):
                        with st.expander(f"Review {i}"):
                            st.write(review)
                else:
                    st.error("No reviews found. The company might not be listed or there could be an error accessing the data.")
    else:
        st.warning("Please enter a company name")

print("Streamlit app is running")