from ibkr_api import get_stock_quote, get_option_chain, get_option_quote

# Example: Get a stock quote
print("AAPL Stock Quote:")
print(get_stock_quote("AAPL"))

# Example: Get option chain for AAPL
print("\nAAPL Option Chain (expiries and strikes):")
chain = get_option_chain("AAPL")
print(chain)

# Example: Get a specific option quote (e.g., July 2024, $150 Call)
expiry = list(chain.keys())[0]  # Use the first available expiry
strikes = chain[expiry]['call'] if 'call' in chain[expiry] else chain[expiry]['put']
strike = strikes[0]  # Use the first available strike
print(f"\nAAPL Option Quote for {expiry} {strike}C:")
print(get_option_quote("AAPL", expiry, strike, "C"))
