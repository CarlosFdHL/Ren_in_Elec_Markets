import pandas as pd
import numpy as np

num_scenarios = 10
num_hours = 24

probability = 0.5

# Generate data
data = np.random.binomial(1, probability, (num_scenarios, num_hours))

# Store in csv
# df = pd.DataFrame(data, columns=[f'Hour_{i+1}' for i in range(num_hours)])
# df.to_csv('ps_condition_scenarios.csv', index=False)
