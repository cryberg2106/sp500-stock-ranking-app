import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

# Fetch data from Yahoo Finance
@st.cache
def fetch_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        'longName': info.get('longName', 'N/A'),
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'marketCap': info.get('marketCap', 0),
        'trailingPE': info.get('trailingPE', 0),
        'priceToBook': info.get('priceToBook', 0),
        'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months', 0),
        'returnOnEquity': info.get('returnOnEquity', 0),
        'returnOnAssets': info.get('returnOnAssets', 0),
        'debtToEquity': info.get('debtToEquity', 0),
        'description': info.get('longBusinessSummary', 'N/A'),
        'sector': info.get('sector', 'N/A')
    }

# Define a function to fetch data for all S&P 500 stocks
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    return df['Symbol'].tolist(), df[['Symbol', 'Security', 'GICS Sector']]

# Fetch S&P 500 tickers
tickers, stock_info = get_sp500_tickers()

# Create an empty DataFrame to store stock data
data = []

# Fetch data for each stock
for ticker in tickers:
    info = fetch_data(ticker)
    data.append([
        ticker,
        info['longName'],
        info['sector'],
        info['trailingPE'],
        info['priceToBook'],
        info['priceToSalesTrailing12Months'],
        info['returnOnEquity'],
        info['returnOnAssets'],
        info['debtToEquity'],
        info['description']
    ])

# Convert the data into a DataFrame
df = pd.DataFrame(data, columns=[
    'Ticker', 'Name', 'Sector', 'P/E Ratio', 'P/B Ratio', 'P/S Ratio', 'ROE', 'ROA', 'Debt to Equity', 'Description'
])

# Normalize metrics
df['P/E Ratio'] = (df['P/E Ratio'] - df['P/E Ratio'].min()) / (df['P/E Ratio'].max() - df['P/E Ratio'].min())
df['P/B Ratio'] = (df['P/B Ratio'] - df['P/B Ratio'].min()) / (df['P/B Ratio'].max() - df['P/B Ratio'].min())
df['P/S Ratio'] = (df['P/S Ratio'] - df['P/S Ratio'].min()) / (df['P/S Ratio'].max() - df['P/S Ratio'].min())
df['ROE'] = (df['ROE'] - df['ROE'].min()) / (df['ROE'].max() - df['ROE'].min())
df['ROA'] = (df['ROA'] - df['ROA'].min()) / (df['ROA'].max() - df['ROA'].min())
df['Debt to Equity'] = (df['Debt to Equity'] - df['Debt to Equity'].min()) / (df['Debt to Equity'].max() - df['Debt to Equity'].min())

# Calculate scores
df['Value Score'] = 0.5 * df['P/E Ratio'] + 0.5 * df['P/B Ratio']
df['Quality Score'] = 0.5 * df['ROE'] + 0.5 * df['ROA']
df['Momentum Score'] = df['P/S Ratio']
df['Volatility Score'] = df['Debt to Equity']

# Composite score
df['Composite Score'] = 0.3 * df['Value Score'] + 0.3 * df['Quality Score'] + 0.3 * df['Momentum Score'] + 0.1 * df['Volatility Score']

# Calculate rank for each factor and composite score
df['Value Rank'] = df['Value Score'].rank(ascending=False).astype(int)
df['Quality Rank'] = df['Quality Score'].rank(ascending=False).astype(int)
df['Momentum Rank'] = df['Momentum Score'].rank(ascending=False).astype(int)
df['Volatility Rank'] = df['Volatility Score'].rank(ascending=False).astype(int)
df['Composite Rank'] = df['Composite Score'].rank(ascending=False).astype(int)

# Calculate rank in percentage terms
df['Rank'] = df['Composite Score'].rank(pct=True)
df['Rank Percentage'] = pd.cut(df['Rank'], bins=np.linspace(0, 1, 11), labels=[
    'Bottom 10%', 'Bottom 20%', 'Bottom 30%', 'Bottom 40%', 'Bottom 50%',
    'Top 50%', 'Top 40%', 'Top 30%', 'Top 20%', 'Top 10%'
])

# Drop unnecessary columns
df = df[['Composite Rank', 'Ticker', 'Name', 'Sector', 'Value Rank', 'Quality Rank', 'Momentum Rank', 'Volatility Rank', 'Rank Percentage', 'Description']]

# Streamlit app
st.title("S&P 500 Stock Ranking by Vantage Capital")

st.write("""
### Vantage Capital Quantitative Stock Selection Model

This model is built by Vantage Capital to rank stocks in the S&P 500 index using a quantitative approach. It combines four key factors to evaluate each stock:

- **Value**: Combines Price-to-Earnings (P/E) and Price-to-Book (P/B) ratios to gauge the stock's value.
- **Quality**: Uses Return on Equity (ROE) and Return on Assets (ROA) to measure the quality of the stock.
- **Momentum**: Reflects the stock's price momentum over a given period.
- **Volatility**: Assesses the stock's price volatility to understand its risk.

### Composite Score
The composite score is a weighted average of the four factors, providing a comprehensive measure to rank stocks.
""")

# Sector filter
selected_sector = st.selectbox("Select Sector", options=['All'] + list(df['Sector'].unique()))
if selected_sector != 'All':
    df = df[df['Sector'] == selected_sector]

# Display the DataFrame with clickable links
def create_clickable_link(ticker, name, description):
    link = f'<a href="#" onclick="alert(\'{description}\')">{ticker} - {name}</a>'
    return link

df['Ticker - Name'] = df.apply(lambda row: create_clickable_link(row['Ticker'], row['Name'], row['Description']), axis=1)

# Drop unnecessary columns
df = df[['Composite Rank', 'Ticker - Name', 'Sector', 'Value Rank', 'Quality Rank', 'Momentum Rank', 'Volatility Rank', 'Rank Percentage']]

# Display the DataFrame
st.write(df.to_html(escape=False), unsafe_allow_html=True)
