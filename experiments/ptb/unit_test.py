
# coding: utf-8

# ## LSTM cell 
# $$ i, j, f, o = Wx + Uh + b \\
#    [i,j,f,o] = [W,U,1][x,h,b]^\top$$
#   i = input_gate, j = new_input, f = forget_gate, o = output_gate
# 

# In[1]:

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import math
# %load unit_test.py
import tensorflow as tf
import numpy as np


from tensorflow.python.framework import ops
from tensorflow.python.framework import tensor_shape
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import clip_ops
from tensorflow.python.ops import embedding_ops
from tensorflow.python.ops import init_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import nn_ops
from tensorflow.python.ops import variable_scope as vs

from tensorflow.python.ops.math_ops import sigmoid
from tensorflow.python.ops.math_ops import tanh

from tensorflow.python.platform import tf_logging as logging
from tensorflow.python.util import nest

import sys, os
sys.path.append(os.path.abspath('../../'))

import tensornet
from tensorflow.python.ops.rnn_cell import *


class TensorBasicLSTMCell(LSTMCell):
    """Tensor Factorized Long short-term memory unit (LSTM) recurrent network cell.

    """
    def __init__(self, num_units, **kwargs):
        super(TensorBasicLSTMCell, self).__init__(num_units)
        self._inp_modes = kwargs['inp_modes']
        self._out_modes = kwargs['out_modes']
        self._mat_ranks = kwargs['mat_ranks']
            
    def __call__(self, inputs, state, scope=None):
        """Long short-term memory cell (LSTM)."""
        with vs.variable_scope(scope or type(self).__name__):  # "BasicLSTMCell"
            # Parameters of gates are concatenated into one multiply for efficiency.
            if self._state_is_tuple:
                c, h = state
            else:
                c, h = array_ops.split(1, 2, state)     
        
            i = linear_tt([inputs, h], self._num_units, self._inp_modes, self._out_modes, self._mat_ranks, bias =True, scope = "i")  
            j = linear_tt([inputs, h], self._num_units, self._inp_modes, self._out_modes, self._mat_ranks, bias =True, scope = "j")   
            f = linear_tt([inputs, h], self._num_units, self._inp_modes, self._out_modes, self._mat_ranks, bias =True, scope = "f")   
            o = linear_tt([inputs, h], self._num_units, self._inp_modes, self._out_modes, self._mat_ranks, bias =True, scope = "o")   
        
#             concat = _linear([inputs, h], 4 * self._num_units, True)
#             # i = input_gate, j = new_input, f = forget_gate, o = output_gate
#             i , j, f, o = array_ops.split(1, 4, concat)

            new_c = (c * sigmoid(f + self._forget_bias) + sigmoid(i) *
                     self._activation(j))
            new_h = self._activation(new_c) * sigmoid(o)

            if self._state_is_tuple:
                new_state = LSTMStateTuple(new_c, new_h)
            else:
                new_state = array_ops.concat(1, [new_c, new_h])
            return new_h, new_state

def linear_tt(args, output_size, inp_modes, out_modes, mat_ranks, bias, bias_start=0.0, scope=None):
    """wrapper for factorization layer"""
    # args = [x, h] solve y = Wx + Uh + b
    if args is None or (nest.is_sequence(args) and not args):
        raise ValueError("`args` must be specified")
    if not nest.is_sequence(args):
        args = [args]

    # Calculate the total size of arguments on dimension 1.
    total_arg_size = 0
    shapes = [a.get_shape().as_list() for a in args]
    for shape in shapes:
        if len(shape) != 2:
            raise ValueError("Linear is expecting 2D arguments: %s" % str(shapes))
        if not shape[1]:
            raise ValueError("Linear expects shape[1] of arguments: %s" % str(shapes))
        else:
            total_arg_size += shape[1]
    dtype = [a.dtype for a in args][0]

    #sin = array_ops.concat(1, args)  batch_size* (x_dim + h_dim)
    with vs.variable_scope(scope or "Linear"):
#         matrix_x = vs.get_variable("Matrix_x", [args[0].get_shape().as_list()[1], output_size])
#         matrix_h = vs.get_variable("Matrix_h", [args[1].get_shape().as_list()[1], output_size])
#         res_x = math_ops.matmul(args[0], matrix_x) #tensornet.layers.tt(args[0], inp_modes['x'], out_modes['x'], mat_ranks['x'])
#         res_h = math_ops.matmul(args[1], matrix_h)#tensornet.layers.tt(args[1], inp_modes['h'], out_modes['h'], mat_ranks['h'])
#         res = res_x +  res_h #batch_size*out_size
        res_x = tensornet.layers.mf_rnn(args[0],  inp_modes['x'], out_modes['x'], mat_ranks['x'], scope ="x")
        res_h = tensornet.layers.mf_rnn(args[1],  inp_modes['h'], out_modes['h'], mat_ranks['h'], scope ="h")
        res = res_x +  res_h
        if not bias:
            return res
        bias_term = vs.get_variable("Bias", [output_size],dtype=dtype,initializer=init_ops.constant_initializer(
                bias_start, dtype=dtype))
      
    return res + bias_term


    
def _linear(args, output_size, bias, bias_start=0.0, scope=None):
    """Linear map: sum_i(args[i] * W[i]), where W[i] is a variable.

    Args:
      args: a 2D Tensor or a list of 2D, batch x n, Tensors.
      output_size: int, second dimension of W[i].
      bias: boolean, whether to add a bias term or not.
      bias_start: starting value to initialize the bias; 0 by default.
      scope: VariableScope for the created subgraph; defaults to "Linear".

    Returns:
      A 2D Tensor with shape [batch x output_size] equal to
      sum_i(args[i] * W[i]), where W[i]s are newly created matrices.

    Raises:
      ValueError: if some of the arguments has unspecified or wrong shape.
    """
    if args is None or (nest.is_sequence(args) and not args):
        raise ValueError("`args` must be specified")
    if not nest.is_sequence(args):
        args = [args]

    # Calculate the total size of arguments on dimension 1.
    total_arg_size = 0
    shapes = [a.get_shape().as_list() for a in args]
    for shape in shapes:
        if len(shape) != 2:
            raise ValueError("Linear is expecting 2D arguments: %s" % str(shapes))
        if not shape[1]:
            raise ValueError("Linear expects shape[1] of arguments: %s" % str(shapes))
        else:
            total_arg_size += shape[1]
    dtype = [a.dtype for a in args][0]

    # Now the computation.
    with vs.variable_scope(scope or "Linear"):
        matrix = vs.get_variable(
            "Matrix", [total_arg_size, output_size], dtype=dtype)
        if len(args) == 1:
            res = math_ops.matmul(args[0], matrix)
        else:
            res = math_ops.matmul(array_ops.concat(1, args), matrix)
        if not bias:
            return res
        bias_term = vs.get_variable(
            "Bias", [output_size],
            dtype=dtype,
            initializer=init_ops.constant_initializer(
                bias_start, dtype=dtype))
    return res + bias_term



if __name__ == '__main__':
    np.random.seed(1)
    # the size of the hidden state for the lstm (notice the lstm uses 2x of this amount so actually lstm will have state of size 2)
    size = 12
    # 2 different sequences total
    batch_size= 2
    # the maximum steps for both sequences is 10
    n_steps = 10
    # each element of the sequence has dimension of 5
    seq_width = 2

    # the first input is to be stopped at 4 steps, the second at 6 steps
    e_stop = np.array([4,6])
    
    # factorize the inp
    inp_modes = {}
    out_modes = {}
    mat_ranks = {}
    # input weights
    inp_modes['x'] = np.array([1, 2, 1, 1], dtype='int32') # product as seq_width
    out_modes['x'] = np.array([1, 4, 3, 1], dtype='int32') # product as num_units (size)
    mat_ranks['x'] = 2
    #mat_ranks['x'] = np.array([1, 2, 2, 2, 1], dtype='int32')
    # hidden state weights
    inp_modes['h'] = np.array([1, 4, 3, 1], dtype='int32') # seq_width
    out_modes['h'] = np.array([1, 4, 3, 1], dtype='int32') # 4 * num_units
    mat_ranks['h'] = 2

    #mat_ranks['h'] = np.array([1, 2, 2, 2, 1], dtype='int32') 
    
    
    initializer = tf.random_uniform_initializer(-1,1)

    # the sequences, has n steps of maximum size
    seq_input = tf.placeholder(tf.float32, [n_steps, batch_size, seq_width], name="placeholder/seqs")
    # what timesteps we want to stop at, notice it's different for each batch hence dimension of [batch]
    early_stop = tf.placeholder(tf.int32, [batch_size], name="placeholder/stops" )

    # inputs for rnn needs to be a list, each item being a timestep.
    # we need to split our input into each timestep, and reshape it because split keeps dims by default
    # input = [n_steps, batch_size, seq_width]
    inputs = [tf.reshape(i, (batch_size, seq_width)) for i in tf.split(0, n_steps, seq_input)]
    
    """Shape checker"""
#     init = tf.initialize_all_variables()
#     sess = tf.InteractiveSession()
#     sess.run(init)
#     print(sess.run(tf.shape(inputs), feed_dict = {seq_input: np.ones((n_steps, batch_size, seq_width)) }))
#     sess.close()
    
    cell = TensorBasicLSTMCell(size, inp_modes=inp_modes, out_modes=out_modes, mat_ranks=mat_ranks, 
                          input_size = seq_width , initializer=initializer)        
        
    initial_state = cell.zero_state(batch_size, tf.float32)

    # ========= This is the most important part ==========
    # output will be of length 4 and 6
    # the state is the final state at termination (stopped at step 4 and 6)
    outputs, state = tf.nn.rnn(cell, inputs, initial_state=initial_state, sequence_length=early_stop)

    # usual crap
    iop = tf.initialize_all_variables()
    session = tf.Session()
    session.run(iop)
    feed = {early_stop:e_stop, seq_input:np.random.rand(n_steps, batch_size, seq_width).astype('float32')}

    print("outputs, should be 2 things one of length 4 and other of 6")
    outs = session.run(outputs, feed_dict=feed)
    for xx in outs:
        print(xx)

    print("states, 2 things total both of size 2, which is the size of the hidden state")
    st = session.run(state, feed_dict=feed)
    print(st)

