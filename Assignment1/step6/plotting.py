import matplotlib.pyplot as plt
import numpy as np
import reserve_model as rm

# Plotting parameters: 
plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.size'] = 14

def plotting_results(model):
# Plotting the results of the optimization problem
    t, price = zip(*model.results.price.items())
    plt.step(t, price)
    plt.xlabel("Hour")
    plt.ylabel("Price $/MWh")
    plt.title("Market clearing price for each hour")

    plt.show()

def plot_reserve_allocation(rm):
    # Plotting the reserve allocation over time
    time = rm.data.timeSpan
    generators = rm.data.generators
    
    reserve_up_total = []
    reserve_down_total = []
    for t in time:
        up = sum(rm.results.reserve_up[g, t] for g in generators)
        down = sum(rm.results.reserve_down[g, t] for g in generators)
        reserve_up_total.append(up)
        reserve_down_total.append(down)
    
    plt.figure(figsize=(10, 6))
    plt.plot(time, reserve_up_total, label='Upward Reserve', marker='o', color='blue')
    plt.plot(time, reserve_down_total, label='Downward Reserve', marker='o', color='green')
    plt.xlabel("Hour")
    plt.ylabel("Reserve (MW)")
    plt.title("Upward and Downward Reserve Allocation Over Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plotting the reserve prices over time
    reserve_up_prices = [rm.results.reserve_up_cost[t] for t in time]
    reserve_down_prices = [rm.results.reserve_down_cost[t] for t in time]

    plt.figure(figsize=(10, 6))
    plt.plot(time, reserve_up_prices, label='Upward Reserve Price ($/MW)', marker='s', color='darkblue')
    plt.plot(time, reserve_down_prices, label='Downward Reserve Price ($/MW)', marker='s', color='darkgreen')
    plt.xlabel("Hour")
    plt.ylabel("Price ($/MW)")
    plt.title("Reserve Market Prices Over Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_generation_and_bid(input_data, hour=0):

    # Demand Bid Curve (Descending)
    system_demand = input_data.demand[hour]
    bid_dict = input_data.demand_bid_price[hour]
    
    # Retrieve demand segments keys in their original order then reverse them
    keys = list(input_data.demand_per_load.keys())
    keys_desc = keys[::-1]
    
    # Load segments (in descending order)
    load_values_desc = [input_data.demand_per_load[k] for k in keys_desc]
    cumulative_percent = np.cumsum(load_values_desc)
    total_percent = cumulative_percent[-1]
    # Scale to system demand (MW)
    cumulative_load_mw_bid = (cumulative_percent / total_percent) * system_demand
    # Corresponding bid prices (descending order)
    bid_prices_desc = [bid_dict[k] for k in keys_desc]

    # Generation Supply Curve (Ascending)
    num_hours = len(input_data.timeSpan)
    num_days = num_hours // 24  # used for wind generation indexing
    
    # Sort generator keys by their bid offers (lowest first)
    sorted_keys = sorted(input_data.bid_offers, key=lambda k: input_data.bid_offers[k])
    
    generation_values = []
    generation_prices = []
    for key in sorted_keys:
        if not input_data.wind[key]:
            gen_val = input_data.Pmax[key]
        else:
            # For wind generators, select the appropriate hour value
            gen_val = input_data.Pmax[key][hour - 24 * num_days]
        generation_values.append(gen_val)
        generation_prices.append(input_data.bid_offers[key])
    
    cumulative_generation = np.cumsum(generation_values)
    
    # Determine equilibrium: first index where cumulative generation meets/exceeds system demand
    equilibrium_index = np.where(cumulative_generation >= system_demand)[0][0]
    equilibrium_gen = cumulative_generation[equilibrium_index]
    equilibrium_price = generation_prices[equilibrium_index]
    
    # Plotting both curves on one figure
    plt.figure(figsize=(10, 6))
    
    # Plot Generation Supply Curve (step plot)
    plt.step(cumulative_generation, generation_prices, where='post', label='Generation Supply Curve', color='blue')
    
    # Plot Demand Bid Curve (line with markers)
    cumulative_load_mw_bid = np.append(cumulative_load_mw_bid, cumulative_load_mw_bid[-1])
    bid_prices_desc = np.append(bid_prices_desc, 0)
    cumulative_load_mw_bid = cumulative_load_mw_bid[1:]
    bid_prices_desc = bid_prices_desc[1:]
    plt.step(cumulative_load_mw_bid, bid_prices_desc, label='Demand Bid Curve', color='orange')
    
    # Mark the equilibrium point (from the generation side)
    #plt.plot(equilibrium_gen, equilibrium_price, 'ro', markersize=1, label='Equilibrium Point') 'commented out to show better final price'
    
    plt.xlabel('Cumulative Generation / Demand (MW)')
    plt.ylabel('Price')
    plt.title(f'Generation Supply & Demand Bid Curves at Hour {hour+1}')
    plt.legend()
    plt.grid(True)
    plt.show()