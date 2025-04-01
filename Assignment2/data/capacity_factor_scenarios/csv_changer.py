import pandas as pd
import os
from datetime import timedelta

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# File name (same as yours)
file_name = '75_2025-03-30T0100_2025-03-31T0200.csv'

# Full path to the file
file_path = os.path.join(current_dir, file_name)

try:
    # Read the CSV file
    df = pd.read_csv(file_path, sep=';')
    
    # Rename the power generation column to 'value' for easier handling
    df = df.rename(columns={'Wind power generation - 15 min data': 'value'})
    
    # Convert startTime to datetime format (handling the Zulu time format)
    df['startTime'] = pd.to_datetime(df['startTime'].str.replace('.000Z', ''))
    
    # Set startTime as the index
    df.set_index('startTime', inplace=True)
    
    # Resample to hourly frequency and sum the values
    hourly_df = df.resample('H').sum()
    
    # Reset index to make startTime a column again
    hourly_df.reset_index(inplace=True)
    
    # Format the startTime back to similar format (without milliseconds)
    hourly_df['startTime'] = hourly_df['startTime'].dt.strftime('%Y-%m-%dT%H%M')
    
    # Create endTime by adding 1 hour to startTime
    hourly_df['endTime'] = (pd.to_datetime(hourly_df['startTime']) + timedelta(hours=1)).dt.strftime('%Y-%m-%dT%H%M')
    
    # Select and reorder columns (removed datasetId since it's not in original)
    hourly_df = hourly_df[['startTime', 'endTime', 'value']]
    
    # Create new filename with "_new" addition
    base_name, ext = os.path.splitext(file_name)
    new_file_name = f"{base_name}_new{ext}"
    output_path = os.path.join(current_dir, new_file_name)
    
    # Save to new CSV file
    hourly_df.to_csv(output_path, sep=';', index=False)
    
    print(f"Success! Hourly production data saved to: {output_path}")
    print(f"Original 15-minute intervals aggregated into {len(hourly_df)} hourly records")
    print("\nSample of aggregated data:")
    print(hourly_df.head())

except FileNotFoundError:
    print(f"Error: The file '{file_name}' was not found in: {current_dir}")
    print("Please make sure:")
    print("1. The file exists in the same directory as this script")
    print("2. The file name is spelled exactly as shown above")
except Exception as e:
    print(f"An error occurred: {str(e)}")