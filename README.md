A simple script that collects data on Bitcoin, Ethereum and the market every 5 minutes from the Coinstats API. Also collects sentiment data from Alternative.

You'll need to insert your API-KEY from Coinstats in Api_Key.txt . You can get one on this site :  https://openapi.coinstats.app/login

The required modules have been included in requirements.txt , so to install them just :
"pip install -r requirements.txt" in your environment.

Copy the repository, install the dependencies and see the magic unfold by launching fetchv4.py
All data will be stored in a database as a time-series database named crypto_datav2.sqlite 
