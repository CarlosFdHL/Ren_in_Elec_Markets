# RENEWABLES IN ELECTRICITY MARKETS: ASSIGMENT 2

## Introduction

## First Task

This repository contains implementations of optimal bidding strategies for electricity producers in day-ahead and balancing markets under one-price and two-price imbalance settlement schemes.

### Table of Contents
1. [Project Description](#project-description)
2. [Folder Structure](#folder-structure)
3. [Key Features](#key-features)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Models](#models)
7. [Analysis Tools](#analysis-tools)
8. [Data Requirements](#data-requirements)
9. [Results](#results)
10. [License](#license)

### Project Description
This project implements mathematical optimization models for electricity producers to:
- Determine optimal bids for the day-ahead market
- Account for production uncertainty and imbalance costs
- Compare one-price and two-price imbalance settlement schemes
- Perform risk analysis and sensitivity testing

The models are implemented using Gurobi optimization solver and Python.

### Folder Structure
first_task/
├── input_data.py # Data loading and scenario generation
├── model_one_price.py # One-price imbalance scheme model
├── model_two_price.py # Two-price imbalance scheme model
├── expost_analysis.py # Cross-validation and out-of-sample testing
├── risk_analysis.py # Risk-averse optimization with CVaR
├── sensitivity_expost.py # Sensitivity analysis tools
├── plotting.py # Visualization functions
└── main.py # Main execution script


### Key Features
- Scenario-based stochastic optimization
- Cross-validation framework for model evaluation
- Risk management using Conditional Value-at-Risk (CVaR)
- Comparative analysis between pricing schemes
- Visualization of results and sensitivity analysis

### Installation
1. Clone the repository
2. Install required packages:
   ```
    pip install -r requirements.txt
    ```
### Usage
Run the main script with either pricing scheme:
```
python main.py one_price
python main.py two_price
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