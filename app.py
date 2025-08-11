import streamlit as st
import requests
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

# ---------------------
# Get social data from LunarCrush
# ---------------------
def get_lunarcrush_data(symbol):
    API_KEY = "tilgcg4ksygfkrjm2cp334kqhjme72p9gclfp593m"
url = f"https://lunarcrush.com/api/v2?data=assets&key={API_KEY}&symbol={symbol.upper()}&data_points=30"

    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    if "data" not in data or len(data["data"]) == 0:
        return None
    asset = data["data"][0]
    return asset

# ---------------------
# Score calculation
# ---------------------
def compute_social_strength(asset):
    vol_score = asset.get("galaxy_score", 50) / 100
    sentiment_score = asset.get("average_sentiment", 0.5)
    engagement_score = asset.get("social_score", 50) / 100000
    engagement_score = min(1.0, engagement_score)

    influencer_score = asset.get("influencer_count", 0) / 50
    influencer_score = min(1.0, influencer_score)

    dominance_score = asset.get("social_dominance", 0) / 100

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
st.title("📊 Crypto Social Strength — Free Version (No Twitter Scraping)")

symbol = st.text_input("Enter coin ticker (e.g., BTC, ETH, SOL)", "BTC").upper()

if st.button("Analyze"):
    asset = get_lunarcrush_data(symbol)
    if not asset:
        st.error("Could not fetch data from LunarCrush.")
    else:
        score = compute_social_strength(asset)
        st.metric("Social Strength Score", f"{score} / 100")

        col1, col2, col3 = st.columns(3)
        col1.metric("Social Volume (Galaxy Score)", asset.get("galaxy_score", "N/A"))
        col2.metric("Avg Sentiment", round(asset.get("average_sentiment", 0)*100, 1))
        col3.metric("Influencer Count", asset.get("influencer_count", "N/A"))

        if "timeSeries" in asset:
            df = pd.DataFrame(asset["timeSeries"])
            if not df.empty:
                df["time"] = pd.to_datetime(df["time"], unit="s")
                st.line_chart(df.set_index("time")["social_volume"])
