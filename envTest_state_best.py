#import math
import gym
import subprocess
import random
import os
from gym import spaces, logger
#from gym.utils import seeding
import numpy as np

paramters = {"kernel.sched_latency_ns" : [100000, 24000000, 1000000000], 
"kernel.sched_migration_cost_ns" :[0, 500000, 1000000000],
"kernel.sched_min_granularity_ns" : [100000, 3000000, 1000000000],
"kernel.sched_nr_migrate" : [0, 32, 1000],
"kernel.sched_rr_timeslice_ms" : [0, 100, 1000],
"kernel.sched_rt_period_us" : [900000, 1000000,1000000],
"kernel.sched_rt_runtime_us" : [0, 950000, 1000000],
"kernel.sched_cfs_bandwidth_slice_us" : [0, 5000, 1000000],
"kernel.sched_wakeup_granularity_ns" : [0, 4000000, 1000000000],
"kernel.sched_time_avg_ms":[0, 1000, 1000]}


class envTestEnv(gym.Env):
    def __init__(self):
        self.resetdefault()
        self.p="-B"
        self.def_bench = self.get_next_result()
        self.result = self.def_bench
        self.best = self.def_bench
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Discrete(4)
        self.ttime=[]
        self.PARA_Range = []
        
        self.para_action = [20000000, 20000000]   

        self.upper_bench = int(round(self.def_bench * 1.2, 2)) 
        self.under_bench = int(round(self.def_bench * 0.8, 2))
        
        print("def = ", self.def_bench, " upper = ", self.upper_bench, " under = ", self.under_bench)
        self.PARA = ["kernel.sched_latency_ns", "kernel.sched_wakeup_granularity_ns"]

        self.PARA_Range.append([paramters[self.PARA[0]][0],paramters[self.PARA[0]][1],paramters[self.PARA[0]][2]])
        self.PARA_Range.append([paramters[self.PARA[1]][0],paramters[self.PARA[1]][1],paramters[self.PARA[1]][2]])

        self.state = [self.PARA_Range[0][1],self.PARA_Range[1][1]]
        self.best_state = self.state

    def resetdefault(self):
        cmd="sysctl -w kernel.sched_autogroup_enabled=1 kernel.sched_cfs_bandwidth_slice_us=5000 kernel.sched_child_runs_first=0 kernel.sched_latency_ns=24000000 kernel.sched_migration_cost_ns=500000 kernel.sched_min_granularity_ns=3000000 kernel.sched_nr_migrate=32 kernel.sched_rr_timeslice_ms=100 kernel.sched_rt_period_us=1000000 kernel.sched_rt_runtime_us=950000 kernel.sched_schedstats=0 kernel.sched_time_avg_ms=1000 kernel.sched_tunable_scaling=1 kernel.sched_wakeup_granularity_ns=4000000"
        os.system (cmd)
        return 0


    def step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid" % (action, type(action))     
        
        if action == 0: 
            pass
        elif action == 1:
            self.para_action[0] *= (-1) 
        else:
            self.para_action[1] *= (-1)

        self.state[0] = self.change_para(self.PARA[0], self.PARA_Range[0], self.state[0], self.para_action[0])

        self.state[1] = self.change_para(self.PARA[1], self.PARA_Range[1], self.state[1], self.para_action[1])

        next_result = self.get_next_result()
        self.ttime.append(next_result)
		
        if next_result > self.best:
            self.best = next_result
            self.best_state = self.state[:]

        if next_result > self.upper_bench:
            reward = 200
            done = True
        elif next_result < self.under_bench:
            reward = -50
            done = False 
        elif next_result > self.result:
            reward = 100
            done = True
        else:
            reward = 0
            done = True

        self.result = next_result
        print("best bench : ", self.best, "best_state = ", self.best_state)
        return np.array(self.state), reward, done, {}

    def reset(self, f=True):
        if f:
            tmp1 = random.choice(range(self.PARA_Range[0][0],self.PARA_Range[0][2],19998000))
            tmp2 = random.choice(range(self.PARA_Range[1][0],self.PARA_Range[1][2],20000000))
        else:
            tmp1 = self.best_state[0]
            tmp2 = self.best_state[1]
        self.state[0] = self.change_para(self.PARA[0],self.PARA_Range[0],tmp1,0)
        self.state[1] = self.change_para(self.PARA[1],self.PARA_Range[1],tmp2,0)

        self.result = self.best
        return np.array(self.state)

    def get_next_result(self):
        #benchcmd = './hackbench.x64 8 process 3000 |grep Time |awk \'{print $2}\''
        benchcmd = "sysbench --test=threads --threads=256 --time=1 run | grep 'events:' | awk '{print $5}'"

        cmd="schedtool " + self.p + " -e " + benchcmd
        print(cmd)

        p2 = int(subprocess.check_output(cmd, shell=True, encoding='utf-8'))
        print(p2)
        return p2


    def change_para(self, para, para_range, num, a):
        if num + a <= para_range[0]:
            next_num = para_range[0]
        elif num + a >= para_range[2]:
            next_num = para_range[2]
        else:
            next_num = num + a
        para_val = next_num
        tunecmd = "sysctl -w " + para + "=" + str(para_val)
        subprocess.run(tunecmd, stdout=subprocess.PIPE, shell=True)
        print("PARA = " + para + " = ", para_val , '\n')
        return next_num
