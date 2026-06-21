
import os 
import sqlite3
import contextlib
from datetime import datetime, timezone, timedelta
import time
import numpy as np
import torch
from neural_model import TinyNet, get_probabilities_mixed


import requests
import logging

WEIGHTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'weights'))
ROOTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', '../'))

LOGPATH = os.path.join(ROOTDIR, 'logs', 'kraken_bot.log')
logger = logging.getLogger(__name__)
logging.basicConfig(filename=LOGPATH, level=logging.INFO)

class KrakenMain():
    def __init__(self):
        self.DBPATH = os.path.join(ROOTDIR, 'crypto_data.sqlite')
        self.row = None
        self.weigths = None
        self.weights_id = '10'
        self.order_id = None
        self.last_price = None
        self.mean = None
        self.std = None
        self.qty = None
        self.good_trades = 0
        self.iter = 0
        self.bad_trades = 0
        self.good_score = 0
        self.bad_score = 0
        self.probability = None
        self.SECRET_KEY = ''
        self.APIKEY = ''
    
        self.last_open = None
        self.has_active_position = False

    @staticmethod
    def with_sqlite(fn):
        def wrapper(self, *args, **kwargs):
           with sqlite3.connect(self.DBPATH, isolation_level=None) as conn:
                with contextlib.closing(conn.cursor()) as cur:
                    try:
                        return fn(self, cur, *args, **kwargs)
                    
                    except sqlite3.Error as e:
                        print(e)

            
        
        return wrapper

    @with_sqlite    
    def startup_init(self, cur):
        seconds_to_wait = 0
        print('\n################# KRAKENBOT #####################\n')
        valid_weights = [f for f in os.listdir(WEIGHTS_DIR) if f.endswith('.pt') and f.startswith('w_')]
        if not valid_weights: 
            print('\nNo weights available , aborting ...')
            os._exit(1)
        print('\nChoose a weight to proceed : ')
        print('-----------------------------\n')
        for idx, w in enumerate(valid_weights):
            print(f'{idx}       {w}')

        print('\n-----------------------------\n')
        while True:
            weight = input('Choice : ')
            try:
                w_idx = int(weight.strip())
                weight_str = valid_weights[w_idx]

                break
            except:
                print('Index is out of range , try again ...\n')
                continue    
        try:
          
            cur.execute("SELECT * FROM bitcoin_data ORDER BY date DESC LIMIT 1")
            row = cur.fetchone()
            date = row[0]
        
            parsed_datetime = datetime.fromisoformat(date)
        
            now = datetime.now(timezone.utc) 
            
            
            delta = now - parsed_datetime
            seconds_difference = delta.total_seconds()
            minutes_difference = seconds_difference / 60
           

            if (minutes_difference / 5 < 1):
                seconds_to_wait = (5 - minutes_difference) * 60
            
            else:
                iterations_done_since = minutes_difference // 5
                last_supposed_iteration = parsed_datetime + timedelta(minutes = iterations_done_since * 5)
                next_supposed_iteration = last_supposed_iteration + timedelta(minutes=5)
                delta_from_next_iteration = next_supposed_iteration - now
                seconds_to_wait = delta_from_next_iteration.total_seconds()
                    

        finally: 
            if seconds_to_wait > 0:
               print(f'\nStarting in {seconds_to_wait + 5} seconds ...')

            time.sleep(seconds_to_wait + 5)
            print("Starting ...\n")
            logger.info('Program started ...')
        
            self.main(weight_str)

    @with_sqlite
    def fetch_last_row(self, cur):
        cur.execute("""SELECT b.*, m.fear_greed_value
                FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY date DESC) AS rn, *
                    FROM bitcoin_data
                    ORDER BY date DESC
                    LIMIT 1
                ) AS b
                JOIN (
                    SELECT ROW_NUMBER() OVER (ORDER BY date DESC) AS rn, *
                    FROM market_data
                    ORDER BY date DESC
                    LIMIT 1 
                ) AS m
                ON b.rn = m.rn;""")
        
        return cur.fetchone()

    def main(self, weight_str):
        weight_idx_str = weight_str.split('.')[0].split('w_')[1]
        elapsed2 = 0
        model = TinyNet()
        mean = np.load(os.path.join(WEIGHTS_DIR, f'mean_{weight_idx_str}.npy'))  ### shape (1, 10)
        std = np.load(os.path.join(WEIGHTS_DIR, f'std_{weight_idx_str}.npy'))    ### shape (1, 10)
        # 2. Load weights
        model.load_state_dict(torch.load(os.path.abspath(os.path.join(WEIGHTS_DIR, f'w_{weight_idx_str}.pt'))))
        model.eval()

        while True:
            start = time.monotonic()

            if self.iter > 0:
                self.last_price = self.row[2]

            self.row = self.fetch_last_row()
            
            
            self.eval_score()
  
            now = datetime.now(timezone.utc)
            
            row_time = datetime.fromisoformat(self.row[1])
            if (now - row_time) > timedelta(seconds=30):
                logger.warning('Error : The row fetched is not the most recent one , Ignoring ...')
         
            sig = get_probabilities_mixed(self.row, model, mean, std)
            if sig: 
                    self.probability = float(sig)
                    
                
                    logger.info(f'Row Time : {self.row[1]}  sig: {self.probability}')
                    self.placebid()

            elapsed =  time.monotonic() - start
        
            time.sleep(max(0, 300 - (elapsed + elapsed2)))
            elapsed2 = 0

            if self.has_active_position:
                start_time_cancel = time.monotonic()
                success = self.make_request(close=True)

                if success :
           
                    self.has_active_position = False
                    print(f'order closed : {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}')
            
                elapsed2 = time.monotonic() - start_time_cancel



    def make_request(self, long=False, close=False):

        for _ in range(3):
     
                try:
     
                    res = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD')

                    j_son = res.json()
                    price = j_son.get('price', None)
                   
                 
              
                    if not res.ok :
                        logger.error(f'Fetching btc_usdt ticker failed')
                        continue


                except requests.exceptions.RequestException as e:
                    logger.warning(f'\nThere was a problem when fetching index price : {e}\n')
                    return None
            
                if price:
                    try:
                        p_side = 'sell' if close else "buy"
                        
                        price = str(float(price) - 25) if close else str(float(price) + 25)

                        self.qty = round(155 / float(price), 4) if not close else self.qty

                        query = {"ordertype": "limit",  "type": p_side, "pair": "BTCUSDT", "price": price,
                                 "nonce": int(time.time() * 1000), "volume": str(self.qty)}
                            
                        url = "https://api.kraken.com/0/private/AddOrder"
                        signature = kraken_sign('/0/private/AddOrder', query, self.SECRET_KEY)
                        
              
                        
                  
                        res = requests.post(url, headers={"API-Key": self.APIKEY, 
                                                          'API-Sign': signature, 
                                                          "Content-Type": "application/json"}, 
                                                          json=query)
                        data = res.json()
                    


                        if not res.ok or data.get('error'):
                            logger.warning(f'Error creating order , error: {data.get('error')}')
                            continue
                    
                        else:   
                            return True
                       
                    except requests.exceptions.RequestException as e:
                        print(f'\nThere was an error creating an order , balance might be insufficient: {e}\n')
         


                time.sleep(5)

        return None


    def placebid(self):

        
        if self.has_active_position:
            print('\nA position is already active , consider closing it before proceeding\n')
            return
        
        if self.probability >= 0.56:

            succeeded = self.make_request(long=True)
            if not succeeded: 
                print('Error placing an order ')
                
                return None
            print(f'Buy order placed at : {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}')


        else:
            return None
        
        self.has_active_position = True
        self.last_open = datetime.now()

    
    
    def eval_score(self):
        
        if self.iter == 0:
            self.iter += 1
            return
        
        if self.probability and self.probability > 0.56:
           if self.last_price < self.row[2]:
               self.good_score += abs(self.row[2] - self.last_price)
         
               self.good_trades += 1
           else:
               self.bad_score += abs(self.row[2] - self.last_price)
               self.bad_trades += 1


        if self.iter > 0 and self.iter % 10 == 0:
       
     
           trades_won = (self.good_trades / (self.bad_trades + self.good_trades)  * 100 ) if self.bad_trades > 0 and self.good_trades > 0 else 0
           

                       
           print(f'\nSummary :')
           print('----------------')
           print(f'Trades won: {str(trades_won)} %')
           print(f'Lost :{self.bad_score}')
           print(f'Earned :{self.good_score}')
   

        self.iter += 1
  
        
    


def start():
    controller = KrakenMain()
    controller.startup_init()



    

import urllib.parse, hashlib, hmac, base64

def kraken_sign(urlpath: str, data: dict, secret: str) -> str:
   
    encoded = (str(data['nonce']) + urllib.parse.urlencode(data)).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()



start()