from __future__ import division
from __future__ import print_function

import time
import numpy as np
import pandas as pd
import tensorflow as tf
import sys, os
import argparse

os.sys.path.append('../../')
from models.seq_model_lstm import *
from models.seq_input import *

#os.environ["CUDA_VISIBLE_DEVICES"]=""
flags = tf.flags
logging = tf.logging

flags.DEFINE_string(
    "model", "small",
    "A type of model. Possible options are: small, medium, large.")
flags.DEFINE_string("data_path", "/Users/roseyu/Documents/Python/lorenz.pkl",
                    "Where the training/test data is stored.")
flags.DEFINE_string("save_path", "/Users/roseyu/Documents/Python/log/lorenz/basic_lstm/",
                    "Model output directory.")
flags.DEFINE_bool("use_fp16", False,
                  "Train using 16-bit floats instead of 32bit floats")
flags.DEFINE_bool("use_error_prop", False,
                  "Feed previous output as input in RNN")

flags.DEFINE_integer('hidden_size', 256, "number of hidden unit")
flags.DEFINE_float('learning_rate', 1e-3, "learning rate of trainig")
flags.DEFINE_integer("num_steps", 12, "output sequence length")
FLAGS = flags.FLAGS



class TestConfig(object):
    """Tiny config, for testing."""
    burn_in_steps = 5
    init_scale = 0.1
    learning_rate = 1.0
    max_grad_norm = 1
    num_layers = 1
    num_steps =12
    horizon = 1
    hidden_size = 64
    max_epoch = 20
    max_max_epoch = 50
    keep_prob = 1.0
    lr_decay = 0.9
    batch_size = 5
    vocab_size = 1340
    rand_init = True

def run_epoch(session, model, eval_op=None, verbose=False):
    """Runs the model on the given data."""
    start_time = time.time()
    costs = 0.0
    iters = 0
    predicts = []
    targets = []
    state = session.run(model.initial_state)

    fetches = {
        "cost": model.cost,
        "predict":model.predict,
        "input":model.input.input_data,
        "target":model.input.targets,
        "final_state": model.final_state,
    }
    if eval_op is not None:
        fetches["eval_op"] = eval_op

    for step in range(model.input.epoch_size):
        feed_dict = {}
       #  for i, (c, h) in enumerate(model.initial_state):
            # feed_dict[c] = state[i].c
            # feed_dict[h] = state[i].h
        for i, s in enumerate(model.initial_state):
            feed_dict[s] = state[i]

        vals = session.run(fetches, feed_dict)
        cost = vals["cost"]
        target = vals["target"]
        predict = vals["predict"]

        ##print("cost at step {0}: {1}".format(step, cost))
        state = vals["final_state"]
        predicts.append(predict)
        targets.append(target)

#         if step % 500 == 0:
          # #for i in vals["input"]:
              # #print("step", step, "input\n", vals["input"][0,0:5])
          # #for i in vals["target"]:
              # print("step", step, "target\n", vals["target"][0,0:5])
          # #for i in predict
              # print("step", step, "predicts\n", predict[0:5])

        costs += cost
        iters += model.input.num_steps

        if verbose and step % (model.input.epoch_size // 10) == 10:
            print("%.3f error: %.3f speed: %.0f wps" %
                  (step * 1.0 / model.input.epoch_size, costs / step,
                   iters * model.input.batch_size / (time.time() - start_time)))

    predicts = np.stack(predicts,1).reshape(-1,model.input.input_size) # test_len x input_size
    targets = np.stack(targets,1).reshape(-1,model.input.input_size) # test_len x input_size
    final_cost = np.sqrt(costs/model.input.epoch_size)
    final_rslt = (targets, predicts) 
    
    return final_cost, final_rslt


def main(_):
    if not FLAGS.data_path:
        raise ValueError("Must set --data_path to PTB data directory")

    raw_data = seq_raw_data(FLAGS.data_path)#seq raw data
    train_data, valid_data, test_data = raw_data
    config = TestConfig()

    config.learning_rate = FLAGS.learning_rate
    config.hidden_size = FLAGS.hidden_size
    config.num_steps = FLAGS.num_steps

    eval_config = TestConfig()
    eval_config.hidden_size = FLAGS.hidden_size
    eval_config.batch_size = 1
    eval_config.num_steps = 1

    if FLAGS.use_error_prop:
        print("Using error prop in RNN!")

    with tf.Graph().as_default():
        initializer = tf.random_uniform_initializer(-config.init_scale,
                                                    config.init_scale)
        with tf.name_scope("Train"):
            train_input = PTBInput(is_training=True, config=config, data=train_data, name="TrainInput")
            with tf.variable_scope("Model", reuse=None, initializer=initializer):
                m = PTBModel(is_training=True, config=config, input_=train_input, use_error_prop=False)
            tf.summary.scalar("Training_Loss", m.cost)
            tf.summary.scalar("Learning_Rate", m.lr)

        with tf.name_scope("Valid"):
            valid_input = PTBInput(is_training=False, config=config, data=valid_data, name="ValidInput")
            with tf.variable_scope("Model", reuse=True, initializer=initializer):
                mvalid = PTBModel(is_training=False, config=config, input_=valid_input, use_error_prop=FLAGS.use_error_prop)
            tf.summary.scalar("Validation_Loss", mvalid.cost)

        with tf.name_scope("Test"):
            test_input = PTBInput(is_training=False, config=eval_config, data=test_data, name="TestInput")
            with tf.variable_scope("Model", reuse=True, initializer=initializer):
                mtest = PTBModel(is_training=False, config=eval_config,
                                 input_=test_input, use_error_prop=FLAGS.use_error_prop)
            tf.summary.scalar("Test_Loss", mtest.cost)

        gpu_config = tf.ConfigProto()
        gpu_config.gpu_options.per_process_gpu_memory_fraction=0.1
        gpu_config.gpu_options.allow_growth = True
        sv = tf.train.Supervisor(logdir=FLAGS.save_path)
        with sv.managed_session(config = gpu_config) as session:
            valid_err_old = float("inf")
            for i in range(config.max_max_epoch):
                lr_decay = config.lr_decay ** max(i + 1 - config.max_epoch, 0.0)
                m.assign_lr(session, config.learning_rate * lr_decay)

                print("Epoch: %d Learning rate: %.3f" % (i + 1, session.run(m.lr)))
                train_err, _ = run_epoch(session, m, eval_op=m.train_op,
                                             verbose=True)
                print("Epoch: %d Train Error: %.3f" % (i + 1, train_err))
                valid_err, _ = run_epoch(session, mvalid)
                print("Epoch: %d Valid Error: %.3f" % (i + 1, valid_err))

                # early stopping
                if valid_err_old <= valid_err:
                    print("Early stopping after %d epoch" % i)
                    break
                valid_err_old = valid_err

            
            test_err, test_rslt = run_epoch(session, mtest)
            print("Test Error: %.3f" % test_err)
            np.save(FLAGS.save_path+"predict.npy", test_rslt)

            # Write config file
            with open(FLAGS.save_path+"config_error.out", 'w') as f:
                f.write('hidden_size:'+ str(config.hidden_size) + '\t'+ 'num_steps:'+ str(config.num_steps) +
                        '\t'+ 'learning_rate:'+ str(config.learning_rate) + '\n')
                f.write('train_error:'+ str(train_err) + '\t' + 'valid_error:'+ str(valid_err) + 
                        '\t'+ 'test_error:'+ str(test_err) + '\n')


            if FLAGS.save_path:
                print("Saving model to %s." % FLAGS.save_path)
                sv.saver.save(session, FLAGS.save_path, global_step=sv.global_step)


if __name__ == "__main__":
    tf.app.run()