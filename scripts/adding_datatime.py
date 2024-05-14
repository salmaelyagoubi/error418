import pandas as pd
from datetime import datetime

# Assuming you can load your data as `data`
data = pd.read_csv(r'C:\Users\salma elyagoubi\error418\data\water_potability.csv')

# Adding a timestamp column with the current time for all rows
data['Timestamp'] = pd.to_datetime('now')

# If you need sequential timestamps (e.g., hourly intervals), you could do:
data['Timestamp'] = pd.date_range(start='2023-01-01', periods=len(data), freq='H')

# Save the updated dataset if needed
data.to_csv(r'C:\Users\salma elyagoubi\error418\data\modified_water_potability.csv', index=False)
