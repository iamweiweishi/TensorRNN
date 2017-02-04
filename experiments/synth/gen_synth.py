import numpy as np
import cPickle as pickle

class Config(object):
    num_time = int(1e5)
    num_dim = 1
    alpha = 4.0
    init_val = 0.1

def gen_chaotic_ts():
    config = Config()   
    data_path = "/tmp/stephan/"
    file_name = "chaotic_ts.pkl"
    x = np.ndarray((config.num_time) )
    x[0]  = config.init_val 
    f = lambda  x ,t: config.alpha* x[t] * (1.0 - x[t]) 
    for t in range(config.num_time-1):
        x[t+1] = f(x,t)
    pickle.dump(x,open(data_path+file_name,"wb"))
    
def main():
    gen_chaotic_ts()

if __name__== "__main__":
    main()
