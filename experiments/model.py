
from __future__ import print_function

import tensorflow as tf
from tensorflow.contrib import rnn
from trnn import *
from trnn_imply import *

def LSTM(inputs, is_training, config):

    # Prepare data shape to match `rnn` function requirements
    # Current data input shape: (batch_size, timesteps, n_input)
    # Required shape: 'timesteps' tensors list of shape (batch_size, n_input)

    # Define a lstm cell with tensorflow
    def lstm_cell():
        return tf.contrib.rnn.BasicLSTMCell(config.hidden_size,forget_bias=1.0)

    cell = tf.contrib.rnn.MultiRNNCell(
        [lstm_cell() for _ in range(config.num_layers)])

    # Get lstm cell output
    outputs, state  = rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def MLSTM(inputs, is_training, config):
    def mlstm_cell():
        return MatrixLSTMCell(config.hidden_size,config.num_lags)
    cell = mlstm_cell()
    if is_training and config.keep_prob < 1:
        cell = tf.contrib.rnn.DropoutWrapper(
          cell, output_keep_prob=config.keep_prob)        
    cell = tf.contrib.rnn.MultiRNNCell(
        [cell for _ in range(config.num_layers)])
    outputs, state = tensor_rnn_with_feed_prev(cell, inputs, is_training, config) 
    return outputs  

def TLSTM(inputs, is_training, config):
    def tlstm_cell():
        return TensorLSTMCell(config.hidden_size, config.num_lags, config.rank_vals)
    cell= tlstm_cell() 
    if is_training and config.keep_prob < 1:
        cell = tf.contrib.rnn.DropoutWrapper(
          cell, output_keep_prob=config.keep_prob)        
    cell = tf.contrib.rnn.MultiRNNCell(
        [cell for _ in range(config.num_layers)])
    outputs, state = tensor_rnn_with_feed_prev(cell, inputs, is_training, config) 
    return outputs  

def PLSTM(inputs, is_training, config):
    def rnn_cell():
        return tf.contrib.rnn.PhasedLSTMCell(config.hidden_size)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [rnn_cell() for _ in range(config.num_layers)])

    outputs, state  = rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def RNN(inputs, is_training, config):
    def rnn_cell():
        return tf.contrib.rnn.BasicRNNCell(config.hidden_size)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [rnn_cell() for _ in range(config.num_layers)])
    
    outputs, state  = rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def MRNN(inputs, is_training, config):
    def mrnn_cell():
        return MatrixRNNCell(config.hidden_size,config.num_lags, config.num_orders)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [mrnn_cell() for _ in range(config.num_layers)])
    
    outputs, state  = tensor_rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def HOLSTM(inputs, is_training, config):
    def holstm_cell():
        return HighOrderLSTMCell(config.hidden_size,config.num_lags,config.num_orders)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [holstm_cell() for _ in range(config.num_layers)])
    
    outputs, state  = tensor_rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def HORNN(inputs, is_training, config):
    def hornn_cell():
        return HighOrderRNNCell(config.hidden_size,config.num_lags)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [hornn_cell() for _ in range(config.num_layers)])
    
    outputs, state  = tensor_rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def TRNN(inputs, is_training, config):
    def trnn_cell():
        return EinsumTensorRNNCell(config.hidden_size, config.num_lags, config.rank_vals)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [trnn_cell() for _ in range(config.num_layers)])
    
    outputs, state  = tensor_rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs

def MTRNN(inputs, is_training, config):
    def mtrnn_cell():
        return MTRNNCell(config.hidden_size, config.num_lags, config.num_freq, config.rank_vals)
        
    cell = tf.contrib.rnn.MultiRNNCell(
        [mtrnn_cell() for _ in range(config.num_layers)])
    
    outputs, state  = tensor_rnn_with_feed_prev(cell, inputs, is_training, config)
    return outputs
