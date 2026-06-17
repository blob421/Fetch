import numpy as np
import os 
import sqlite3
from contextlib import closing
import json

CURRENT_DIR = os.path.dirname(__file__)

WEIGHT_SAVE_PATH = os.path.join(CURRENT_DIR, 'weights')
BASE_WEIGHT = os.path.join(CURRENT_DIR, 'weights', 'initial.json')
DB_PATH = os.path.join(CURRENT_DIR, 'crypto_data.sqlite')

SCHEMA = ["price","volume","marketCap","availableSupply","totalSupply",
          "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w", "sentiment"]

mean = 'Unset'
std = 'Unset'


def save_weight():
    global weights
    file_count = sum(1 for f in os.listdir(WEIGHT_SAVE_PATH)
                       if os.path.isfile(os.path.join(WEIGHT_SAVE_PATH, f)))
    
    final_path = os.path.join(WEIGHT_SAVE_PATH, f'weight_{file_count + 1}.npy')

    np.save(final_path, weights)
      

def load_weights():
    global weights, mean, std
    with open(BASE_WEIGHT, 'r') as f:
        weights =  np.array(json.load(f).get('weights', []))

    mean = np.load(os.path.join(CURRENT_DIR, 'mean.npy'))
    std = np.load(os.path.join(CURRENT_DIR, 'std.npy'))

    

def row_gen():
    with sqlite3.connect(DB_PATH) as conn :
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


def train(learning_rate=0.01, epochs=100, threshold = 1e-3):
    global weights, mean , std
    console_init()
    print('\nTrained started ...\n')
    load_weights()

    if not isinstance(mean, np.ndarray) or not isinstance(std, np.ndarray):
        print('Mean and std could not be retrived , aborting ...')
        os._exit(1)

    prev_weights = None
    for epoch in range(epochs):
        last_price = None
        for row in row_gen():

            if not last_price:
                last_price = row[1]
                continue

            price = row[1]
            data = np.array([float(f) for f in row[2:]], dtype=float).reshape(1, -1)

            data_standarized = (data - mean) / std

            result = data_standarized @ weights

            sig = sigmoid(result)

            movement = 0 if last_price > price else 1
            

            # Gradient
            gradient = ((sig - movement) * data_standarized).T

            # Update
            weights -= learning_rate * gradient

            last_price = price 

        print(f'Epoch {epoch} done ...')
    
        if isinstance(prev_weights, np.ndarray) and np.all(np.abs(weights - prev_weights) < threshold):
            save_weight()
            print("Gradient converged, done ...")
            
            return
        
        prev_weights = weights.copy()
    
    save_weight()
    print('Done ...')

def console_init():
    if not os.path.exists(os.path.join(CURRENT_DIR, 'mean.npy')):
        compute_norm_params()
        print('Computed mean and standard deviation for the dataset\n')
        return
    
    
    while True:
        recalc = input("Recalculate norm params ? (y , n) : ")
        if recalc.lower().strip() in ('y', 'yes'):
            compute_norm_params()
            break

        elif recalc.lower().strip() in ('n', 'no'):
            break
        
        else:
            print('Wrong choice, please enter (y or n)\n')
            continue

    
def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def compute_norm_params():
    n = 0
    mean = None
    M2 = None  # sum of squared differences

    for row in row_gen():
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

    np.save(os.path.join(CURRENT_DIR, 'mean.npy'), mean)
    np.save(os.path.join(CURRENT_DIR, 'std.npy'), std)


train()

