# RENEWABLES IN ELECTRICITY MARKETS: ASSIGMENT 2

## Introduction
This repository contains the code for Assignment 2 of the “Renewables in Electricity Markets” course (Spring 2025, DTU). It is split into two parts:

First Task: Optimal day-ahead and balancing-market bidding for a price-taking wind farm under one-price and two-price imbalance settlement schemes, including ex-post validation, sensitivity analysis, and risk-averse CVaR optimization.

Second Task: Bidding stochastic flexible-load capacity into the FCR-D UP ancillary service market under a P90 availability requirement, using ALSO-X and CVaR methods, plus a sensitivity study on the P90 level.

IMPORTANT: To run this program, make sure you are in the following directory in your terminal:
```
Ren_in_Elec_Markets\Assignment2
```
## First Task

This repository contains implementations of optimal bidding strategies for electricity producers in day-ahead and balancing markets under one-price and two-price imbalance settlement schemes.

### Table of Contents
1. [Project Description](#project-description)
2. [Folder Structure](#folder-structure)
3. [Usage](#usage)
4. [Analysis Tools](#analysis-tools)

### Project Description
This project implements mathematical optimization models for electricity producers to:
- Determine optimal bids for the day-ahead market
- Account for production uncertainty and imbalance costs
- Compare one-price and two-price imbalance settlement schemes
- Perform risk analysis and sensitivity testing

The models are implemented using Gurobi optimization solver and Python.

### Folder Structure
```
first_task/
├── input_data.py # Data loading and scenario generation
├── model_one_price.py # One-price imbalance scheme model
├── model_two_price.py # Two-price imbalance scheme model
├── expost_analysis.py # Cross-validation and out-of-sample testing
├── risk_analysis.py # Risk-averse optimization with CVaR
├── sensitivity_expost.py # Sensitivity analysis tools
├── plotting.py # Visualization functions
└── main.py # Main execution script
└── main_risk.py # Task 1.4 execution script
```

### Usage
For Tasks 1.1 and 1.2 run the main script with either pricing scheme:
```
python -m first_task.main one_price
python -m first_task.main two_price
```
In order to plot a comparison between the one price and two price schemes you also need to specify a valid model, although it will not be considered at the moment of running the program. 

For Task 1.3, in case you want to run only expost analysis for one of the price schemes you need to uncoment the specified block of code on 'main.py' and run specifying the price scheme:
```
python -m first_task.main one_price
python -m first_task.main two_price
```
For Task 1.3, to run the sensitivity analysis on the insample size run specifying the price scheme:
```
python -m first_task.sensitivity_expost one_price
python -m first_task.sensitivity_expost two_price
```
For Task 1.4 run the main_risk script with either pricing scheme:
```
python -m first_task.main_risk one_price
python -m first_task.main_risk two_price
```

### Analysis Tools

#### ExPost Analysis
- Performs cross-validation to evaluate model performance
- Compares in-sample vs out-of-sample profits
- Calculates expected imbalances and profits

### Sensitivity Analysis
- Tests model performance with different in-sample sizes

- Evaluates stability of results

- Produces visualizations of sensitivity

#### Risk Analysis
- Incorporates Conditional Value-at-Risk (CVaR)
- Allows risk-averse optimization
- Adjustable risk parameters:
  - `alpha`: Confidence level (e.g., 0.95)
  - `beta`: Risk aversion coefficient (0-1)



## Second Task
This part, included in the repository, addresses bidding stochastic flexible‐load capacity into the FCR-D UP ancillary service market under a P90 availability requirement. We implement two chance-constrained methods (ALSO-X and CVaR) and a P90 sensitivity analysis.


### Table of Contents
1. [Project Description](#project-description)
2. [Folder Structure](#folder-structure)
3. [Usage](#usage)
4. [Analysis Tools](#analysis-tools)

### Project Description
In the second task, it implements a flexible load in a minute-level consumption between 220kW and 600kW, considering:
* The scenarios:
    -100 in-sample profiles for determining the bid 
    -200 out-of-sample profiles
* P90 Requirement that needs to be less or equal than 10% of the minutes that can have a shortfall 
* Two methods were used:
  -ALSO-X (model_ancilliary.py): MILP + LP relaxation and bisection for in-sample P90.
  -CVaR (model_ancilliary_cvar.py): LP controlling expected shortfall for P90.
*Sensitivity (sensitivity_2_3.py): varying ϵ from 0.00 (P100) to 0.20 (P80), quantifying the trade-off between offered capacity and expected shortfall.


The models are implemented using Gurobi optimization solver and Python.

### Folder Structure
```
second_task/
├── input_data.py                 # Load/generate in- and out-of-sample profiles & probabilities
├── model_ancilliary.py           # Gurobi ALSO-X (per-hour) implementation
├── model_ancilliary_cvar.py      # Gurobi CVaR approximation implementation
├── sensitivity_2_3.py            # Task 2.3 P90 sensitivity analysis script
├── main.py                       # CLI: run_hourly, run_relaxed, CVaR & verification
└── p90_model.lp                  # Last MILP dump (for debugging)
```

### Usage
For Tasks 2.1 ( ALSO-X solve CVaR ) solvers and Taskt 2.2 ( P90 verification ) run the main script:
```
python -m second_task.main
```
For Tasks 2.3 run the script:
```
python -m second_task.sensitivity_2_3
```

### Analysis Tools
#### P90 Verification
-verify_p90_out_of_sample() in both models
-Checks fraction of minutes bid ≥ actual consumption, ensures ≥ P90
  
#### P90 Sensitivity
-Varies ε (0.00→0.20)
-Plots in-sample bid vs. out-of-sample expected shortfall














