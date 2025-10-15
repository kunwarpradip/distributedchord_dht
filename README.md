# Chord DHT - Experiments

Python implementation of Chord Distributed Hash Table with performance evaluation.

## Available Experiments

### 1. Simple Experiment (`experiment_1.py`)
Basic 4-node ring with mixed GET/SET workload.

**Run:**
```bash
python3 experiment_1.py
```

**Output:** `experiment_1.json` in current directory

---

### 2. Comprehensive Experiments (`run_all_experiments.py`)
Three experiments evaluating Chord DHT performance:

1. **Scaling** - Tests 2-256 nodes for O(log N) validation
2. **WAN Latency** - Measures impact of 5-20ms network delay
3. **Node Failures** - Tests fault tolerance and recovery

**Run all:**
```bash
python3 run_all_experiments.py
```

**Run individual:**
```bash
python3 run_all_experiments.py --experiment 1  # Scaling
python3 run_all_experiments.py --experiment 2  # WAN
python3 run_all_experiments.py --experiment 3  # Node Failures
```

---


## Results Location

| Experiment | Output File | Location |
|------------|-------------|----------|
| Simple | `experiment_1.json` | Current directory |
| Scaling | `experiment_scaling.json` | `results/` |
| WAN Latency | `experiment_wan.json` | `results/` |
| Node Failures | `experiment_node_failures.json` | `results/` |
| Visualization | `experiments_summary.png` | `plots/` |

---

## License

See [LICENSE](LICENSE)
