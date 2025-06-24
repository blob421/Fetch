About Fetch
============


Introduction
----------------

Fetch is a script designed to collect market-related data on cryptocurrencies, including 
Bitcoin and Ethereum. It uses an SQLite3 database for storage and excels at time consistency. 
By leveraging the power of asynchronous programming, Fetch efficiently harnesses threading to
deliver precise and optimized operations.

How it works
----------------

Fetch is an asynchronous program running through a main event loop. It uses the `asyncio` 
module to run tasks concurrently. This means the program continuously executes functions 
instead of processing them sequentially. Timestamps are also based on UTC to avoid timezone or
DST discrepancies.

How it fetches and writes to the database
-----------------------------------------------

There are three main functions responsible for fetching data:

 - `fetch_coindata()`,  `fetch_marketdata()`,  and  `fetch_sentiment()`. 

They all use a core function named `fetch_data_with_retry()` to handle their requests. They are 
also managed by three scheduled coroutines:

 - `fetch_stack()`,  `hourly_sentiment()`  and  `daily_sentiment()`.
    
`fetch_sentiment()` is the only fetching function that does not write to the database directly.
Instead, it fetches data and stores it globally to save ressources. Values are then passed 
through the `fetch_marketdata()` function. 


Timing Accuracy and System Clock Drift
----------------------------------------

Although this application uses a precisely calibrated scheduler based on time.monotonic(), you
may occasionally observe discrepancies between expected and actual timestamp values in the 
database. This is a consequence of how operating systems handle wall-clock time. Most systems 
are not as precise as an atomic clock in terms of measurement accuracy and must ideally re-sync
with NTP once a day to keep track of real time. 

For this purpose, Fetch uses a hybrid between monotonic time and regular time and is equipped
with an anti-drift mechanism. Once NTP updates, Fetch calculates the difference and 
automatically adjusts itself for the next round. 

For instance, if NTP corrects the system clock by moving it back by one second, Fetch will wait 
an additional second in the next round to compensate.


Fail-safe mechanisms
--------------------------

`fetch_data_with_retry()` is the core function responsible for making requests. It allows for 
up to five retries before giving up. If an attempt to fetch fails, it notifies the user. This 
prevents outdated or biased data from being inserted into the database and instead writes
`NULL` values. By using an hybrid of time.monotonic and datetime.now(), Fetch ensures time 
measurements are always accurate. Moreover, time measurements are always proceeded before `fetch_data_with_retry()`,
ensuring time consistency even if attempts to fetch were made.

Database operations
------------------------

The database consists of three tables: `bitcoin_data`, `eth_data`, and `market_data`.
The database runs in **WAL (Write-Ahead Logging) mode**, allowing for efficient chunked data movements 
and optimizing performance. Time measures are taken in a DateTime format and stored in the column
"date" for each tables. These columns are indexed by default for faster access.

