import os
import pandas as pd

df = pd.read_csv('C:/Users/salma elyagoubi/error418/data/water_potability_with_errors.csv') 

output_folder = 'raw_data'
os.makedirs(output_folder, exist_ok=True)

rows_per_file = 10

for i in range(0, len(df), rows_per_file):
    df_subset = df.iloc[i:i + rows_per_file]
    subset_filename = f'water_data_{i // rows_per_file + 1}.csv'
    df_subset.to_csv(os.path.join(output_folder, subset_filename), index=False)

print(f'Dataset split into {len(df) // rows_per_file} files and saved in {output_folder}.')
