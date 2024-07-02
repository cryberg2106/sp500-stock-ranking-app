import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# URL to fetch S&P 500 stock list
url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
s_and_p_500 = pd.read_csv(url)

# Function to fetch and calculate required metrics for multiple stocks
def get_stock_data(tickers):
    stocks = yf.download(tickers, period="1y")
    data = {}

    for ticker in tickers:
        try:
            hist = stocks['Close'][ticker]
            if hist.isnull().all():
                continue

            # Calculate 12-month price change (Momentum)
            price_change = ((hist[-1] - hist[0]) / hist[0]) * 100

            # Calculate standard deviation of daily returns (Volatility)
            daily_returns = hist.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized volatility

            stock_info = yf.Ticker(ticker).info

            pe_ratio = stock_info.get('trailingPE', None)
            pb_ratio = stock_info.get('priceToBook', None)
            ps_ratio = stock_info.get('priceToSalesTrailing12Months', None)
            roe = stock_info.get('returnOnEquity', None)
            roa = stock_info.get('returnOnAssets', None)
            debt_to_equity = stock_info.get('debtToEquity', None)

            data[ticker] = {
                'Price_Change': price_change,
                'Volatility': volatility,
                'PE_Ratio': pe_ratio,
                'PB_Ratio': pb_ratio,
                'PS_Ratio': ps_ratio,
                'ROE': roe,
                'ROA': roa,
                'Debt_to_Equity': debt_to_equity,
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    
    return data

# Function to calculate scores and rankings
def calculate_scores(data):
    df = pd.DataFrame(data).T

    for metric in ['Price_Change', 'Volatility', 'PE_Ratio', 'PB_Ratio', 'PS_Ratio', 'ROE', 'ROA', 'Debt_to_Equity']:
        df[f'{metric}_Norm'] = (df[metric] - df[metric].min()) / (df[metric].max() - df[metric].min())

    df['Value_Score'] = df[['PE_Ratio_Norm', 'PB_Ratio_Norm', 'PS_Ratio_Norm']].mean(axis=1)
    df['Quality_Score'] = df[['ROE_Norm', 'ROA_Norm', 'Debt_to_Equity_Norm']].mean(axis=1)
    df['Momentum_Score'] = df['Price_Change_Norm']
    df['Volatility_Score'] = df['Volatility_Norm']

    df['Composite_Score'] = (0.3 * df['Value_Score'] + 0.3 * df['Quality_Score'] + 0.3 * df['Momentum_Score'] + 0.1 * df['Volatility_Score'])
    df['Rank'] = df['Composite_Score'].rank(ascending=False)

    return df.sort_values(by='Rank')

# Streamlit app
st.title('Vantage Capital's S&P 500 Stock Ranking')
st.write("This ranks S&P 500 stocks based on their value, quality, momentum, and volatility metrics. Data is updated daily. A high rank indicates that a stock is rated higher on the four metrics.")

tickers = s_and_p_500['Symbol'].tolist()
data = get_stock_data(tickers)
df_sorted = calculate_scores(data)

# Cache the data for 24 hours to prevent multiple fetches within a day
@st.cache_data(ttl=86400)
def get_cached_data():
    return df_sorted

df_sorted = get_cached_data()

# Display the DataFrame
st.dataframe(df_sorted)

# Add some interactivity: Select a stock to see detailed information
selected_stock = st.selectbox('Select a stock to see details:', df_sorted.index)

if selected_stock:
    stock = yf.Ticker(selected_stock)
    info = stock.info
    st.write(f"**{info['longName']} ({selected_stock})**")
    st.write(f"**Sector:** {info['sector']}")
    st.write(f"**Industry:** {info['industry']}")
    st.write(f"**Market Cap:** {info['marketCap']}")
    st.write(f"**Trailing P/E:** {info['trailingPE']}")
    st.write(f"**Forward P/E:** {info['forwardPE']}")
    st.write(f"**Return on Equity:** {info['returnOnEquity'] * 100:.2f}%")
    st.write(f"**12-month Price Change:** {df_sorted.loc[df_sorted.index == selected_stock, 'Price_Change'].values[0]:.2f}%")
    st.write(f"**Volatility:** {df_sorted.loc[df_sorted.index == selected_stock, 'Volatility'].values[0]:.2f}%")
    st.write(f"**Composite Score:** {df_sorted.loc[df_sorted.index == selected_stock, 'Composite_Score'].values[0]:.2f}")
