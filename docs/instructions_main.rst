Getting started
===============

Setting up your API key
-----------------------

To use Fetch, you need an API key. Follow this link and create an account on Coinstats Open API:

https://openapi.coinstats.app/

Your API key will be on your dashboard. Once you are done, go to the file named ApiKey.txt in the root folder of the repository.
Open it and replace this field with your key : YOUR_API_KEY_HERE 


Required dependencies
----------------------
This program requires Python.

- Download the latest version of Python and ensure the "Add Python to PATH" option is checked 
  during installation.

- Required dependencies are included in requirements.txt and must be installed
  in your python environment before proceeding.

- With your python environment activated in the terminal:

   1. Navigate to the directory where `requirements.txt` is located. 
        e.g. cd /desktop/project

   2. Activate your virtual enviroment if you have one 

   3. pip install -r requirements.txt


Scheduling on startup
-------------------------
 1. Make a batch file where fetch.py lives (It should activate your virtual environment and run fetch.py).

 2. Save and add a shortcut to this file to your startup folder(windows)

 3. Fetch will wait and resume on startup to stay aligned with current data timestamps.


Correcting missing data 
---------------------------
- To interpolate missing row , run correct_tables.py

 1. This script will interpolate rows that have NULL values.

 2. It will also add rows for missed intervals.
   

   
  

