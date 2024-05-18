import pandas as pd
import os
from math import ceil

def split_dataset(dataset_path, raw_data_folder, num_files):
    if not os.path.exists(raw_data_folder):
        os.makedirs(raw_data_folder)

    df = pd.read_csv(r"C:\Users\salma elyagoubi\error418\data\water_potability_with_errors.csv")
    
    total_rows = len(df)
    rows_per_file = ceil(total_rows / num_files)
    
    for i in range(num_files):
        start_row = i * rows_per_file
        end_row = min(start_row + rows_per_file, total_rows)
        subset_df = df.iloc[start_row:end_row]
        subset_df.to_csv(os.path.join(raw_data_folder, f'data_part_{i+1}.csv'), index=False)
        print(f'Saved {len(subset_df)} rows to {os.path.join(raw_data_folder, f"data_part_{i+1}.csv")}')

split_dataset(r"C:\Users\salma elyagoubi\error418\data\water_potability_with_errors.csv", 'C:/Users/salma elyagoubi/error418/docker/airflow/dags/raw-data', 10)
