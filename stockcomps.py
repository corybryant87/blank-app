# Let's try a different approach with error handling and data validation
import yfinance as yf
import pandas as pd

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Get current price from history
        hist = stock.history(period='1d')
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
        
        info = stock.info
        
        return {
            'Ticker': ticker,
            'Name': info.get('shortName', 'N/A'),
            'Price': current_price,
            'Market Cap': info.get('marketCap', None),
            'P/E Ratio': info.get('trailingPE', None),
            'EPS': info.get('trailingEps', None),
            'Volume': info.get('volume', None)
        }
    except Exception as e:
        print(f"Error with {ticker}: {e}")
        return None

# Test with three stocks
tickers = ['AAPL', 'MSFT', 'GOOGL']
print("Fetching current stock data...")

data = []
for ticker in tickers:
    info = get_stock_info(ticker)
    if info:
        data.append(info)

if data:
    df = pd.DataFrame(data)
    df.set_index('Ticker', inplace=True)
    
    # Format market cap to billions
    if 'Market Cap' in df.columns:
        df['Market Cap'] = df['Market Cap'].apply(lambda x: f"${x/1e9:.2f}B" if pd.notnull(x) else 'N/A')
    
    # Format price to 2 decimal places
    if 'Price' in df.columns:
        df['Price'] = df['Price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else 'N/A')
    
    print("\
Stock Comparison:")
    print(df)
else:
    print("Could not retrieve data for any of the specified stocks.")