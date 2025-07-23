import pandas as pd

# Read the raw data (ensure it's correctly formatted in the CSV)
df = pd.read_csv('Models.csv', header=None)

# Flatten the data into three columns: Year, Make, Model
data = []
for i in range(0, len(df), 3):
    year = df.iloc[i].values[0]
    make = df.iloc[i+1].values[0]
    model = df.iloc[i+2].values[0]
    data.append([year, make, model])

# Create a new DataFrame
new_df = pd.DataFrame(data, columns=["Year", "Make", "Model"])

# Save the cleaned DataFrame
new_df.to_csv('Cleaned_Models.csv', index=False)
