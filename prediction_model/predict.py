import numpy as np
import sqlite3
from contextlib import closing
from train import DB_PATH, WEIGHT_SAVE_PATH, sigmoid, CURRENT_DIR
import os 

ROOT_DB_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '../', 'crypto_data.sqlite'))
def load_last_row():
    with sqlite3.connect(DB_PATH) as conn:
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
        

def load_weights(n):
    path = os.path.join(WEIGHT_SAVE_PATH, f'weight_{n}.npy')
    weights = np.load(path)
    mean = np.load(os.path.join(CURRENT_DIR, 'mean.npy'))
    std = np.load(os.path.join(CURRENT_DIR, 'std.npy'))
    return weights, mean ,std

def get_probabilities(weights, row, mean, std):
    data = np.array(row[2:], dtype=float).reshape(1, -1)
    standard  = (data - mean) / std

    score = standard @ weights                   ### data (1 , 10) weights (10, 1)

    sig = sigmoid(score)

    return sig




def predict():
    while True:
        weight_number = input('Enter a weight id to proceed, e.g. (6) : ')
        try:
            number = int(weight_number.strip())
            break

        except Exception:
            continue

    weights, mean, std = load_weights(number)
    row = load_last_row()
    
    result = get_probabilities(weights, row, mean, std )

    print(f'Probability of bitcoin going up : {result * 100} %')

predict()