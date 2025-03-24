# RENEWABLES IN ELECTRICITY MARKETS: ASSIGMENT 1

## Introduction
This project is related to the subject Renewables in Electricity Markets Assigment 1 in 2025 spring semester at DTU. It was built to analyse the different models from most basic to more complex scenarios for electricity markets. It covers copper plate models, battery implementation time-dependant copper plate, comparisson of zonal and nodal approaches as well as regulation and reserve markets. 

The data was obtained from the paper: IEEE 24-bus reliability test system. [View the paper here](chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://backend.orbit.dtu.dk/ws/portalfiles/portal/120568114/An_Updated_Version_of_the_IEEE_RTS_24Bus_System_for_Electricty_Market_an....pdf).

# Project Directory Structureç
```
optimizationMPS_project-main/ 
├── data/ 
│ ├── bid_offers.csv # Bid offers for generators 
│ ├── bus_capacity.csv # Bus capacity data 
│ ├── bus_reactance.csv # Bus reactance data 
│ ├── demand_per_load.csv # Demand per load data 
│ ├── GeneratorData.csv # Data for generators 
│ ├── p_ini.csv # Initial power data 
│ ├── system_demand.csv # System-wide demand data 
│ └── wind_capacity_factors.csv # Wind capacity factors 
├── step1/ 
│ ├── init.py # Initialization script for the module 
│ ├── input_data.py # Loads and prepares input data 
│ ├── main.py # Main execution script 
│ ├── model.py # Defines the optimization model 
│ └── plotting.py # Contains functions for plotting results 
├── step2/ 
│ ├── init.py 
│ ├── input_data.py 
│ ├── main.py 
│ ├── model.py 
│ ├── plotting.py 
│ └── sensitivity.py # Sensitivity analysis scripts 
├── step3_nodal/ 
│ ├── init.py 
│ ├── input_data.py 
│ ├── main.py 
│ ├── model.py 
│ └── sensitivity.py 
├── step3_zonal/ 
│ ├── init.py 
│ ├── input_data.py 
│ ├── main.py 
│ ├── model.py 
│ └── sensitivity.py 
├── step5/ 
│ ├── init.py 
│ ├── day_ahead_model.py # Model for day-ahead market simulation 
│ ├── input_data_day_ahead.py # Day-ahead market data preparation 
│ ├── input_data_regulation.py # Regulatory data preparation 
│ ├── main.py 
│ ├── plotting.py 
│ └── regulation_model.py # Regulation market model 
├── step6/ 
│ ├── init.py 
│ ├── day_ahead_model.py 
│ ├── input_data.py 
│ ├── main.py 
│ ├── plotting.py 
│ └── reserve_model.py # Reserve market model 
└── README.md # Documentation for the project 
└── requirements.txt # Required Python libraries
```
**Install required Python libraries:**
```
pip install -r requirements.txt
``` 
The data used for the project is in data folder. 
In each step folder:
 - main.py is the main file used to run a model for each step.
 - Constrains are defined in the model.py file.
 - Input_data uses the data from data folder and also uses additional data required for the step. 
 - If there is a plotting.py file, the plotting functions for the step are defined there.

## Step 1
In this step we do the analysis of the market for one hour. We determined the market-clearing-price, social welfere, profit for each producer and utility of each demand.

**How to run:**
```
cd step1/
python main.py
```

## Step 2
In this step we do the same analysis as in step 1 but for multiple hours. We also added a battery tp the system to see how it can help balance it. 
**How to run:**
```
cd step2/
python main.py
```
**How to run sensitivity:**
```
cd step2/
python sensitivity.py
```
Step 3 is focusing on the comparison between nodal and zonal frameworks.
## Step 3 Nodal
In this step network constrains are introduced to find nodal market-clearing prices.
**How to run:**
```
cd step3_nodal/
python main.py
```
**How to run sensitivity:**
```
cd step3_nodal/
python sensitivity.py
```
## Step 3 Zonal
In this step network constrains are introduced to find zonal prices. The number of zones and the nodes that are in each zones can be changed in input_data.py.
**How to run main:**
```
cd step3_zonal/
python main.py
```
**How to run sensitivity:**
```
cd step3_zonal/
python sensitivity.py
```
## Step 5
In this step we are focusing on analysis how balancing market works. We compare one and two-prices scheme.
**How to run:**
```
cd step5/
python main.py
```
**Choose one or two price scheme**

Change variable self.regulation_pricing on line 35 of the file input_data_day_ahead.py.


## Step 6
In step 6 we focus on reserve market.
**How to run:**
```
cd step6/
python main.py
```

## Contributors
Kacper Rokosz, Diego Moran, Adam Zielinski, Carlos Fernández de Heredia