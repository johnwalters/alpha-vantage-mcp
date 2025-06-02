# Alpha Vantage API Documentation

Alpha Vantage provides a wide array of APIs categorized into the following groups:

1. Core Time Series Stock Data APIs  
2. US Options Data APIs  
3. Alpha Intelligence™  
4. Fundamental Data  
5. Physical and Digital/Crypto Currencies  
6. Commodities  
7. Economic Indicators  
8. Technical Indicators  

---

## Core Time Series Stock Data APIs

These APIs provide OHLCV data in different timeframes.

- **Intraday Data**  
  Example: [Intraday Data for IBM](https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo)

- **Daily Data**  
  Example: [Daily Data for IBM](https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo)

- **Daily Adjusted Data**  
  Example: [Daily Adjusted Data for IBM](https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&apikey=demo)

- **Weekly Data**  
  Example: [Weekly Data for IBM](https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=demo)

- **Monthly Data**  
  Example: [Monthly Data for IBM](https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol=IBM&apikey=demo)

- **Quote Endpoint**  
  Example: [Quote for IBM](https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=demo)

- **Symbol Search**  
  Example: [Search for "Tesla"](https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=tesla&apikey=demo)

- **Market Status**  
  Example: [Market Status](https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=demo)

---

## US Options Data APIs

Access to real-time and historical U.S. options data.

- **Realtime Options**  
  Example: [Realtime Options for IBM](https://www.alphavantage.co/query?function=REALTIME_OPTIONS&symbol=IBM&apikey=demo)

- **Historical Options**  
  Example: [Historical Options for IBM on 2017-11-15](https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol=IBM&date=2017-11-15&apikey=demo)

---

## Alpha Intelligence™

Insights from news sentiment, earnings call transcripts, and insider transactions.

- **News & Sentiments**  
  Example: [News Sentiment for IBM](https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=IBM&apikey=demo)

- **Earnings Call Transcripts**  
  Example: [Earnings Call Transcript for IBM](https://www.alphavantage.co/query?function=EARNINGS_CALL_TRANSCRIPT&symbol=IBM&apikey=demo)

- **Top Gainers & Losers**  
  Example: [Top Gainers & Losers](https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey=demo)

- **Insider Transactions**  
  Example: [Insider Transactions for IBM](https://www.alphavantage.co/query?function=INSIDER_TRANSACTIONS&symbol=IBM&apikey=demo)

---

## Fundamental Data

Company financials, earnings, and other fundamentals.

- **Company Overview**  
  Example: [Company Overview for IBM](https://www.alphavantage.co/query?function=OVERVIEW&symbol=IBM&apikey=demo)

- **Income Statement**  
  Example: [Income Statement for IBM](https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=IBM&apikey=demo)

- **Balance Sheet**  
  Example: [Balance Sheet for IBM](https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=IBM&apikey=demo)

- **Cash Flow**  
  Example: [Cash Flow for IBM](https://www.alphavantage.co/query?function=CASH_FLOW&symbol=IBM&apikey=demo)

- **Earnings**  
  Example: [Earnings for IBM](https://www.alphavantage.co/query?function=EARNINGS&symbol=IBM&apikey=demo)

- **Listing & Delisting Status**  
  Example: [Listing Status](https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo)

- **Earnings Calendar**  
  Example: [Earnings Calendar](https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&apikey=demo)

- **IPO Calendar**  
  Example: [IPO Calendar](https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey=demo)

---

## Physical and Digital/Crypto Currencies

Currency exchange and crypto data.

- **Currency Exchange Rate**  
  Example: [Exchange Rate USD to EUR](https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=EUR&apikey=demo)

- **Digital Currency Daily**  
  Example: [Daily Data for BTC/USD](https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=USD&apikey=demo)

---

## Commodities

Daily prices for commodities like crude oil and natural gas.

- **Crude Oil (WTI)**  
  Example: [Crude Oil WTI](https://www.alphavantage.co/query?function=WTI&apikey=demo)

- **Crude Oil (Brent)**  
  Example: [Crude Oil Brent](https://www.alphavantage.co/query?function=BRENT&apikey=demo)

- **Natural Gas**  
  Example: [Natural Gas](https://www.alphavantage.co/query?function=NATURAL_GAS&apikey=demo)