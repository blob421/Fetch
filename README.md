Fetch is a script designed to collect market-related data on cryptocurrencies, including Bitcoin and Ethereum. It uses an SQLite3 database for storage and excels at time consistency. By leveraging the power of asynchronous programming, Fetch efficiently harnesses threading to deliver precise and optimized operations.

Documentation is available at this address: 
https://fetch-documentation.readthedocs.io/en/latest/instructions_main.html


Starting Fetch 
===========================

- Fetch must be started from the "/Fetch" directory. The same applies for tools. In your terminal : 

  1. cd path/to/Fetch

  2. python fetch.py

  Data will be located at Fetch/crypto_data.sqlite



Scripts 
===========================

- fetch.py : Start or resume collecting data 

- correct_tables.py: Interpolate and fill missing rows across all tables

- Analyze and remove duplicates.py : Get a report on timestamps and gaps. Detect and remove duplicates.


** It is recommended to run correct_tables.py before removing any duplicates 
for data integrity **






