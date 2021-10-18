import numpy
import os
import time

def resetdefault():
	cmd="sysctl -w kernel.sched_autogroup_enabled=1 kernel.sched_cfs_bandwidth_slice_us=5000 kernel.sched_child_runs_first=0 kernel.sched_latency_ns=24000000 kernel.sched_migration_cost_ns=500000 kernel.sched_min_granularity_ns=3000000 kernel.sched_nr_migrate=32 kernel.sched_rr_timeslice_ms=100 kernel.sched_rt_period_us=1000000 kernel.sched_rt_runtime_us=950000 kernel.sched_schedstats=0 kernel.sched_tunable_scaling=1 kernel.sched_wakeup_granularity_ns=4000000"
	os.system (cmd)
	return 0

#policy=["-N", "-D", "-B", "-Fp99", "-Rp99"]
policy=["-N", "-D", "-B"]

paramters = {"kernel.sched_latency_ns" : [100000, 24000000, 1000000000], 
"kernel.sched_migration_cost_ns" :[0, 500000, 1000000000],
"kernel.sched_min_granularity_ns" : [100000, 3000000, 1000000000],
"kernel.sched_nr_migrate" : [0, 32, 1000],
"kernel.sched_rr_timeslice_ms" : [0, 100, 1000],
"kernel.sched_rt_period_us" : [950000, 1000000,1000000000],
"kernel.sched_rt_runtime_us" : [0, 950000, 1000000],
"kernel.sched_wakeup_granularity_ns" : [0, 4000000, 1000000000],
"kernel.sched_cfs_bandwidth_slice_us" : [1, 5000, 1000000000]}
outfn="sys_out.csv"

os.system ("rm -f "+ outfn)

benchcmd="sysbench --test=threads --threads=256 --time=1 run | grep 'events:' | awk '{print $5}'"

start = time.time()

for p in policy:
    for para in paramters:
        resetdefault()
        for i in range(3):
            cmd="sysctl -w " + para + "=" + str(paramters[para][i])
            os.system (cmd)

            cmd="echo -n '"+ p +" ' >> "+ outfn
            os.system (cmd)

            cmd="echo -n '" + para + " "+ str(paramters[para][i]) +" ' >> "+ outfn
            os.system (cmd)

            cmd="timeout 5 schedtool "+ p +" -e "+ benchcmd +" >> "+ outfn
            os.system (cmd)	

print("time : ", time.time() - start)
# print( policy[minidx] )

resetdefault()
ff = open("./sys_filtering.txt","w")

with open("sys_out.csv","r") as f:
    for i in range(27):
        line1 = f.readline().split()
        line2 = f.readline().split()
        line3 = f.readline().split()
        per = (float(line3[3]) - float(line1[3])) / float(line1[3]) * 100
        if abs(per) > 20:
            s = str(line1[0]) + " " + str(line1[1]) + " " + str(format(per,".2f"))
            print(s)
            ff.write(s + "\n")

