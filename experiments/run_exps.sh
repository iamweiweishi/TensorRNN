#!/bin/bash
timestamp() {
  date +"%T"
}
datestamp() {
  date +"%D"
}

t=$(timestamp)
t="$(echo ${t} | tr ':' '-')"

d=$(datestamp)
d=$(echo ${d} | tr '/' '-')

start_time="$d-$t"

use_error=True #--use_error_prop

#data_path=../../../data/lorenz_series.pkl
#chaotic_ts_mat.pkl  chaotic_ts.pkl  lorenz_series_mat.pkl  lorenz_series.pkl  traffic_9sensors.pkl  ushcn_CA.pkl


hidden_size=64
learning_rate=1e-2
burn_in_steps=5 # just for naming purposes


for exp in climate traffic 
do 
    data_path=/home/qiyu/data/${exp}.npy
            for model in LSTM MLSTM TLSTM
            do
            save_path=/tmp/tensorRNN/log/$exp/$start_time/$model/
            echo $save_path
            mkdir -p $save_path
            python train.py --model=$model --data_path=$data_path --save_path=$save_path --hidden_size=$hidden_size --learning_rate=$learning_rate --use_error_prop=$use_error  
            done
done

cp $(pwd)/run_exps.sh ${save_path}run_exps.sh
