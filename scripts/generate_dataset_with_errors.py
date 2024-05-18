import pandas as pd
import numpy as np

def introduce_errors_to_df(df):
    # Randomly remove a column
    if len(df.columns) > 1:  # Ensure there is more than one column
        df = df.drop(df.columns[np.random.choice(range(len(df.columns)))], axis=1)

    # Insert wrong values for a given feature
    if 'ph' in df.columns:  # Assuming 'ph' is a numerical feature
        wrong_indices = np.random.choice(df.index,  replace=False)
        df.loc[wrong_indices, 'ph'] = -999  # An impossible negative value for pH

    # Place string values in a numerical column
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    if numerical_cols.size > 0:
        # Convert the first numerical column to object type to allow string insertion
        df[numerical_cols[0]] = df[numerical_cols[0]].astype(object)
        str_indices = np.random.choice(df.index,  replace=False)
        df.loc[str_indices, numerical_cols[0]] = 'INVALID'

    return df

# Read the dataset
file_path = 'C:/Users/salma elyagoubi/error418/data/water_potability_clean_10000.csv'
df = pd.read_csv(file_path)

# Introduce errors to the DataFrame
df_with_errors = introduce_errors_to_df(df)

# Output the manipulated DataFrame to a new CSV file
output_file_path = 'C:/Users/salma elyagoubi/error418/data/water_potability_with_errors.csv'
df_with_errors.to_csv(output_file_path, index=False, na_rep='null')

print(f"File saved with errors introduced: {output_file_path}")