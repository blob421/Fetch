
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
LOGPATH = os.path.join(ROOTDIR, 'logs', 'mexc_bot.log')
logger = logging.getLogger(__name__)
logging.basicConfig(filename=LOGPATH, level=logging.INFO)

class MexcMain():
    def __init__(self):
        self.DBPATH = os.path.join(ROOTDIR, 'crypto_data.sqlite')
        self.row = None
        self.weigths = None
        self.weights_id = '10'
        self.order_id = None
        self.last_price = None
        self.mean = None
        self.std = None
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
        print('\n################# MEXCBOT #####################\n')
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
            
            if self.iter > 0:
                self.eval_score()
  
            now = datetime.now(timezone.utc)
            
            row_time = datetime.fromisoformat(self.row[1])

            if (now - row_time) > timedelta(seconds=30):
                logger.warning('Error : The row fetched is not the most recent one , Ignoring ...')
            
            else:
                sig = get_probabilities_mixed(self.row, model, mean, std)
                if sig: 
                    self.probability = float(sig)
                    
                
                    logger.info(f'Row Time : {self.row[1]}  sig: {self.probability}')
                    long = self.placebid()

            elapsed =  time.monotonic() - start
        
            time.sleep(max(0, 300 - (elapsed + elapsed2)))
            elapsed2 = 0
            if self.has_active_position:
                start_time_cancel = time.monotonic()
                success = self.make_request(close=True, long=long)
                if success :
                    pos_str = 'Long' if long else 'Short'
                    self.has_active_position = False
                    print(f'{pos_str} closed : {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}')
                else:
                    try:
                        body = [self.order_id]
                        headers = get_headers(body , self.SECRET_KEY, self.APIKEY)
                        json_str = json.dumps(body, separators=(',', ':'))
                        res = requests.post('/api/v1/private/order/cancel' ,data=json_str, headers=headers)
                        success = res.json().get('success', None)

                        if not success:
                              print('\nWarning , the position could not be closed ! Requires immediate intervention\n')
                        else:
                            self.order_id = None

                    except requests.exceptions.RequestException as e:
                        logger.warning(f"could not cancel order by id : {e}")
                elapsed2 = time.monotonic() - start_time_cancel



    def make_request(self, long=False, close=False):

        if not close:
            side = 1 if long else 3
            
        else:
            side = 4 if long else 2

        cross = 2
        isolated = 1
        for _ in range(3):
            if not close:
                try:
     
                    res = requests.get('https://api.mexc.com/api/v1/contract/ticker?symbol=BTC_USDC')

                    j_son = res.json()
                    data = j_son.get('data', {})
                    bid1 = float(data.get("bid1"))
                    ask1 = float(data.get("ask1"))

                    price = bid1 -5 if long else ask1 + 5
                    success = j_son.get('success', None)
              
                    if not success :
                        logger.error(f'Fetching btc_usdc ticker failed, code : {data.get('code')} data: {data.get('data')}')
                        continue


                except requests.exceptions.RequestException as e:
                    logger.warning(f'\nThere was a problem when fetching index price : {e}\n')
                    return None
            
                if price:
                    try:
                        ### 3.22 usdc per contracts , 6 contracts 19.2 usdc
                        body = {'symbol': 'BTC_USDC', 'vol': 6,  'price': price , 
                                'side': side, 'type': 1, 'openType': isolated, 'leverage': 2}
                        
                        json_str = json.dumps(body, separators=(',', ':'))

                        headers = get_headers(body, self.SECRET_KEY, self.APIKEY)

                        res = requests.post('https://api.mexc.com/api/v1/private/order/create', headers=headers, 
                                            data=json_str)
                        data = res.json()
                        
                       
                        success = data.get('success', None)

                        if success :
                            self.order_id = data.get('data', {}).get('823514465458327680', None)
                            
                            return success
                        else:
                            logger.warning(f'Failed to place order, code : {data.get('code')} data: {data.get('data')}')
                            continue

                    except requests.exceptions.RequestException as e:
                        print(f'\nThere was an error creating an order , balance might be insufficient: {e}\n')
            else:
                try: 
                    body = {}
                    headers = get_headers(body, self.SECRET_KEY, self.APIKEY)
                    json_str = json.dumps(body, separators=(',', ':'))
                    res = requests.post('https://api.mexc.com/api/v1/private/position/close_all', 
                                        headers=headers, data=json_str)
                    success = res.json().get('success', False)

                    if success: 
                        return success 
                    else: 
                       
                        continue

                except requests.exceptions.RequestException as e:
                        print(f'\nThere was an error closing all orders : {e}\n')
                        continue


            time.sleep(5)

        return None


    def placebid(self):

        
        if self.has_active_position:
            print('\nA position is already active , consider closing it before proceeding\n')
            return
        
        if self.probability >= 0.56:

            succeeded = self.make_request(long=True)
            if not succeeded: 
                print('Error placing a long ')
                
                return None
            print(f'Long placed at : {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}')

        elif self.probability <= 0.44:

            succeeded = self.make_request(long=False)
            if not succeeded: 
                print('Error placing a short')
                return None

            print(f'Short placed at : {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}')
        else:
            return None
        
        self.has_active_position = True
        self.last_open = datetime.now()

        return self.probability >= 0.56
    
    def eval_score(self):

        if self.probability and self.probability > 0.56:
           if self.last_price < self.row[2]:
               self.good_score += abs(self.row[2] - self.last_price)
         
               self.good_trades += 1
           else:
               self.bad_score += abs(self.row[2] - self.last_price)
               self.bad_trades += 1


        elif self.probability and self.probability < 0.44 :

            if self.last_price > self.row[2]:
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
    controller = MexcMain()
    controller.startup_init()

import hmac, hashlib, time, json

def get_headers(body, secret, key):

    timestamp, signature = sign_post(key, secret, body)
    return {
            "ApiKey": key,
            "Request-Time": timestamp,
            "Signature": signature,
            "Content-Type": "application/json"
                }

def sign_post(api_key, secret_key, body_dict):
    timestamp = str(int(time.time() * 1000))

    # JSON string EXACTLY as sent
    json_str = json.dumps(body_dict, separators=(',', ':'))

    target = api_key + timestamp + json_str

    signature = hmac.new(
        secret_key.encode(),
        target.encode(),
        hashlib.sha256
    ).hexdigest()

    return timestamp, signature


start()