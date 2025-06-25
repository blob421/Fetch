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

   - 1. Navigate to the directory where `requirements.txt` is located. 
        e.g. cd /desktop/project

   - 2. pip install -r requirements.txt 
  

Using the scheduler to start Fetch
------------------------------------

There is two options to start Fetch:

1. **Direct Start**: Run `fetch.py` to begin immediately.
2. **Scheduled Start**: Run `scheduled_start.py` to launch Fetch at a specific time.

The later will prompt the user for a precise launch time.

**Example — to start Fetch at 20:05:00.00:**

1. Enter the hour : `"20"`
2. Enter the minute : `"5"` or `"05"`
3. Enter the second : `"0"`
4. Enter the microsecond : `"0"`
