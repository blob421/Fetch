import numpy as np
import os 

import json
from utils.utils import compute_norm_params, sigmoid, load_dataset, row_gen

CURRENT_DIR = os.path.dirname(__file__)

WEIGHT_SAVE_PATH = os.path.join(CURRENT_DIR, 'weights')
BASE_WEIGHT = os.path.join(CURRENT_DIR, 'weights', 'initial.json')


SCHEMA = ["price","volume","marketCap","availableSupply","totalSupply",
          "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w", "sentiment"]

mean = 'Unset'
std = 'Unset'


def save_weight():
    global weights
    file_count = sum(1 for f in os.listdir(WEIGHT_SAVE_PATH)
                       if os.path.isfile(os.path.join(WEIGHT_SAVE_PATH, f)) and f.endswith('npy') and f.startswith('weights'))
    
    final_path = os.path.join(WEIGHT_SAVE_PATH, f'weights_{file_count + 1}.npy')
    print(f'Numpy weights saved to /weights/weights_{file_count + 1}.npy')

    np.save(final_path, weights)
      

def load_weights(n=None):
    global weights, mean, std
    if not n:
        with open(BASE_WEIGHT, 'r') as f:
            weights =  np.array(json.load(f).get('weights', []))
    else:
        weights = np.load(os.path.join(WEIGHT_SAVE_PATH, f'weights_{n}.npy'))

    mean = np.load(os.path.join(WEIGHT_SAVE_PATH, 'mean_regr.npy'))
    std = np.load(os.path.join(WEIGHT_SAVE_PATH, 'std_regr.npy'))

    



def train(learning_rate=0.01, epochs=100, threshold = 1e-4, batch_size=512) -> None:
    global weights, mean , std
    n, db_index = console_init()
    print('\nTrained started ...\n')
    load_weights(n)

    if not isinstance(mean, np.ndarray) or not isinstance(std, np.ndarray):
        print('Mean and std could not be retrived , aborting ...')
        os._exit(1)

    prices, X = load_dataset(db_index)


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
 
    while True:
        
        weight_number = input('\nEnter a numpy weight id to proceed or (n) to train from scratch : ')
        try:
            number = int(weight_number.strip())
            return number
         
        
        except Exception:
            if weight_number in ('n', 'no'):
               break      
            else:
                print('\nPlease provide a weight number or enter (n) to train from scratch')
                continue
          

    
    while True:
        print("Choose a dataset index , preferably the biggest as mean and std will only be calculated one time")
        idx = input('Index : ')
        try:
            idx = int(idx.strip())
            break

        except:
            continue

    if not os.path.exists(os.path.join(WEIGHT_SAVE_PATH, 'mean_regr.npy')):
        compute_norm_params(idx, regr=True)
        print('\nComputed mean and standard deviation for the dataset\n')
    
    
 
        
    return None, idx


if __name__ == '__main__':
    train()

