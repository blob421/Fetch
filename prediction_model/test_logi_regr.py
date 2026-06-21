import numpy as np
from utils.utils import sigmoid ,load_last_row
import os 
import time
CURRENT_DIR = os.path.dirname(__file__)
WEIGHT_SAVE_PATH = os.path.join(CURRENT_DIR, 'weights')



        
def load_weights(n):
    path = os.path.join(WEIGHT_SAVE_PATH, f'w_{n}.npy')
    weights = np.load(path)
    mean = np.load(os.path.join(WEIGHT_SAVE_PATH, 'mean_{n}.npy'))
    std = np.load(os.path.join(WEIGHT_SAVE_PATH, 'std_{n}.npy'))
    return weights, mean ,std

def get_probabilities(weights, row, mean, std):
    data = np.array(row[2:], dtype=float).reshape(1, -1)
    standard  = (data - mean) / std

    score = standard @ weights                   ### data (1 , 10) weights (10, 1)

    sig = sigmoid(score)

    return sig




def predict(index:str):
    weights, mean, std = load_weights(index)
    while True:
        time_start = time.monotonic()
        
        row = load_last_row()
        
        result = get_probabilities(weights, row, mean, std )

        print(f'Probability of bitcoin going up : {result * 100} %')
        delata = time.monotonic() - time_start
        time.sleep(max(0, 300 - delata))





def main()-> None:
    while True:
                       
        print('\nChoose a weight from the following list :')
        print('-----------------------------------------\n')
        

     
        valid_files = [f for f in os.listdir(WEIGHT_SAVE_PATH) if f.endswith('.npy') and f.startswith('w_')]

        if not valid_files:
            print('There are no numpy weights in the weights folder , please train before infering ...')
            os._exit(1)

        for idx, f in enumerate(valid_files):
            print(f'{idx}     {f}')
        
        while True:
            print('\n-----------------------------------------')
                     
            choice = input('\nChoice : ')

            try:
                choice = int(choice.strip())
                file = valid_files[choice]
                break
            except:
                print('The index entered is out of range, try again ...')
                continue

        index = file.split('.')[0].split('.')[0].split('w_')[1]
        print('\nStarting the inference process ....\n')
        predict(index)

if __name__ == '__main__': 
    main()
