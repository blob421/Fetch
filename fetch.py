# Price api
import sqlite3
import requests
import json
import time
import datetime
import schedule


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


def fetch_sentiment():
 
 global fng_name, fng_value
 date_time = datetime.datetime.now() 
 fng_name, fng_value = None, None
 
 url2 = 'https://api.alternative.me/fng/?limit=2&format=json'

 try:
     
      response2 = fetch_data_with_retry(url2, None)
        
      if response2 and "data" in response2 and response2["data"]:
         fng_value = response2['data'][0]['value']
         fng_name = response2['data'][0]['value_classification']
         return
     
      if response2 is None:         
         print(f"{date_time} Couldn't get sentiment data, returning 'None' ")
         return
       
   
 except json.JSONDecodeError as e:
       print(f"{date_time} Couldn't get sentiment data, returning 'None' : {e}")
       return

 except (IndexError, KeyError) as e:
       print(f"{date_time} Couldn't get sentiment data, returning 'None' : {e}")
       return
            
 except Exception as e:
       print(f"{date_time} Couldn't get sentiment data, returning 'None' : {e}")
       return
       

def fetch_marketdata():
 global fng_name, fng_value
 
 marketCap = None
 volume = None
 btcDominance = None
 marketCapChange = None
 volumeChange = None
 btcDominanceChange = None

 url = "https://openapiv1.coinstats.app/markets"
 date_time = datetime.datetime.now()

 try:
    
    response = fetch_data_with_retry(url, headers)
          
    if response is None:
       print(f"{date_time} 'None' values registered (market)")
       pass
   
    
    with sqlite3.connect('crypto_data.sqlite') as conn:
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
            
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(date);')
       
        data = response
            
        marketCap = data.get("marketCap") if data else None
        volume = data.get("volume") if data else None
        btcDominance = data.get("btcDominance") if data else None
        marketCapChange = data.get("marketCapChange") if data else None    
        volumeChange = data.get("volumeChange") if data else None
        btcDominanceChange = data.get("btcDominanceChange") if data else None
        date = date_time
 
 except json.JSONDecodeError as e:
    print(f"{date_time} 'None' values registered (market): {e}")
    pass
 except (IndexError, KeyError) as e:
    print(f"{date_time} 'None' values registered (market): {e}")
    pass
 except Exception as e:
    print(f"{date_time} 'None' values registered (market): {e}")
    pass
        
      
      
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
 
 price = None
 volume = None
 marketCap = None
 availableSupply = None
 totalSupply = None
 fullyDilutedValuation = None
 priceChange1h = None
 priceChange1d = None
 priceChange1w = None
 
 url = "https://openapiv1.coinstats.app/coins?currency=USD&name=bitcoin&symbol=BTC"
 date_time = datetime.datetime.now()
   
 try:
   response = fetch_data_with_retry(url, headers)

   if response is None:
      print(f"{date_time} 'None' values registered (bitcoin)")
      pass
  
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

   
   with sqlite3.connect('crypto_data.sqlite') as conn:
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
      
      cursor.execute('CREATE INDEX IF NOT EXISTS idx_btc_data_date ON bitcoin_data(date);')

 except json.JSONDecodeError as e:
    print(f"{date_time} 'None' values registered (bitcoin) : {e}")
    pass
 except (IndexError, KeyError) as e:
    print(f"{date_time} 'None' values registered (bitcoin) : {e}")
    pass
 except Exception as e:
    print(f"{date_time} 'None' values registered (bitcoin) : {e}")
    pass
 
 
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
 
 price = None
 volume = None
 marketCap = None
 availableSupply = None
 totalSupply = None
 fullyDilutedValuation = None
 priceChange1h = None
 priceChange1d = None
 priceChange1w = None
 
 url = "https://openapiv1.coinstats.app/coins?currency=USD&name=ethereum&symbol=ETH"
 date_time = datetime.datetime.now()

 
 try:
   
   response = fetch_data_with_retry(url, headers)
   
   if response is None:
      print(f"{date_time} 'None' values registered (eth)")
      pass
   
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
    
   
   with sqlite3.connect('crypto_data.sqlite') as conn:
    
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
 
      cursor.execute('CREATE INDEX IF NOT EXISTS idx_eth_data_date ON eth_data(date);')

 
 except json.JSONDecodeError as e:
    print(f"{date_time} 'None' values registered (eth) : {e}")
    pass
 except (IndexError, KeyError) as e:
    print(f"{date_time} 'None' values registered (eth) : {e}")
    pass
 except Exception as e:
    print(f"{date_time} 'None' values registered (eth) : {e}")
    pass
 
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

## Main program

fng_value = None
fng_name = None
fetch_sentiment()

schedule.every().day.at("20:02").do(fetch_sentiment)
schedule.every().hour.do(fetch_sentiment)


while True:      
  
  schedule.run_pending()
  
  fetch_marketdata()
  fetch_bitcoin()
  fetch_eth()
  
  time.sleep(300)















