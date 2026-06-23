from train_neural import TinyNet
import numpy as np
import os 
from utils.utils import load_last_row, calculate_mean_action, amplify_sig
import time
import torch 


CURRENT_DIR = os.path.dirname(__file__)
WEIGHTS_DIR = os.path.join(CURRENT_DIR, 'weights')




def predict(index:str, filename:str, use_momentum=False) -> None:
    # 1. Recreate the model architecture
    model = TinyNet()
    mean = np.load(os.path.join(WEIGHTS_DIR, f'mean_{index}.npy'))  ### shape (1, 10)
    std = np.load(os.path.join(WEIGHTS_DIR, f'std_{index}.npy'))    ### shape (1, 10)
    # 2. Load weights
    model.load_state_dict(torch.load(os.path.join(WEIGHTS_DIR, filename)))
    model.eval()
    preds = {'good': 0 ,'bad' : 0, 'bad_diff': 0, 'good_diff': 0}
    last_pred = None
    last_price = None 
    iter = 0
    action_mean = 0
    action_std = 0
   

  
    while True:
        start_mono = time.monotonic()

        # 3. Load and preprocess the last row
        row_raw = load_last_row()                 # numpy array shape (10,)
        data = np.array(row_raw[2:], dtype=float).reshape(1, -1)
        standard = (data - mean) / std              # same normalization as training

        row = torch.tensor(standard, dtype=torch.float32)

        # 4. Forward pass
        with torch.no_grad():
            pred = model(row)

        result = pred.item()
        if use_momentum and action_mean > 0 and action_std > 0:
            sig = amplify_sig(float(result), action_mean, action_std)
            
        else:
            sig = float(result)

        if last_pred and last_pred > 0.56:
           if last_price < row_raw[2]:
               preds['good_diff'] += abs(row_raw[2] - last_price)
         
               preds['good'] += 1
           else:
               preds['bad_diff'] += abs(row_raw[2] - last_price)
               preds['bad'] += 1


        elif last_pred and last_pred < 0.44 :

            if last_price > row_raw[2]:
                preds['good_diff'] += abs(row_raw[2] - last_price)

                preds['good'] += 1
            else:
                preds['bad_diff'] += abs(row_raw[2] - last_price)
                preds['bad'] += 1
            
        last_pred = sig
        last_price = row_raw[2]
                       
        if iter > 0 and iter % 10 == 0:
           good = preds.get('good', 0)
           bad = preds.get('bad', 0) 
     
           trades_won = (good / (bad + good)  * 100 ) if bad > 0 and good > 0 else 0 
           

                       
           print(f'\nSummary :')
           print('----------------')
           print(f'Trades won: {str(trades_won)} %')
           print(f'Lost :{preds.get('bad_diff')}')
           print(f'Earned :{preds.get('good_diff')}')
   

        iter += 1
  

        print(f"Probability of BTC going up:  {sig * 100}%")

        action_mean, action_std = calculate_mean_action()

        delta_mono = max(0, time.monotonic() - start_mono)
        
        time.sleep(300 - delta_mono)


def main()-> None:
    while True:
                       
        print('\nChoose a weight from the following list :')
        print('-----------------------------------------\n')
        

     
        valid_files = [f for f in os.listdir(WEIGHTS_DIR) if f.endswith('.pt') and f.startswith('w_') ]

        if not valid_files:
            print('There are no pytorch weights in the weights folder , please train before infering ...')
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
            
        while True:
            use_momentum = False
   
            choice = input('Use momentum ? (y or n) : ')
            if choice.strip().lower() in ('y', 'yes'):
                use_momentum = True
                break
            elif choice.strip().lower() in ('n', 'no'):
                use_momentum = False
                break

            else:
                print('Invalid choice , Please enter "y" or "n" ..')
                continue

                    

        index = file.split('_P')[0].split('w_')[1]
        print('\nStarting the inference process ....\n')
        predict(index, file, use_momentum)

if __name__ == '__main__': 
    main()
            

        
                   