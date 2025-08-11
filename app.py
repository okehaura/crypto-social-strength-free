# app.py
import streamlit as st
import requests
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import subprocess

# Optional: try importing snscrape for tweets
try:
    import snscrape.modules.twitter as sntwitter
    SCRAPE_AVAILABLE = True
except ImportError:
    SCRAPE_AVAILABLE = False

analyzer = SentimentIntensityAnalyzer()

# ---------------------
# Get social data from LunarCrush
# ---------------------
def get_lunarcrush_data(symbol):
    url = f"https://lunarcrush.com/api/v2?data=assets&symbol={symbol.upper()}&data_points=30"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    if "data" not in data or len(data["data"]) == 0:
        return None
    asset = data["data"][0]
    return asset

# ---------------------
# Optional: scrape tweets for sentiment
# ---------------------
def scrape_twitter_sentiment(symbol, limit=50):
    if not SCRAPE_AVAILABLE:
        return None
    query = f"({symbol} OR ${symbol} OR #{symbol}) lang:en"
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        tweets.append(tweet.content)
    if not tweets:
        return None
    scores = [analyzer.polarity_scores(t)["compound"] for t in tweets]
    return np.mean(scores)  # Average compound score

# ---------------------
# Score calculation
# ---------------------
def compute_social_strength(asset, tweet_sentiment=None):
    # Extract metrics
    vol_score = asset.get("galaxy_score", 50) / 100  # 0–1
    sentiment_score = asset.get("average_sentiment", 0.5)
    if tweet_sentiment is not None:
        # Override with live tweet sentiment (scaled 0–1)
        sentiment_score = (tweet_sentiment + 1) / 2
    engagement_score = asset.get("social_score", 50) / 100000  # scaled down
    engagement_score = min(1.0, engagement_score)

    influencer_score = asset.get("influencer_count", 0) / 50  # max 50 for scale
    influencer_score = min(1.0, influencer_score)

    dominance_score = asset.get("social_dominance", 0) / 100  # percentage → 0–1

    # Weights
    score = (
        0.35 * vol_score +
        0.25 * sentiment_score +
        0.20 * engagement_score +
        0.10 * influencer_score +
        0.10 * dominance_score
    ) * 100
    return round(score, 1)

# ---------------------
# Streamlit UI
# ---------------------
st.set_page_config(page_title="Crypto Social Strength (Free)", page_icon="📊", layout="wide")
st.title("📊 Crypto Social Strength — Free Version (No API Keys)")

symbol = st.text_input("Enter coin ticker (e.g., BTC, ETH, SOL)", "BTC").upper()

use_tweet_scrape = st.checkbox("Scrape recent tweets for sentiment (optional, may fail)", value=False)

if st.button("Analyze"):
    asset = get_lunarcrush_data(symbol)
    if not asset:
        st.error("Could not fetch data from LunarCrush.")
    else:
        tweet_sentiment = None
        if use_tweet_scrape:
            if SCRAPE_AVAILABLE:
                st.info("Scraping tweets…")
                tweet_sentiment = scrape_twitter_sentiment(symbol)
            else:
                st.warning("snscrape not installed — skipping tweet scrape.")

        score = compute_social_strength(asset, tweet_sentiment)
        st.metric("Social Strength Score", f"{score} / 100")

        # Show key metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Social Volume (Galaxy Score)", asset.get("galaxy_score", "N/A"))
        col2.metric("Avg Sentiment", round(asset.get("average_sentiment", 0)*100, 1))
        col3.metric("Influencer Count", asset.get("influencer_count", "N/A"))

        # Historical social volume
        if "timeSeries" in asset:
            df = pd.DataFrame(asset["timeSeries"])
            if not df.empty:
                df["time"] = pd.to_datetime(df["time"], unit="s")
                st.line_chart(df.set_index("time")["social_volume"])
