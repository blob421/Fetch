
import sqlite3
import os 
import time
from datetime import datetime , timedelta, timezone
from contextlib import closing
import requests
import numpy as np

CURDIR = os.path.dirname(__file__)
DBPATH = os.path.abspath(os.path.join(CURDIR, '../', '../', 'crypto_data.sqlite'))

class Momentum():
    def __init__(self):
  
        pass

    def init_db(self):
        with sqlite3.connect(DBPATH) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("""CREATE TABLE IF NOT EXISTS bitcoin_momentum(date VARCHAR(40),
                                                                        cumul_delta FLOAT)""")    
 
    def wait_for_db(self):

        with sqlite3.connect(DBPATH) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute("""SELECT * FROM bitcoin_data ORDER BY date DESC LIMIT 1""")
                row = cur.fetchone()
                next_iter = datetime.fromisoformat(row[0]) + timedelta(minutes=5)
                delta =  next_iter- datetime.now(timezone.utc) 
            
        print(f'Starting in {delta.total_seconds()}s ...')
        time.sleep(delta.total_seconds())

    def collect_data(self):
        data = []

        next_tick = time.monotonic()
        start_time = time.monotonic()
        try:
            while time.monotonic() <= start_time + 296:
                next_tick += 2
                
                res = requests.get('https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT')
                price = res.json().get('price', None)
                if not price:
                    print('None detected')
                data.append(price)
                time_until_next_tick = next_tick - time.monotonic()
                time.sleep(max(0, time_until_next_tick))
        
        
            cleaned = np.array([float(p) for p in data if p])
            deltas = np.abs(cleaned[1:] - cleaned[:-1])
            spike_thr = np.percentile(deltas, 90) ### 90% biggest moves
            filtered = deltas[deltas < spike_thr] ### Must be smaller than those moves

            cumul_delta = np.sum(filtered)
            print(cumul_delta)       
            return round(cumul_delta, 3)
        
        except requests.exceptions.SSLError:
            print('An error was encountered with the api')
            return None


    def save_timeframe(self, deltas):
        with sqlite3.connect(DBPATH) as conn:
            with closing(conn.cursor()) as cur:
                now = datetime.now(timezone.utc).isoformat()
                print(f'Date: {now} , deltas: {deltas}')
                cur.execute("""INSERT INTO bitcoin_momentum(date, cumul_delta) VALUES(?, ?)""", [now, deltas])    

                if cur.rowcount != 1:
                    print('Error inserting row')
                conn.commit()

    def collect(self):
        self.init_db()
        self.wait_for_db()
        print('Started ...')
        while True:
            time_start = time.monotonic()  
            cumul_delta= self.collect_data() ## takes 296s  
            if cumul_delta:           
                self.save_timeframe(cumul_delta)   
            delta = time.monotonic() - time_start
            time.sleep(300 - delta)



if __name__ == '__main__':
    collector = Momentum()
    collector.collect()

            


