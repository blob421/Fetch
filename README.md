Fetch is a script designed to collect market-related data on cryptocurrencies, including Bitcoin and Ethereum. It uses an SQLite3 database for storage and excels at time consistency. By leveraging the power of asynchronous programming, Fetch efficiently harnesses threading to deliver precise and optimized operations.

Documentation is available at this address: 
https://fetch-documentation.readthedocs.io/en/latest/instructions_main.html


Fetch 
===========================

- fetch.py : Start or resume collecting data 

- correct_tables.py: Interpolate and fill missing rows across all tables

- Analyze and remove duplicates.py : Get a report on timestamps and gaps. Detect and remove duplicates.


** It is recommended to run correct_tables.py before removing any duplicates 
for data integrity **

Data
=============================
Data will be stored in the same folder as fetch.py, in a file named crypto_data.sqlite.

Store old databases as crypto_data_p1 , p2 into /Fetch/datasets for ML training.


Prediction models
=============================

Datasets : 

The actual dataset used for predictions is the one in /Fetch/ and used by the fetch process .

Training:
---------------

1. Either train a neural model by running train_neural.py or a logistic regression model with train_logi_regr.py

2. If you chose to train a neural network , you can either train on a single dataset or mix a selection.

 - Ajust the percentile value of load__mixed_dataset() in utils.py to reduce noise from small movements.
 - Use a mean and std that is based on your biggest dataset to enforce a regime.



Inference:
---------------
1. Simply select a weight from the list when asked .

- test_logi_regr.py will predict every 5 minutes based on your logistic regression model.

- test_neural.py will sync with your database and make predictions while building accuracy and a price score. 


Bots:
------------
1. You need to enter your own api key and secret key in each bots .
2. Ajust probability tresholds in bot scripts to fit your model .
3. These bots only support neural models.

- mexc_controller_spot.py is meant for spot trading so it only buys and clear orders every 5 minutes.
- mexc_controller.py is meant for futures trading (use at your own risk)
- kraken_spot_bot is unfinished due to high trading fees on this platform but should work nevertheless.





