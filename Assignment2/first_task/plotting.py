import matplotlib.pyplot as plt

# Plotting parameters: 
plt.rcParams['font.family'] = 'serif' 
plt.rcParams['font.size'] = 14

def plot_comparison_bids(one_price_model, two_price_model):
    """Plot the comparison of the bids of the two models.
    Args:
        one_price_model: The one price model instance.
        two_price_model: The two price model instance.
    """
    # Define figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define arrays to be plotted
    p_one_price = [one_price_model.results.production[t] for t in one_price_model.data.T]
    p_two_price = [two_price_model.results.production[t] for t in two_price_model.data.T]
    real_prod_one_price = [one_price_model.results.expected_real_prod[t].getValue() for t in one_price_model.data.T]
    real_prod_two_price = [two_price_model.results.expected_real_prod[t].getValue() for t in two_price_model.data.T] 

    # Plot configuration
    ax.plot(one_price_model.data.T, p_one_price, label='One Price Scheme', color='blue', marker = 'x', linestyle = '--')
    ax.plot(one_price_model.data.T, p_two_price, label='Two Price Scheme', color='orange', marker = 'o', linestyle='-.')
    ax.plot(real_prod_one_price, label='Real Production', color='black', linestyle = '-')
    ax.grid()
    ax.legend()
    ax.set_xlabel('Time (h)')
    ax.set_ylabel('Production (MW)')
    plt.tight_layout()