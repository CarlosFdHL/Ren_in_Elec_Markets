import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
num_profiles = 300
in_sample_count = 100
profile_length = 1440
min_kw = 220
max_kw = 600
max_change = 35

# Profile generation function
def generate_profile():
    profile = np.zeros(profile_length)
    profile[0] = np.random.uniform(min_kw, max_kw)
    for i in range(1, profile_length):
        lower = max(min_kw, profile[i - 1] - max_change)
        upper = min(max_kw, profile[i - 1] + max_change)
        profile[i] = np.random.uniform(lower, upper)
    return profile

# Generate profiles
np.random.seed(2)
all_profiles = np.array([generate_profile() for _ in range(num_profiles)])
in_sample_indices = np.random.choice(num_profiles, in_sample_count, replace=False)
in_sample_profiles = all_profiles[in_sample_indices]
out_sample_profiles = np.delete(all_profiles, in_sample_indices, axis=0)

# Save profiles to CSV
df_in_sample = pd.DataFrame(in_sample_profiles)
df_in_sample.to_csv("data/consumption_profiles/in_sample_profiles2.csv", index=False)

df_out_sample = pd.DataFrame(out_sample_profiles)
df_out_sample.to_csv("data/consumption_profiles/out_sample_profiles2.csv", index=False)

# Generate heatmap data function
def create_heatmap_data(profiles, resolution_kw=10):
    bins = np.arange(min_kw, max_kw + resolution_kw, resolution_kw)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    heatmap = np.zeros((len(bin_centers), profile_length))
    for t in range(profile_length):
        hist, _ = np.histogram(profiles[:, t], bins=bins)
        heatmap[:, t] = hist / profiles.shape[0]
    return heatmap, bin_centers

# Generate heatmap data
heatmap_all, bin_centers = create_heatmap_data(all_profiles)
heatmap_in_sample, _ = create_heatmap_data(in_sample_profiles)

# X axis labels
time_labels = np.linspace(0, 24, 9)
time_ticks = (time_labels * 60).astype(int)

# Graph function
def plot_heatmap(heatmap, bin_centers, title):
    plt.figure(figsize=(12, 6))
    extent = [0, profile_length, bin_centers[0], bin_centers[-1]]
    plt.imshow(1 - heatmap, aspect='auto', cmap='inferno', extent=extent, origin='lower')
    mean_profile = np.sum(heatmap * bin_centers[:, np.newaxis], axis=0)
    plt.plot(np.arange(profile_length), mean_profile, color='lime', label='Mean')
    plt.colorbar(label='Probability')
    plt.xticks(time_ticks, [f"{int(h):02d}:00" for h in time_labels])
    plt.xlim(0, 10)
    plt.xlabel('Time of day')
    plt.ylabel('Power [kW]')
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Show plots
# plot_heatmap(heatmap_all, bin_centers, "All scenarios")
# plot_heatmap(heatmap_in_sample, bin_centers, "In-sample scenarios")
