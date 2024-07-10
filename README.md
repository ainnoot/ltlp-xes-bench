# ltlf-xes-bench

Data to generate LTLp formulae from a set of logs, according to the following:

* Mine a Declare model from a XES log
* Add Declare assumptions
* Add a formula ensuring a lower bound

## Usage

```
usage: mine.py [-h] [-l L] [-p P] [-k K] log_folder output_folder
mine.py: error: the following arguments are required: log_folder, output_folder
```

### Example
```
python3 mine.py logs formulae -l 16,32,64 -p 0.20,0.40,0.60 -k 5
```

This creates formulae starting from event logs in the `logs` folder, generating (satisfiable) DECLARE specifications, (sampling 20%, 40% and 60% of available constraints) that admit models longer than 16, 32, 64. For each (length, num. constraint) configuration, 5 specifications are generated. Generated files follow the naming convention `[log]_[num-constraints]_[model-length]_[idx].ltlf`.
