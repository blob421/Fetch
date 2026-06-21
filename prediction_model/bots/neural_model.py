
import torch
import numpy as np
import torch.nn as nn

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
    
def get_probabilities_mixed(row_raw, model, mean, std):


                 # numpy array shape (10,)
    data = np.array(row_raw[2:], dtype=float).reshape(1, -1)
    standard = (data - mean) / std              # same normalization as training

    row = torch.tensor(standard, dtype=torch.float32)

        # 4. Forward pass
    with torch.no_grad():
        pred = model(row)

    return pred.item()