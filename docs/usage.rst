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
module to run tasks concurrently within the `main()` function. This means that the 
program continuously executes functions instead of processing them sequentially. Asynchronous 
operations occur inside the `gather()` function of the `main()` loop.

How it fetches and writes to the database
-----------------------------------------------
There are three main functions responsible for fetching the data: 

`fetch_coindata()`, `fetch_marketdata()`, and `fetch_sentiment()`.

All fetching functions use a core function named `fetch_data_with_retry()` to handle their
requests. 

`fetch_sentiment()` is the only fetching function that doesn't write to the database.
Instead, it fetches data and stores it globally to save ressources. 
This data is then written to the database through the `fetch_marketdata()` function.

The timing process
-----------------------
When starting `main()`, Fetch first checks the time and will delay execution by one minute using the 
`start_delay()` function if deemed necessary. This will prevent other asynchronous functions from 
conflicting with `daily_sentiment()` at 20:03.

Fetch then retrieves sentiment data once before proceeding. In `gather()`, the 
script will sets timers in three different functions: 

`fetch_stack()`, `daily_sentiment()`, and `hourly_sentiment()`.


`fetch_stack()` will runs once, and be set to every five minutes. `hourly_sentiment()` will be set to
one hour and two minutes, and to exactly one hour afterwards to prevent synchronization with
`fetch_stack()`. This avoids conflicts due to their asynchronous nature. `daily_sentiment()` 
will runs every day at 20:03, with the exact timing calculated using the `calculate_time()` 
function. 

Fail-safe mechanisms
--------------------------
`fetch_data_with_retry()` is the core function responsible for making requests. It allows for 
up to five retries before giving up. If an attempt to fetch fails, it notifies the user. This 
prevents outdated or biased data from being inserted into the database and instead writes
`NULL` values. Fetch can also compensates for any accumulated time-overhead by executing its
`fetch_stack()` function sooner. It ensures time measurements are always taken at the same exact 
second for every interval. Moreover, time measurements are always proceeded before `fetch_data_with_retry()`,
ensuring consistency even if attempts to fetch were made.

Database operations
------------------------
The database consists of three tables: `bitcoin_data`, `eth_data`, and `market_data`.
The database runs in **WAL (Write-Ahead Logging) mode**, allowing for efficient chunked data movements 
and optimizing performance. Time measures are taken in a DateTime format and stored in the column
"date" for each tables. These columns are indexed by default for faster access.

