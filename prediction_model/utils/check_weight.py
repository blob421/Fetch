import numpy as np
import os 
cur_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../', 'weights', 'weight_5.npy'))
w = np.load(cur_dir)
print(w)
print(w.shape)