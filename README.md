Fetch is a script designed to collect market-related data on cryptocurrencies, including Bitcoin and Ethereum. It uses an SQLite3 database for storage and excels at time consistency. By leveraging the power of asynchronous programming, Fetch efficiently harnesses threading to deliver precise and optimized operations.

Documentation is available at this address: 
https://fetch-documentation.readthedocs.io/en/latest/index.html


Scripts : 
===========================

- fetch.py : Start or resume collecting data 

- correct_tables.py: Interpolate and fill missing rows across all tables

- Analyze and remove duplicates.py : Get a report on timestamps and gaps. Detect and remove duplicates.


** It is recommended to run correct_tables.py before removing any duplicates 
for data integrity **


Data will be located at /crypto_data.sqlite



