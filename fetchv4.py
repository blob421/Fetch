# Price api
import sqlite3
import requests
import json
import time
import datetime

with open('ApiKey.txt', 'r') as file:
    headers = json.load(file)


def fetch_data_with_retry(url, headers, max_retries=5, wait_time=10):
   
   for attempt in range(max_retries):
     
     try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
     except requests.exceptions.RequestException as e:
        print(f'Attempt{attempt + 1} failed: {e}')
      
        time.sleep(wait_time)
   print("Max retries reached. Failed to fetch data.")
   return None 
      

def fetch_marketdata():
    
 url = "https://openapiv1.coinstats.app/markets"
 url2 = 'https://api.alternative.me/fng/?limit=2&format=json'
 date_time = datetime.datetime.now()

 try:
    response = fetch_data_with_retry(url, headers)
    response2 = fetch_data_with_retry(url2, None)
    fng_value, fng_name = None, None  
    
    if response2 and "data" in response2 and response2["data"]:
       fng_value = response2['data'][0]['value']
       fng_name = response2['data'][0]['value_classification']
       
    if response is None and response2 is None:
       print('Data not fetched, both api failed')
       return
   
    

    with sqlite3.connect('crypto_datav2.sqlite') as conn:
        cursor = conn.cursor() 
        
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor.execute('''CREATE TABLE IF NOT EXISTS market_data 
                           (date DATETIME,
                           marketCap INTEGER, 
                           volume INTEGER, 
                           btcDominance DECIMAL(20, 2),
                           marketCapChange DECIMAL(20, 2),
                           volumeChange DECIMAL(20, 2),
                           btcDominanceChange DECIMAL(20, 2),
                           fear_greed_value INTEGER,
                           fear_greed_name VARCHAR(20))''')
            
        cursor.execute('CREATE INDEX idx_market_data_date ON market_data(date);')
       
        data = response
            
        marketCap = data.get("marketCap", None) if data else None
        volume = data.get("volume", None) if data else None
        btcDominance = data.get("btcDominance", None) if data else None
        marketCapChange = data.get("marketCapChange", None) if data else None    
        volumeChange = data.get("volumeChange", None) if data else None
        btcDominanceChange = data.get("btcDominanceChange", None) if data else None
        date = date_time
 
 except json.JSONDecodeError as e:
    print(f'Json decode error: {e}')
    return
 except (IndexError, KeyError) as e:
    print(f'Element not in json: {e}')
    return
 except Exception as e:
    print(f'Unexpected error : {e}')
    return
        
      
      
 try:
   cursor.executemany('''INSERT INTO market_data (date, marketCap, volume, btcDominance,
   marketCapChange, volumeChange, btcDominanceChange, fear_greed_value , fear_greed_name)
   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', [(date, marketCap, volume,
   btcDominance, marketCapChange, volumeChange , btcDominanceChange, fng_value, fng_name)])
        
   conn.commit()
   cursor.close()
       
 except sqlite3.Error as e:
           print(f'Database insert error: {e}')
 
  

def fetch_bitcoin():    
   
 url = "https://openapiv1.coinstats.app/coins?currency=USD&name=bitcoin&symbol=BTC"
 date_time = datetime.datetime.now()
   
 try:
   response = fetch_data_with_retry(url, headers)

   if response is None:
      print('Api connexion error')
      return
  
   if "result" in response and len(response["result"]) > 0:
      price = response["result"][0]["price"]
      volume = response["result"][0]["volume"]
      marketCap = response["result"][0]["marketCap"]
      availableSupply = response["result"][0]["availableSupply"]
      totalSupply = response["result"][0]["totalSupply"]
      fullyDilutedValuation = response["result"][0]["fullyDilutedValuation"]
      priceChange1h = response["result"][0]["priceChange1h"]
      priceChange1d = response["result"][0]["priceChange1d"]
      priceChange1w = response["result"][0]["priceChange1w"]
  
   else:
      price = None
      volume = None
      marketCap = None
      availableSupply = None
      totalSupply = None
      fullyDilutedValuation = None
      priceChange1h = None
      priceChange1d = None
      priceChange1w = None
   
   with sqlite3.connect('crypto_datav2.sqlite') as conn:
      cursor = conn.cursor()
      conn.execute("PRAGMA journal_mode=WAL;")
      cursor.execute('''CREATE TABLE IF NOT EXISTS bitcoin_data
                      (date DATETIME,
                      price DECIMAL(20, 2),
                      volume DECIMAL(20, 2),
                      marketCap DECIMAL(20, 2),
                      availableSupply DECIMAL(20, 2),
                      totalSupply INTEGER,
                      fullyDilutedValuation DECIMAL(20, 2),
                      priceChange1h DECIMAL(20, 2),
                      priceChange1d DECIMAL(20, 2),
                      priceChange1w DECIMAL(20, 2))''')
      
      cursor.execute('CREATE INDEX idx_btc_data_date ON bitcoin_data(date);')

 except json.JSONDecodeError as e:
    print(f'Json decode error: {e}')
    return
 except (IndexError, KeyError) as e:
    print(f'Element not in json: {e}')
    return
 except Exception as e:
    print(f'Unexpected error : {e}')
    return
 
 
 date = date_time
      
      
 try:
   cursor.executemany('''INSERT INTO bitcoin_data (date, price, volume, marketCap,
    availableSupply, totalSupply, fullyDilutedValuation, priceChange1h,
    priceChange1d, priceChange1w)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', [(date, price, volume, marketCap,
    availableSupply, totalSupply, fullyDilutedValuation, priceChange1h, priceChange1d,
    priceChange1w)])
                       
   conn.commit()
   cursor.close()
      
 except sqlite3.Error as e:
         print(f'Database insert error: {e}')
 
 

def fetch_eth():
 
 url = "https://openapiv1.coinstats.app/coins?currency=USD&name=ethereum&symbol=ETH"
 date_time = datetime.datetime.now()

 
 try:
   
   response = fetch_data_with_retry(url, headers)
   
   if response is None:
      print('Api connexion error')
      return
   
   if "result" in response and len(response["result"]) > 0:
      price = response["result"][0]["price"]
      volume = response["result"][0]["volume"]
      marketCap = response["result"][0]["marketCap"]
      availableSupply = response["result"][0]["availableSupply"]
      totalSupply = response["result"][0]["totalSupply"]
      fullyDilutedValuation = response["result"][0]["fullyDilutedValuation"]
      priceChange1h = response["result"][0]["priceChange1h"]
      priceChange1d = response["result"][0]["priceChange1d"]
      priceChange1w = response["result"][0]["priceChange1w"]
  
   else:
      price = None
      volume = None
      marketCap = None
      availableSupply = None
      totalSupply = None
      fullyDilutedValuation = None
      priceChange1h = None
      priceChange1d = None
      priceChange1w = None
   
   with sqlite3.connect('crypto_datav2.sqlite') as conn:
    
      cursor = conn.cursor()
      conn.execute("PRAGMA journal_mode=WAL;")
      
      cursor.execute('''CREATE TABLE IF NOT EXISTS eth_data
                      (date DATETIME,
                      price DECIMAL(20, 2),
                      volume DECIMAL(20, 2),
                      marketCap DECIMAL(20, 2),
                      availableSupply DECIMAL(20, 2),
                      totalSupply INTEGER,
                      fullyDilutedValuation DECIMAL(20, 2),
                      priceChange1h DECIMAL(20, 2),
                      priceChange1d DECIMAL(20, 2),
                      priceChange1w DECIMAL(20, 2))''')
 
      cursor.execute('CREATE INDEX idx_eth_data_date ON eth_data(date);')

 
 except json.JSONDecodeError as e:
    print(f'Json decode error: {e}')
    return
 except (IndexError, KeyError) as e:
    print(f'Element not in json: {e}')
    return
 except Exception as e:
    print(f'Unexpected error : {e}')
    return
 
 date = date_time
     
 try:
   cursor.executemany('''INSERT INTO eth_data (date, price, volume, marketCap,
    availableSupply, totalSupply, fullyDilutedValuation, priceChange1h,
    priceChange1d, priceChange1w)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', [(date, price, volume, marketCap,
    availableSupply, totalSupply, fullyDilutedValuation, priceChange1h, priceChange1d,
    priceChange1w)])
                       
   conn.commit()
   cursor.close()
      
 except sqlite3.Error as e:
         print(f'Database insert error: {e}')


while True:      
  
  fetch_marketdata()
  fetch_bitcoin()
  fetch_eth()
  time.sleep(300)















