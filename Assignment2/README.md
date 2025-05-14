# RENEWABLES IN ELECTRICITY MARKETS: ASSIGMENT 2

## Introduction

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
For Task 1.4 run also specifying the price scheme
```
python -m first_task.risk_analysis one_price
python -m first_task.risk_analysis two_price
```

### Analysis Tools

#### ExPost Analysis
- Performs cross-validation to evaluate model performance
- Compares in-sample vs out-of-sample profits
- Calculates expected imbalances and profits

#### Risk Analysis
- Incorporates Conditional Value-at-Risk (CVaR)

- Allows risk-averse optimization

- Adjustable risk parameters:

*  alpha: Confidence level (e.g., 0.95)

*  beta: Risk aversion coefficient (0-1)

### Sensitivity Analysis
- Tests model performance with different in-sample sizes

- Evaluates stability of results

- Produces visualizations of sensitivity