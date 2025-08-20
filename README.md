# Digital Twin for Aerospace Production Line (Discrete Event Simulation)

A minimal yet defensible **Discrete Event Simulation (DES)** of a 3-station aerospace assembly line using `simpy`. 
It models:
- Inter-arrival of parts
- Processing at three serial stations
- Finite buffer between stations (configurable)
- Metrics: throughput, station utilization, average queue lengths, WIP, cycle time distribution

## Why this matters
This mirrors typical digital-twin questions: **Where is the bottleneck? How large should buffers be? What is the max throughput?**

## Quick start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python simulation.py
```

Outputs:
- `results/throughput_vs_buffer.png`
- `results/utilization.png`
- `results/summary.json`
- `results/run_log.csv`

## Experiment knobs
Edit the `CONFIG` at the top of `simulation.py`:
- `SIM_TIME`: total simulated minutes
- `ARRIVAL_MEAN`: mean inter-arrival time (min)
- `PROC_MEANS`: mean processing time per station (min)
- `BUFFER_RANGE`: list of buffer capacities to test (e.g., `[0, 2, 5, 10]`)

## Interview talking points
- Explain **DES** (events, queues, resources) and how it helps validate **buffer sizing** and **throughput** before any shop-floor change.
- Show **utilization** proves the bottleneck — the highest-utilized station constrains throughput.
- Connect to **Industry 4.0**: live IoT data can sync with the simulation to turn this into a *living digital twin* (calibrated in real time).
---

## Interview Cheat Sheet (STAR)

**Situation**: Aerospace assembly line with uncertain bottlenecks and inconsistent throughput.  
**Task**: Determine optimal buffer sizing and identify constraints before physical changes.  
**Action**: Built a SimPy-based DES of 3 serial stations with finite buffers, ran sensitivity analysis over buffer capacities and cycle times, and collected KPIs (throughput, utilization, WIP).  
**Result**: Quantified throughput uplift with modest buffer increases; identified Station 2 as bottleneck at lower buffers; produced plots and logs to justify recommendations.
