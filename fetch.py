import sqlite3
import json
import datetime
import asyncio
import aiohttp



with open('ApiKey.txt', 'r') as file:   #Reads api-key from file 
    headers = json.load(file)



async def fetch_data_with_retry(url, headers, max_retries=5, wait_time=10):
   """Main function responsible for fetching data. Includes a retry mechanism 
      to handle errors and returns a parsed JSON response as a dictionary.
   """
   
   for attempt in range(max_retries):
     
     try:
        async with aiohttp.ClientSession() as session:
           async with session.get(url, headers=headers) as response:
             response.raise_for_status()
             return await response.json()
    
     except aiohttp.ClientError as e:
        print(f'Attempt{attempt + 1} failed: {e}')
        await asyncio.sleep(wait_time)
   
   print("Max retries reached. Failed to fetch data.")
   return None 



async def fetch_sentiment():
 """Function that fetches sentiment data and stores it globally.
    fng_name and fng_value will be set to "None" in case of failure
    and the user will be notified. 
 """
 global fng_name, fng_value
 date_time = datetime.datetime.now() 
 fng_name, fng_value = None, None

 url2 = 'https://api.alternative.me/fng/?limit=2&format=json'

 try:
      
      response2 = await fetch_data_with_retry(url2, None)

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
       


async def fetch_marketdata():
 """Fetches market data and writes it to the database.
    Values will be set to "None" in case of failure and the user will be notified.
 """
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
    
    response = await fetch_data_with_retry(url, headers)
          
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
   
       
 except sqlite3.Error as e:
           print(f'Database insert error: {e}')
 
 finally:
   cursor.close()
 


async def fetch_bitcoin():    
 """Fetches bitcoin data and writes it to the database.
    Values will be set to "None" in case of failure and the user will be notified.
 """
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
   response = await fetch_data_with_retry(url, headers)

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
   
      
 except sqlite3.Error as e:
         print(f'Database insert error: {e}')
 
 finally:
   cursor.close()
 


async def fetch_eth():
 """Fetches eth data and writes it to the database.
    Values will be set to "None" in case of failure and the user will be notified.
 """
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
   
   response = await fetch_data_with_retry(url, headers)
   
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
      
 except sqlite3.Error as e:
         print(f'Database insert error: {e}')
 
 finally:
   cursor.close()



def calculate_time():
 """Calculates the time left until 20:02 (until Alternative updates), returns seconds"""
 time_now = datetime.datetime.now()
 target_time = datetime.datetime.now().replace(hour=20, minute=2)
 
 if time_now > target_time:                   
    target_time += datetime.timedelta(days=1)
 
 return (target_time - time_now).total_seconds()


## Main program

fng_value = None    #Initializing global sentiment, market_data will use it 
fng_name = None


async def hourly_sentiment():
   """Fetches sentiment data every hours"""
   while True:
      await asyncio.sleep(3600)
      await fetch_sentiment()


async def daily_sentiment():
   """Fetches sentiment data every day at 20:02"""
   while True:
      sleeptime = calculate_time()
      await asyncio.sleep(sleeptime)
      await fetch_sentiment()
      
      
async def fetch_stack():
   """Concurrently fetches data on btc, eth and the market"""
   while True:
     asyncio.create_task(fetch_marketdata())
     asyncio.create_task(fetch_bitcoin())
     asyncio.create_task(fetch_eth())
     await asyncio.sleep(300)


async def main():
   """Gathers all tasks in a concurrent main event loop"""
   await fetch_sentiment()
   await asyncio.gather(
      fetch_stack(),
      daily_sentiment(),
      hourly_sentiment(),
   )
 

asyncio.run(main())




  
  
  
















