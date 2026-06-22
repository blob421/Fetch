
import numpy as np
import os 
import sqlite3
from contextlib import closing
import torch


CURRENT_DIR = os.path.dirname(__file__)


MODEL_ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../'))

WEIGHT_SAVE_PATH = os.path.join(MODEL_ROOT_DIR, 'weights')

DB_PATH = os.path.join(MODEL_ROOT_DIR, 'crypto_data.sqlite')


FETCH_DIR = os.path.abspath(os.path.join(MODEL_ROOT_DIR, '../'))

DB_PARTS_DIR = os.path.join(FETCH_DIR, 'datasets')

CURRENT_DB_PATH = os.path.join(FETCH_DIR, 'crypto_data.sqlite')

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def load_weights(n):
    path = os.path.join(WEIGHT_SAVE_PATH, f'weight_{n}.npy')
    weights = np.load(path)
    mean = np.load(os.path.join(CURRENT_DIR, 'mean.npy'))
    std = np.load(os.path.join(CURRENT_DIR, 'std.npy'))
    return weights, mean ,std

def save_weight():
    global weights
    file_count = sum(1 for f in os.listdir(WEIGHT_SAVE_PATH)
                       if os.path.isfile(os.path.join(WEIGHT_SAVE_PATH, f)))
    
    final_path = os.path.join(WEIGHT_SAVE_PATH, f'weight_{file_count + 1}.npy')

    np.save(final_path, weights)

    
def get_probabilities(weights, row, mean, std):
    data = np.array(row[2:], dtype=float).reshape(1, -1)
    standard  = (data - mean) / std

    score = standard @ weights                   ### data (1 , 10) weights (10, 1)

    sig = sigmoid(score)

    return sig





def load_last_row():

    with sqlite3.connect(CURRENT_DB_PATH) as conn:
        with closing(conn.cursor()) as cur:
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

            result = cur.fetchone()
            return result 


def load__mixed_dataset():
    rows = []
    for d_id in range(1, 7):
        
        for row in row_gen(os.path.join(DB_PARTS_DIR, f'crypto_data_p{d_id}.sqlite')):
             
            rows.append(row[2:])

    rows = np.array(rows, dtype=float)
    prices = rows[:, 0]                  ### (rows_count, )   

    diff = np.abs(prices[1:] - prices[:-1]) 
    threshold = np.percentile(diff, 5) 
    mask = diff >= threshold

    X_filtered = rows[:-1][mask]                     ### (rows_count, 10)
    price_filtered = prices[1:][mask]
    return price_filtered, X_filtered


def load_dataset(n):
    rows = []
    for row in row_gen(os.path.join(DB_PARTS_DIR, f'crypto_data_p{n}.sqlite')):

        rows.append(row[2:])
    rows = np.array(rows, dtype=float)
    prices = rows[:, 0]                  ### (rows_count, )     
    X = rows[:, :]                       ### (rows_count, 10)
    return prices, X


def row_gen(DB=None):
    db_str = DB_PATH if not DB else DB
    with sqlite3.connect(db_str) as conn :
        with closing(conn.cursor()) as cur :
            cur.execute("""
                SELECT b.*, m.fear_greed_value
                FROM (
                    SELECT ROW_NUMBER() OVER (ORDER BY date) AS rn, *
                    FROM bitcoin_data
                ) AS b
                JOIN (
                    SELECT ROW_NUMBER() OVER (ORDER BY date) AS rn, *
                    FROM market_data
                ) AS m
                ON b.rn = m.rn;
            """)
            
            for row in cur:
                yield row




def compute_norm_params_mixed(indexes):
    n = 0
    mean = None
    M2 = None  # sum of squared differences
    for d_id in indexes:
    
    
      for row in row_gen(os.path.join(DB_PARTS_DIR, f'crypto_data_p{d_id}.sqlite')):
  
        x = np.array([float(f) for f in row[2:]], dtype=float)

        if mean is None:
            mean = np.zeros_like(x)
            M2 = np.zeros_like(x)

        n += 1
        delta = x - mean
        mean += delta / n
        delta2 = x - mean
        M2 += delta * delta2

    variance = M2 / (n - 1)
    std = np.sqrt(variance)

    idx_str = '_'.join([i for i in indexes])
    np.save(os.path.join(WEIGHT_SAVE_PATH, f'mean_{idx_str}.npy'), mean)
    np.save(os.path.join(WEIGHT_SAVE_PATH, f'std_{idx_str}.npy'), std)



def compute_norm_params(index, regr=False):
    n = 0
    mean = None
    M2 = None  # sum of squared differences

    for row in row_gen(os.path.join(DB_PARTS_DIR, f'crypto_data_p{index}.sqlite')):
        x = np.array([float(f) for f in row[2:]], dtype=float)

        if mean is None:
            mean = np.zeros_like(x)
            M2 = np.zeros_like(x)

        n += 1
        delta = x - mean
        mean += delta / n
        delta2 = x - mean
        M2 += delta * delta2

    variance = M2 / (n - 1)
    std = np.sqrt(variance)

    mean_path = os.path.join(WEIGHT_SAVE_PATH, f'mean_{index}.npy') if not regr else os.path.join(WEIGHT_SAVE_PATH, f'mean_regr.npy')
    std_path = os.path.join(WEIGHT_SAVE_PATH, f'std_{index}.npy') if not regr else os.path.join(WEIGHT_SAVE_PATH, f'std_regr.npy')
    np.save(mean_path, mean)
    np.save(std_path, std)




def get_action_score():
  with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cur:
                cur.execute("""SELECT * FROM bitcoin_momentum ORDER BY date DESC LIMIT 1""") 
                row = cur.fetchone()
                return row[1]        

def calculate_mean_action():
  with sqlite3.connect(DB_PATH) as conn:
        with closing(conn.cursor()) as cur:
                cur.execute("""SELECT * FROM bitcoin_momentum""") 
                rows = cur.fetchall()
                array = np.array([r[1] for r in rows])
                mean = np.mean(array)
                std = np.std(array)
                return mean, std     

def amplify_sig(sig, mean, std):
  
    
    score = get_action_score()
    std_units = abs(score - mean) / std
    multiplier = 0.005
    boost = multiplier * std_units
   
    if score < mean :
        final_boost = 0
    else:
        final_boost = min(0.04, boost)
    
    return sig - final_boost if sig < 0.5 else sig + final_boost