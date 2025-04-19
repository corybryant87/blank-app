
# Streamlit app for Stock Comparison
st.title('Stock Comparison Tool')
st.write('Enter three stock tickers to compare their financial metrics.')

# Input fields for tickers
col1, col2, col3 = st.columns(3)
with col1:
    ticker1 = st.text_input('First Stock Ticker', value='AAPL').upper()
with col2:
    ticker2 = st.text_input('Second Stock Ticker', value='MSFT').upper()
with col3:
    ticker3 = st.text_input('Third Stock Ticker', value='GOOG').upper()

if ticker1 and ticker2 and ticker3:
    # Get data for all tickers
    data_list = []
    for ticker in [ticker1, ticker2, ticker3]:
        data = get_financial_data(ticker)
        if data:
            data_list.append(data)
    
    if len(data_list) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(data_list)
        df.set_index('Ticker', inplace=True)
        
        # Display company names
        st.subheader('Companies Being Compared')
        for idx, row in df.iterrows():
            st.write(f"{idx}: {row['Company Name']}")
        
        # Remove Company Name column for display
        df_display = df.drop('Company Name', axis=1)
        
        # Format the dataframe
        st.subheader('Financial Metrics Comparison')
        st.dataframe(df_display.style.format("{:.2f}"))
        
        # Metrics for visualization
        viz_metrics = [
            'Current Price', 'P/E Ratio', 'EPS', 'ROE (%)', 
            'Revenue Growth (%)', 'Profit Margin (%)', 
            'Market Cap (B)', '1Y Return (%)'
        ]
        
        # Create radar chart for selected metrics
        st.subheader('Comparative Analysis - Radar Chart')
        metrics_for_radar = ['P/E Ratio', 'ROE (%)', 'Revenue Growth (%)', 
                           'Profit Margin (%)', '1Y Return (%)']
        
        # Prepare data for radar chart
        fig = go.Figure()
        for company in df.index:
            values = df.loc[company, metrics_for_radar].fillna(0)
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metrics_for_radar,
                name=company
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(showticklabels=True, ticks='')),
            showlegend=True
        )
        st.plotly_chart(fig)
        
        # Bar charts for selected metrics
        st.subheader('Individual Metrics Comparison')
        for metric in viz_metrics:
            if metric in df.columns:
                fig = px.bar(
                    df.reset_index(), 
                    x='Ticker', 
                    y=metric,
                    title=f'{metric} Comparison',
                    text=df[metric].round(2)
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig)
        
        # Investment Analysis Summary
        st.subheader('Investment Analysis Summary')
        summary_text = []
        
        # Analyze each metric
        for metric in df_display.columns:
            values = df_display[metric].dropna()
            if not values.empty:
                if metric in ['P/E Ratio', 'P/B Ratio', 'P/S Ratio', 'EV/EBITDA', 'Debt/Equity']:
                    best = values.idxmin()
                    summary_text.append(f"{metric}: {best} leads with lowest value of {values[best]:.2f}")
                else:
                    best = values.idxmax()
                    summary_text.append(f"{metric}: {best} leads with highest value of {values[best]:.2f}")
        
        st.text_area('Key Findings', '\
'.join(summary_text), height=300)
        
        st.write('Note: This tool provides basic financial metrics comparison. '
                'Please conduct thorough research before making investment decisions.')
