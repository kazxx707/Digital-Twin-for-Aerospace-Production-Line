import simpy
import random
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, json

# ------------------ CONFIG ------------------
CONFIG = {
    "SIM_TIME": 8 * 60,           # minutes (8 hours)
    "WARMUP": 60,                 # minutes
    "ARRIVAL_MEAN": 5.0,          # mean inter-arrival time (min)
    "PROC_MEANS": [6.0, 7.0, 5.0],# mean process times per station (min)
    "BUFFER_RANGE": [0, 2, 5, 10]
}

random.seed(42)
np.random.seed(42)

# ------------------ MODEL -------------------
class Station:
    def __init__(self, env, name, mean_proc):
        self.env = env
        self.name = name
        self.resource = simpy.Resource(env, capacity=1)
        self.mean_proc = mean_proc
        self.busy_time = 0.0
        self.last_start = None

    def process(self):
        pt = random.expovariate(1.0 / self.mean_proc)
        self.last_start = self.env.now
        yield self.env.timeout(pt)
        self.busy_time += pt
        self.last_start = None

def source(env, arrival_mean, in_queue):
    i = 0
    while True:
        i += 1
        inter = random.expovariate(1.0 / arrival_mean)
        yield env.timeout(inter)
        yield in_queue.put({"id": i, "t_arrive": env.now})

def flow(env, stations, q01, q12, out_list, log_rows):
    while True:
        # from source queue to station 0
        part = yield q01.get()
        with stations[0].resource.request() as req0:
            yield req0
            t_start = env.now
            yield env.process(stations[0].process())
            t_end = env.now
        # into buffer to station 1
        yield q12.put({"id": part["id"], "t_s0_end": t_end})

        # station 1 takes from buffer
        part2 = yield q12.get()
        with stations[1].resource.request() as req1:
            yield req1
            t1s = env.now
            yield env.process(stations[1].process())
            t1e = env.now

        # directly to station 2 (no extra buffer at end)
        with stations[2].resource.request() as req2:
            yield req2
            t2s = env.now
            yield env.process(stations[2].process())
            t2e = env.now

        out_list.append({"id": part2["id"], "t_out": t2e})
        log_rows.append([part2["id"], t_start, t_end, t1s, t1e, t2s, t2e])

def run_once(buffer_cap):
    env = simpy.Environment()
    s0 = Station(env, "S0", CONFIG["PROC_MEANS"][0])
    s1 = Station(env, "S1", CONFIG["PROC_MEANS"][1])
    s2 = Station(env, "S2", CONFIG["PROC_MEANS"][2])
    q01 = simpy.Store(env, capacity=buffer_cap if buffer_cap > 0 else 1_000_000)  # large if 0 implies unlimited before S0
    q12 = simpy.Store(env, capacity=buffer_cap)
    out_list = []
    log_rows = []

    env.process(source(env, CONFIG["ARRIVAL_MEAN"], q01))
    env.process(flow(env, [s0, s1, s2], q01, q12, out_list, log_rows))
    env.run(until=CONFIG["SIM_TIME"])

    # metrics
    prod = [r for r in out_list if r["t_out"] >= CONFIG["WARMUP"]]
    throughput_per_min = len(prod) / (CONFIG["SIM_TIME"] - CONFIG["WARMUP"])
    util = [(s.busy_time / CONFIG["SIM_TIME"]) for s in [s0, s1, s2]]
    return {
        "buffer": buffer_cap,
        "throughput_per_min": throughput_per_min,
        "utilization": util,
        "log": log_rows
    }

def main():
    os.makedirs("results", exist_ok=True)
    summaries = []
    util_rows = []
    log_all = []

    for b in CONFIG["BUFFER_RANGE"]:
        res = run_once(b)
        summaries.append({"buffer": b, "throughput_per_min": res["throughput_per_min"]})
        util_rows.append({"buffer": b, "S0": res["utilization"][0], "S1": res["utilization"][1], "S2": res["utilization"][2]})
        for row in res["log"]:
            log_all.append([b] + row)

    df_sum = pd.DataFrame(summaries)
    df_util = pd.DataFrame(util_rows)
    df_log = pd.DataFrame(log_all, columns=["buffer","id","t0_start","t0_end","t1_start","t1_end","t2_start","t2_end"])
    df_sum.to_json("results/summary.json", orient="records", indent=2)
    df_log.to_csv("results/run_log.csv", index=False)

    # Plot throughput vs buffer
    plt.figure()
    plt.plot(df_sum["buffer"], df_sum["throughput_per_min"], marker="o")
    plt.xlabel("Buffer capacity between S0-S1 and S1-S2")
    plt.ylabel("Throughput (parts/minute)")
    plt.title("Throughput vs Buffer Capacity")
    plt.grid(True, which="both", linestyle="--", alpha=0.4)
    plt.savefig("results/throughput_vs_buffer.png", bbox_inches="tight")
    plt.close()

    # Utilization at max buffer (last run)
    plt.figure()
    last_util = df_util.iloc[-1][["S0","S1","S2"]].values
    plt.bar(["S0","S1","S2"], last_util)
    plt.ylabel("Utilization")
    plt.ylim(0,1)
    plt.title(f"Station Utilization (buffer={CONFIG['BUFFER_RANGE'][-1]})")
    plt.savefig("results/utilization.png", bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    main()