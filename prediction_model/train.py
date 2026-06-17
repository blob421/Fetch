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

def load_dataset():
    rows = []
    for row in row_gen():

        rows.append(row[2:])
    rows = np.array(rows, dtype=float)
    prices = rows[:, 0]                  ### (rows_count, )     
    X = rows[:, :]                       ### (rows_count, 10)
    return prices, X

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


def train(learning_rate=0.01, epochs=100, threshold = 1e-4, batch_size=512) -> None:
    global weights, mean , std
    console_init()
    print('\nTrained started ...\n')
    load_weights()

    if not isinstance(mean, np.ndarray) or not isinstance(std, np.ndarray):
        print('Mean and std could not be retrived , aborting ...')
        os._exit(1)

    prices, X = load_dataset()


    X = X[:-1]                                           ### Both miss the last row 
    movement = (prices[1:] >= prices[:-1]).astype(float)

    prev_weights = None
    b = 0.0

    for epoch in range(epochs):
        for i in range(0, len(X), batch_size):
            xb = X[i:i+batch_size]
            yb = movement[i:i+batch_size].reshape(-1, 1)           ### (512, 1)
            

            data_standarized = (xb - mean) / std    ### Standarized array
                                                    ### (512, 10) 10 col per row
              
            result = data_standarized @ weights + b ### (512, 1) 1 result per row
         

            sig = sigmoid(result)                  ### (512, 1) 1 proba per row
         
            
          

           
            # Gradient
            err = sig - yb          # (512, 1) * (512, 10) = (512, 10) applies to all cols
            gradient_b = err.mean()
            gradient = (err * data_standarized).mean(axis=0).reshape(-1,1)

          

                    

            # Update                              ### Weights (10, 1)
            b -= learning_rate * gradient_b                  ### Grad    (512, 10)
            weights -= learning_rate * gradient   ### Gradient is unique for each features
                                                  ### Depending on how they derived 


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



