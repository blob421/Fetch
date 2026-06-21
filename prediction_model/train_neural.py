import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

import numpy as np
import os 
print(os.getcwd())
from utils.utils import (compute_norm_params_mixed, load__mixed_dataset, load_dataset, load_last_row, 
                   compute_norm_params)

CURRENT_DIR = os.path.dirname(__file__)

WEIGHTS_DIR = os.path.join(CURRENT_DIR, 'weights')

class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(        ### Defines a layer of sequences 
            nn.Linear(10, 32),           ### Creates 32 signals based on 10 features 
            nn.BatchNorm1d(32),          ### Normalize the signals so they don't jump or disappear
            nn.ReLU(),                   ### Keep only positive signals 

            nn.Linear(32, 16),           ### Make 16 signals out of those 32 signals 
            nn.BatchNorm1d(16),          ### Repeat normalization and keep positive signals 
            nn.ReLU(),

            nn.Linear(16, 1),            ### Create one score and pass it into a sigmoid 
            nn.Sigmoid()
        )

    def forward(self, x):                ### Send input into the sequence 
        return self.net(x)
    

def train_neural(mean_path , std_path, indexes):
    mean = np.load(os.path.join(WEIGHTS_DIR, mean_path))  ### shape (1, 10)
    std = np.load(os.path.join(WEIGHTS_DIR, std_path))    ### shape (1, 10)

    model = TinyNet()

    optimizer = torch.optim.Adam(model.parameters(), lr=5e-5)  ### Define learning rate 

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    factor=0.5,
    patience=5
)
    criterion = nn.BCELoss()              # binary classification loss
    

    prices , X = load__mixed_dataset()
  
    X = X[:-1]                                           ### Both miss the last row 
    Y = (prices[1:] >= prices[:-1]).astype(float)
   
    X = (X - mean) / std
    
    X_train = torch.tensor(X, dtype=torch.float32)
    y_train = torch.tensor(Y, dtype=torch.float32).unsqueeze(1)
    split = int(len(X_train) * 0.9)

    X_val = X_train[split:]
    y_val = y_train[split:]
    X_train = X_train[:split]
    y_train = y_train[:split]

    val_dataset = TensorDataset(X_val, y_val)
    val_loader = DataLoader(val_dataset, batch_size=512, shuffle=False)

    dataset = TensorDataset(X_train, y_train)
    loader = DataLoader(dataset, batch_size=512, shuffle=True)

    for epoch in range(200):
        model.train()
        for Xb, yb in loader:
            optimizer.zero_grad()

            preds = model(Xb)            # forward pass
            loss = criterion(preds, yb)  # compute loss

            loss.backward()                   # compute gradients
            optimizer.step()       
                                           # update weights
        
        model.eval()
        
        val_loss = 0.0

        with torch.no_grad():
            for Xb, yb in val_loader:
                preds = model(Xb)
                loss = criterion(preds, yb)
                val_loss += loss.item()

        val_loss /= len(val_loader)
        scheduler.step(val_loss)
        print(f"Epoch {epoch+1}, Train Loss: {loss.item():.4f}, Val Loss: {val_loss:.4f}")
    
    idx_str = '_'.join([i for i in indexes])
    torch.save(model.state_dict(), os.path.join(WEIGHTS_DIR, f"w_{idx_str}.pt"))
    print(f'\n Done ... weights saved in /weights/{f"w_{idx_str}.pt"}')


    
def prompt():
    print('\nWelcome to Fetch neural training script ...\n')
    while True:
        choice = input('Enter (m) for mixed datasets or (s) for a specific dataset  : ')
        if choice.lower().strip() == 'm':

                while True:

                    print("\nProvide a comma separared list of dataset indexes to use for mean and std calculations")
                    input_list = input('For crypto_data_p6 and p_1 , enter (6,1) : ')
                    try:
                        indexes = [i.strip() for i in input_list.split(',')]
                        return indexes, 'mixed'

                    except:
                        print('\nThere was a problem parsing this string, try again ...')
                        continue

               

        elif choice.lower().strip() == 's':

                 while True:
                 
                    print("Provide a dataset index to use for mean and std calculation")
                    input_list = input('For crypto_data_p6, enter 6  : ')
                    
                    try:
                        return int(input_list.strip()), 'single'
                    

                    except:
                        print('\nThere was a problem parsing this string, try again ...')
                        continue

        else:
            print('This choice is invalid')
            continue

def main():
    indexes, action = prompt()
    idx_str = '_'.join([i for i in indexes]) if not isinstance(indexes, int) else str(indexes)
    
    if action == 'mixed':
        
        if (not os.path.exists(os.path.join(WEIGHTS_DIR, f'mean_{idx_str}.npy'))
                or not os.path.exists(os.path.join(WEIGHTS_DIR, f'std_{idx_str}.npy'))):
            
            compute_norm_params_mixed(indexes)
            print(f'\nMean and std generated successfully for datasets {indexes} ...')
            print(f'Location : /weights/mean_{idx_str}.npy')

   
    else:
        if (not os.path.exists(os.path.join(WEIGHTS_DIR, f'mean_{idx_str}.npy'))
                or not os.path.exists(os.path.join(WEIGHTS_DIR, f'std_{idx_str}.npy'))):
            
            compute_norm_params(indexes)
            print(f'Mean and std generated successfully for dataset {indexes} ...')
            print(f'Location : /weights/mean_{idx_str}.npy\n')


    print('Training started ...\n')
    train_neural(f'mean_{idx_str}.npy', f'std_{idx_str}.npy', indexes)


if __name__ == '__main__':
    main()