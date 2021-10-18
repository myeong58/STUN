# -*- coding: utf-8 -*-
import gym
import numpy as np
import random
import math
from time import sleep
from gym.envs.registration import register
import matplotlib
from matplotlib import pyplot as plt
from datetime import datetime
import time
import os
import sys

register(
    id='EnvTest-v0',
    entry_point='envTest_state_best:envTestEnv',
)

env = gym.make('EnvTest-v0')

NUM_BUCKETS = (50, 50) 
NUM_ACTIONS = env.action_space.n

## Creating a Q-Table for each state-action pair
q_table = np.zeros(NUM_BUCKETS + (NUM_ACTIONS,))

## Learning related constants
MIN_EXPLORE_RATE = 0.01
MIN_LEARNING_RATE = 0.1

## Defining the simulation related constants
NUM_EPISODES = int(sys.argv[1])
MAX_T = int(sys.argv[2])
DEBUG_MODE = True

num = NUM_EPISODES - 1

array_state=[]

path = "./gp_E" + sys.argv[1] + "_T" + sys.argv[2]+ datetime.today().strftime("_%H%M")

def simulate():
    ## Instantiating the learning related parameters
    learning_rate = get_learning_rate(0)
    explore_rate = get_explore_rate(0)
    discount_factor = 0.99  # since the world is unchanging

    flag = False
    for episode in range(NUM_EPISODES):
        if episode < NUM_EPISODES-10:
            obv = env.reset()
        else:
            obv = env.reset(False)
        
        state_0 = state_to_bucket(obv)
        env.ttime = []
        array_state = []
        count_bad = 0
        for t in range(MAX_T):
            # Select an action
            if episode < NUM_EPISODES - 2:
                action = select_action(state_0, explore_rate)
            else:
                action = select_action(state_0, explore_rate, flag)

            # Execute the action
            obv, reward, done, _ = env.step(action  )
            state = state_to_bucket(obv)

            best_q = np.amax(q_table[state])
            q_table[tuple(state_0) + (action,)] += learning_rate * (reward + discount_factor *(best_q) - q_table[tuple(state_0) + (action,)])
        
            state_0 = state

            # Print data
            if DEBUG_MODE:
                print("\nEpisode = %d" % episode)
                print("t = %d" % t)
                print("Action: %d" % action)
                print("State: %s" % str(state))
                print("Reward: %f" % reward)
                print("Best Q: %f" % best_q)
                print("count_bad: %d" % count_bad)
                print("")
                array_state.append(state)

            if not done:
                count_bad += 1
                if count_bad > 5:
                    break
            else:
                count_bad = 0
                

        t_name = path +"/gp_" + str(episode)
        matplotlib.use('Agg')
        ff = open(t_name + ".log", "w")
        ff.write(str(env.ttime))
        plt.plot(env.ttime, marker='.')
        plt.ylim(0, 7000)
        plt.title(str(episode)+"_")
        plt.savefig(t_name + ".png")
        plt.clf()

        plt.plot(array_state, marker='.')
        plt.legend([env.PARA[0],env.PARA[1]])
        plt.ylim(0, 55)
        plt.savefig(path + "/state" + str(episode) + ".png")
        plt.clf()

        # Update parameters
        explore_rate = get_explore_rate(episode)
        learning_rate = get_learning_rate(episode)


def select_action(state, explore_rate, f=True):
    # Select a random action
    if random.random() < explore_rate and f:
        action = env.action_space.sample()
    # Select the action with the highest q
    else:
        action = np.argmax(q_table[tuple(state)])
        #print(q_table[state])
    return action

def get_explore_rate(t):
    if t >= 24:
        return max(MIN_EXPLORE_RATE, min(1, 1.0 - math.log10((t + 1) / 25)))
    else:
        return 1.0

def get_learning_rate(t):
    if t >= 24:
        return max(MIN_LEARNING_RATE, min(0.5, 1.0 - math.log10((t + 1) / 25)))
    else:
        return 1.0

def state_to_bucket(state):
    bucket_indice = []
    for i in range(len(state)):
        if state[i] <= env.PARA_Range[i][0]:
            bucket_index = 0
        elif state[i] >= env.PARA_Range[i][2]:
            bucket_index = NUM_BUCKETS[i] - 1
        else:
            # Mapping the state bounds to the bucket array
            bound_width = env.PARA_Range[i][2] - env.PARA_Range[i][0]
            offset = (NUM_BUCKETS[i]-1)*env.PARA_Range[i][0]/bound_width
            scaling = (NUM_BUCKETS[i]-1)/bound_width
            bucket_index = int(round(scaling*state[i] - offset))
        bucket_indice.append(bucket_index)
    return tuple(bucket_indice)



if __name__ == "__main__":
    if not os.path.isdir(path):
        os.mkdir(path)

    start = time.time()
    simulate()
    matplotlib.use('Agg')

    f = open(path +"/state.log", "w")
    f.write("def = "+ str(env.def_bench) + " upper = "+ str(env.upper_bench) + " under = " + str(env.under_bench))
    f.write("\nbest bench : " + str(env.best))
    f.write("\nresult") 
    f.write("\n" + str(env.PARA[0])+ "=" + str(env.best_state[0]))
    f.write("\n" + str(env.PARA[1])+ "=" + str(env.best_state[1]))
    f.write("\ntime : " + str(time.time() - start))
    f.close()

    print("time : ", time.time() - start)
