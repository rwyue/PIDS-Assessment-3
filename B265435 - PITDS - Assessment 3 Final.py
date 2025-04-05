#!/usr/bin/env python
# coding: utf-8

# ## B265435 - PITDS - Assessment 3 - Python code

# ### Part 1: Can clustering algorithm be used to see if weather stations can be clustered into groups with “similar” weather?

# In[1]:


import os
import requests
import pandas as pd
import re
import time
from pathlib import Path

# Define base URL and output directory
BASE_URL = "http://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/"
INPUT_FILE = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\station.txt"
OUTPUT_DIR = os.path.join(os.path.dirname(INPUT_FILE))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Part1_weather_stations.xlsx")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Function to handle file permission errors
def safe_excel_writer(output_file, max_retries=5, wait_time=5):
    for attempt in range(max_retries):
        try:
            return pd.ExcelWriter(output_file, engine='xlsxwriter')
        except PermissionError:
            print(f"Permission denied: {output_file}. Ensure the file is closed. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    raise PermissionError(f"Could not access {output_file} after {max_retries} retries.")

# Function to extract latitude and longitude from the 2nd or 3rd line
def extract_lat_lon(lines):
    """Searches for latitude and longitude in the 2nd or 3rd line of the station file."""
    lat, lon = "Unknown", "Unknown"
    for i in range(1, min(3, len(lines))):  # Check 2nd and 3rd lines
        lat_match = re.search(r'Lat\s*[:\s]*([-+]?[\d.]+)', lines[i], re.IGNORECASE)
        lon_match = re.search(r'Lon\s*[:\s]*([-+]?[\d.]+)', lines[i], re.IGNORECASE)
        if lat_match:
            lat = lat_match.group(1)
        if lon_match:
            lon = lon_match.group(1)
    return lat, lon

# Read station names from the provided text file
with open(INPUT_FILE, "r") as file:
    stations = [line.strip() for line in file.readlines() if line.strip()]

# Create a Pandas Excel writer safely
with safe_excel_writer(OUTPUT_FILE) as writer:
    all_weather_stations = []
    for station in stations:
        url = f"{BASE_URL}{station}data.txt"
        response = requests.get(url)
        if response.status_code == 200:
            lines = response.text.split("\n")
            # Extract latitude and longitude
            latitude, longitude = extract_lat_lon(lines)
            # Locate the header line
            for i, line in enumerate(lines):
                if "yyyy" in line.lower():
                    header_index = i
                    break
            else:
                print(f"Skipping {station}: Header not found.")
                continue
            # Extract header and data
            columns = re.split(r'\s+', lines[header_index].strip())
            data = [re.split(r'\s+', line.strip()) for line in lines[header_index+1:] if line.strip()]
            # Ensure all rows have the same number of columns as the header
            data = [row for row in data if len(row) == len(columns)]
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=columns)
            # Append station name, latitude, and longitude columns
            df["Station"] = station
            df["Latitude"] = latitude
            df["Longitude"] = longitude
            # Append to the list for the combined dataframe
            all_weather_stations.append(df)
            # Save to Excel worksheet
            df.to_excel(writer, sheet_name=station[:31], index=False)
            print(f"Saved {station} data.")
        else:
            print(f"Failed to download {station} data.")
# Combine all dataframes into one
all_weather_stations = pd.concat(all_weather_stations, ignore_index=True)
print("Combined all data into a single dataframe: all_weather_stations")
print(f"Data saved to {OUTPUT_FILE}.")


# In[2]:


# Initial check data
all_weather_stations


# In[3]:


# Check any station that stopped recording Sun data since 1971:
df = all_weather_stations

# Convert 'yyyy' column to integer (in case it's stored as string)
df['yyyy'] = pd.to_numeric(df['yyyy'], errors='coerce')

# Filter data from 1971 onward
df_post_1971 = df[df['yyyy'] >= 1971]

# Identify stations where all 'sun' values are missing or invalid since 1971
invalid_sun_stations = df_post_1971.groupby('Station')['sun'].apply(lambda x: all((x.isna()) | (x == '---')))

# Extract station names where the condition is True
stations_stopped_sun = invalid_sun_stations[invalid_sun_stations].index.tolist()

# Display the results
print("Stations that stopped recording Sun data since 1971:")
print(stations_stopped_sun)


# In[4]:


# Check any station with no sun data recored in 2023
df = all_weather_stations

# Filter data for the year 2023
df_2023 = df[df['yyyy'] == 2023]

# Identify stations where all 'sun' values in 2023 are missing or invalid
stations_missing_sun_2023 = df_2023.groupby('Station')['sun'].apply(lambda x: all((x.isna()) | (x == '---')))

# Extract station names where sun data is entirely missing in 2023
stations_no_sun_2023 = stations_missing_sun_2023[stations_missing_sun_2023].index.tolist()

# Display the results
print("Stations with no sun data recorded in 2023:")
print(stations_no_sun_2023)


# In[5]:


# Save data as csv file as a consolidated data
# Specify the directory and file path
directory = r'C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3'
file_path = os.path.join(directory, 'Part1_consolidated_weather_stations.csv')

# Create the directory if it doesn't exist
os.makedirs(directory, exist_ok=True)

# Save the DataFrame to a CSV file
all_weather_stations.to_csv(file_path, index=False)

print(f"CSV file saved at: {file_path}")


# In[6]:


consolidated_df = pd.DataFrame(all_weather_stations)
consolidated_df


# In[7]:


# Function to clean symbols
def clean_symbols(value):
    if isinstance(value, str):  # Only clean string values
        return value.strip('#*$')  # Remove unwanted characters
    return value  # Return unchanged if not a string

# Apply cleaning function to all elements in the DataFrame
df_cleaned = consolidated_df.applymap(clean_symbols)

# Apply cleaning function to all columns *except* "Station"
df_cleaned = df.copy()
df_cleaned.loc[:, df.columns != 'Station'] = df.loc[:, df.columns != 'Station'].applymap(clean_symbols)

# Display cleaned DataFrame
print(df_cleaned)


# In[8]:


# Check out data types for each column 
df = df_cleaned
print(df.dtypes)


# In[9]:


# Convert 'yyyy', 'mm', 'tmax', and 'tmin' columns to numeric, forcing errors to NaN
df[['yyyy', 'mm', 'tmax', 'tmin', 'af', 'rain', 'sun', 'Latitude']] = df[['yyyy', 'mm', 'tmax', 'tmin', 'af', 'rain', 'sun', 'Latitude']].apply(pd.to_numeric, errors='coerce')

# Verify the data types
print(df.dtypes)


# In[10]:


reformat_df = df

# Calculate the 'tavg' column as (tmax - tmin / 2)
reformat_df['tavg'] = (reformat_df['tmax'] - reformat_df['tmin']) / 2

# Insert 'tavg' between 'tmin' and 'af'
cols = ['yyyy', 'mm', 'tmax', 'tmin', 'tavg', 'af', 'rain', 'sun', 'Station', 'Latitude']
reformat_df = reformat_df[cols]

# Display updated DataFrame
print(reformat_df)


# In[11]:


reformat_df = pd.DataFrame(reformat_df)

# Define the file path
file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part1_reformat_weather_stations.csv"

# Save DataFrame to CSV
reformat_df.to_csv(file_path, index=False)  # Set index=False to avoid saving the index column

print(f"DataFrame saved as '{file_path}'")


# In[12]:


# Calculate the average for the specified columns excluding NaN values
columns_to_average_6 = ['tmax', 'tmin', 'tavg', 'af', 'rain', 'sun']
# Group by 'station' and calculate the mean for each station while excluding NaN
averages_by_station_6 = reformat_df.groupby('Station')[columns_to_average_6].mean()

# Display the averages by station
print(averages_by_station_6)


# In[13]:


# Calculate the correlation matrix
correlation_matrix_6 = averages_by_station_6.corr()

# Display the correlation matrix
print("Correlation Matrix:")
print(correlation_matrix_6)

# (Optional) Visualizing the correlation matrix using a heatmap
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(8,6))
sns.heatmap(correlation_matrix_6, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title("Correlation Matrix of 6 Weather Features")
plt.show()


# In[14]:


# Calculate the average for the specified columns excluding NaN values
columns_to_average = ['tavg', 'af', 'rain', 'sun']
# Group by 'station' and calculate the mean for each station while excluding NaN
averages_by_station = reformat_df.groupby('Station')[columns_to_average].mean()

# Display the averages by station
print(averages_by_station.head())


# In[15]:


# Calculate the correlation matrix
correlation_matrix = averages_by_station.corr()

# Display the correlation matrix
print("Correlation Matrix:")
print(correlation_matrix)

# (Optional) Visualizing the correlation matrix using a heatmap
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(8,6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title("Correlation Matrix of Weather Features")
plt.show()


# In[16]:


# Reset index to include 'Station' as a column
averages_by_station = averages_by_station.reset_index()
# Save to CSV
averages_by_station.to_csv('averages_by_station.csv', index=False)
# Define the file path
file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part1_averages_by_station.csv"
# Save DataFrame to CSV
averages_by_station.to_csv(file_path, index=False)  # Set index=False to avoid saving the index column
print(f"DataFrame saved as '{file_path}'")


# In[17]:


import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import RobustScaler

# Selecting only numerical weather data for clustering
columns_to_cluster = ['tavg', 'af', 'rain','sun']
weather_data = averages_by_station[columns_to_cluster]

# Standardizing the data for better clustering performance
# scaler = StandardScaler()
# scaled_data = scaler.fit_transform(weather_data)

#Alternative: If data has many outliers, use RobustScaler instead.
scaler = RobustScaler()
scaled_data = scaler.fit_transform(weather_data)

# Finding the optimal number of clusters using the Elbow method
inertia = []
K_range = range(1, 10)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(scaled_data)
    inertia.append(kmeans.inertia_)

# Plot the Elbow Method Graph
plt.figure(figsize=(8, 5))
plt.plot(K_range, inertia, marker='o', linestyle='--')
plt.xlabel('Number of Clusters (K)')
plt.ylabel('Inertia (Sum of Squared Distances)')
plt.title('Elbow Method for Optimal K')
plt.show()


# In[18]:


from sklearn.metrics import silhouette_score
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# Define the range of clusters
K_range = range(2, 10)  # Start from 2 since silhouette score is undefined for k=1

# Store silhouette scores
silhouette_scores = []

# Loop through different values of k
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled_data)  # Get cluster labels
    
    score = silhouette_score(scaled_data, labels)  # Compute silhouette score
    silhouette_scores.append(score)
    print(f'For K={k}, Silhouette Score={score:.3f}')  # Print score for each k

# Plot the silhouette scores
plt.figure(figsize=(8, 5))
plt.plot(K_range, silhouette_scores, marker='o', linestyle='--')
plt.xlabel('Number of Clusters (K)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score for Optimal K')
plt.show()


# In[19]:


# Choose an optimal number of clusters based on the elbow point (e.g., k=4)
optimal_k = 4
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
averages_by_station['cluster'] = kmeans.fit_predict(scaled_data)
averages_by_station


# In[81]:


averages_by_station = averages_by_station.reset_index()
# Display the clustered stations
print(averages_by_station[['Station', 'cluster']])
# Visualize the clusters using a pairplot (2D representation)
sns.pairplot(averages_by_station, hue='cluster', vars=columns_to_cluster, palette='tab10')
plt.show()


# In[20]:


# Count number of weather stations in each cluster
cluster_counts = averages_by_station['cluster'].value_counts().sort_index()

# Display the result
print("Number of weather stations in each cluster:")
print(cluster_counts)


# In[21]:


# Define columns to compute averages
columns_to_average = ['tavg', 'af', 'rain', 'sun']
# Group by 'cluster' and calculate mean for each attribute
cluster_averages = averages_by_station.groupby('cluster')[columns_to_average].mean()
# Display the result
print(cluster_averages)


# ### Part 2: Can you predict if weather stations fall in the Northern Third of the UK, Central Third of the UK or Southern Third of the UK by using only the weather data?

# In[87]:


df_part2 = averages_by_station
# Assuming df is your DataFrame
df_part2 = df_part2.drop(columns=['index','cluster'])

# Display the updated DataFrame
print(df_part2.head())  # Show the first few rows


# In[88]:


# 1. Merge the two datasets on the 'Station' column to append the Latitude data
averages_by_station_part2 = pd.merge(df_part2, df_cleaned[['Station', 'Latitude']], on='Station', how='inner')

# 2. Remove duplicate rows (if any)
averages_by_station_part2 = averages_by_station_part2.drop_duplicates()

df_part2 = averages_by_station_part2
# 3. Check the resulting dataframe to ensure the Latitude column is added
print(df_part2.head())


# In[89]:


import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# 1. Exclude the last 5 stations alphabetically
averages_by_station_part2 = averages_by_station_part2.sort_values('Station', ascending=True)
train_data = averages_by_station_part2.iloc[:-5]  # Exclude the last 5 stations
test_data = averages_by_station_part2.iloc[-5:]   # Last 5 stations as test set

# 2. Create a new column 'region' based on latitude
def assign_region(latitude):
    if latitude >= 57.233:  # Northern Third of the UK (>= 57.233)
        return 'Northern'
    elif latitude >= 53.567:  # Central Third of the UK (>= 53.567)
        return 'Central'
    else:  # Southern Third of the UK (< 53.567)
        return 'Southern'

# Apply the function to assign regions based on latitude
train_data['region'] = train_data['Latitude'].apply(assign_region)
test_data['region'] = test_data['Latitude'].apply(assign_region)

# 3. Define features and target
# features = ['tmax', 'tmin', 'tavg', 'af', 'rain', 'sun']
features = ['tavg', 'af', 'rain', 'sun']
X_train = train_data[features]
y_train = train_data['region']
X_test = test_data[features]
y_test = test_data['region']

# 4. Train a classifier
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate the model
y_pred = model.predict(X_test)

# Display the classification report
print(classification_report(y_test, y_pred))

# You can also check accuracy directly
accuracy = (y_pred == y_test).mean()
print(f"Accuracy: {accuracy:.2f}")


# In[93]:


train_data.head()


# In[91]:


test_data


# In[94]:


print(y_pred)


# ### Part 3: Does the weather affect how happy we are?

# In[95]:


import pandas as pd
# Load the spreadsheet
file_path = "C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Wellbeing data 2014_15.xlsx"
xls = pd.ExcelFile(file_path)

# Display sheet names to identify the relevant one
xls.sheet_names

# Load the "Happiness" sheet
df_happiness = pd.read_excel(xls, sheet_name="Happiness")

# Display the first few rows to understand its structure
df_happiness.head(10)


# In[96]:


import pandas as pd
from io import StringIO

# Define file path
file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Wellbeing data 2014_15.xlsx"

# Load the Excel file
xls = pd.ExcelFile(file_path)

# Define relevant sheets and their corresponding column names
sheets = {
    "Happiness": "Happiness Score"
    #,"Life Satisfaction": "Life Satisfaction Score",
    #"Worthwhile": "Worthwhile Score",
    #"Anxiety": "Anxiety Score"
}

# Initialize an empty DataFrame for merging
df_final = None

# Process each sheet and merge the data
for sheet, score_col in sheets.items():
    df = pd.read_excel(xls, sheet_name=sheet, skiprows=5)  # Skip metadata rows
    df = df.rename(columns={
        df.columns[0]: "Area Code",
        df.columns[1]: "Area Name",
        df.columns[8]: score_col  # Assuming column 8 holds the score
    })
    df = df[["Area Code", "Area Name", score_col]].dropna(subset=["Area Name", score_col])
    
    if df_final is None:
        df_final = df  # First dataset
    else:
        df_final = df_final.merge(df, on=["Area Code", "Area Name"], how="inner")

# Load the region data
region_data = """Area Code,Region,Latitude,Longitude
E12000001,NORTH EAST,55.0,-1.9
E12000002,NORTH WEST,54.0,-2.6
E12000003,YORKSHIRE AND THE HUMBER,53.6,-1.2
E12000004,EAST MIDLANDS,53.0,-0.8
E12000005,WEST MIDLANDS,52.5,-2.3
E12000006,EAST,52.2,0.4
E12000007,LONDON,51.5,-0.1
E12000008,SOUTH EAST,51.3,-0.5
E12000009,SOUTH WEST,51.0,-3.2
W92000004,WALES,51.5,-3.2
S92000003,SCOTLAND,56.0,-3.2
N92000002,NORTHERN IRELAND,54.6,-5.9"""

df_region = pd.read_csv(StringIO(region_data))

# Merge with region data
df_final = df_final.merge(df_region, on="Area Code", how="inner").drop(columns=["Region"])

# Define the output file path
output_file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part3_format_Happiness_data_2014_15.csv"

# Save to CSV
df_final.to_csv(output_file_path, index=False)

print(f"DataFrame saved as '{output_file_path}'")


# In[97]:


df_final


# In[98]:


# 1. Merge the two datasets on the 'Station' column to append the Latitude data
averages_by_station_part3 = pd.merge(averages_by_station_part2, df_cleaned[['Station', 'Longitude']], on='Station', how='inner')

# 2. Remove duplicate rows (if any)
averages_by_station_part3 = averages_by_station_part3.drop_duplicates()

averages_by_station_part3

# Define the output file path
output_file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part3_averages_by_station.csv"

# Save to CSV
averages_by_station_part3.to_csv(output_file_path, index=False)

print(f"DataFrame saved as '{output_file_path}'")


# In[99]:


averages_by_station_part3.head()


# In[101]:


# Merge the Region text data with weather data
from scipy.spatial import cKDTree

# Load the weather station data
weather_data_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part3_averages_by_station.csv"
weather_df = pd.read_csv(weather_data_path)

# Ensure weather data has necessary columns
if "Latitude" not in weather_df.columns or "Longitude" not in weather_df.columns:
    raise ValueError("Weather data must contain 'Latitude' and 'Longitude' columns.")

# Convert latitude and longitude to NumPy arrays for efficient lookup
region_coords = df_final[["Latitude", "Longitude"]].to_numpy()
weather_coords = weather_df[["Latitude", "Longitude"]].to_numpy()

# Build KDTree for nearest neighbor search
tree = cKDTree(weather_coords)

# Find nearest weather station for each region
_, indices = tree.query(region_coords)

df_final["Nearest Station"] = weather_df.iloc[indices].reset_index(drop=True)["Station"]
df_final["tavg"] = weather_df.iloc[indices].reset_index(drop=True)["tavg"]
df_final["af"] = weather_df.iloc[indices].reset_index(drop=True)["af"]
df_final["rain"] = weather_df.iloc[indices].reset_index(drop=True)["rain"]
df_final["sun"] = weather_df.iloc[indices].reset_index(drop=True)["sun"]

# Define the output file path
output_file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part3_joined_dataset.csv"

# Save to CSV
df_final.to_csv(output_file_path, index=False)

print(f"DataFrame saved as '{output_file_path}'")


# In[102]:


# Load the joined dataset we just saved
file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part3_joined_dataset.csv"
df_joined = pd.read_csv(file_path)

# Display basic information and the first few rows
df_joined.head()


# In[103]:


import scipy
import statsmodels
import statsmodels.api as sm
# Define independent variables (weather-related features)
X = df_joined[['tavg', 'af', 'rain', 'sun']]

# Define dependent variable (happiness score)
y = df_joined['Happiness Score']

# Add a constant to the model (for intercept)
X = sm.add_constant(X)

# Perform Ordinary Least Squares (OLS) regression
model = sm.OLS(y, X).fit()

# Display regression results
model.summary()


# In[104]:


import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

# Step 1: Check correlation between variables
correlation_matrix = df_joined[['Happiness Score', 'tavg', 'af', 'rain', 'sun']].corr()

# Plot correlation heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Correlation Matrix of Variables")
plt.show()


# ### Part 4: Perform clustering on the well-being data.

# In[23]:


import pandas as pd
from io import StringIO

# Define file path
file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Wellbeing data 2014_15.xlsx"

# Load the Excel file
xls = pd.ExcelFile(file_path)

# Define relevant sheets and their corresponding column names
sheets = {
    "Happiness": "Happiness Score",
    "Life Satisfaction": "Life Satisfaction Score",
    "Worthwhile": "Worthwhile Score",
    "Anxiety": "Anxiety Score"
}

# Initialize an empty DataFrame for merging
df_final = None

# Process each sheet and merge the data
for sheet, score_col in sheets.items():
    df = pd.read_excel(xls, sheet_name=sheet, skiprows=5)  # Skip metadata rows
    df = df.rename(columns={
        df.columns[0]: "Area Code",
        df.columns[1]: "Area Name",
        df.columns[8]: score_col  # Assuming column 8 holds the score
    })
    df = df[["Area Code", "Area Name", score_col]].dropna(subset=["Area Name", score_col])
    
    if df_final is None:
        df_final = df  # First dataset
    else:
        df_final = df_final.merge(df, on=["Area Code", "Area Name"], how="inner")

# Load the region data
region_data = """Area Code,Region,Latitude,Longitude
E12000001,NORTH EAST,55.0,-1.9
E12000002,NORTH WEST,54.0,-2.6
E12000003,YORKSHIRE AND THE HUMBER,53.6,-1.2
E12000004,EAST MIDLANDS,53.0,-0.8
E12000005,WEST MIDLANDS,52.5,-2.3
E12000006,EAST,52.2,0.4
E12000007,LONDON,51.5,-0.1
E12000008,SOUTH EAST,51.3,-0.5
E12000009,SOUTH WEST,51.0,-3.2
W92000004,WALES,51.5,-3.2
S92000003,SCOTLAND,56.0,-3.2
N92000002,NORTHERN IRELAND,54.6,-5.9"""

df_region = pd.read_csv(StringIO(region_data))

# Merge with region data
df_final = df_final.merge(df_region, on="Area Code", how="inner").drop(columns=["Region"])

# Define the output file path
output_file_path = r"C:\RWY\Edinburgh DSTI (24 - XX)\Practical Introduction to Data Science\Assessment\Assessment 3\Part4_reformat_wellbeing_data_2014_15.csv"

# Save to CSV
df_final.to_csv(output_file_path, index=False)

print(f"DataFrame saved as '{output_file_path}'")


# In[106]:


df_final


# In[31]:


from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Select relevant numerical columns for clustering
features = ['Happiness Score', 'Life Satisfaction Score', 'Worthwhile Score', 'Anxiety Score', 'Latitude', 'Longitude']
X = df_final[features]

# Normalize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Determine the optimal number of clusters using the elbow method
inertia = []
k_range = range(1, 10)
for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertia.append(kmeans.inertia_)

# Plot the elbow curve
plt.figure(figsize=(8, 5))
plt.plot(k_range, inertia, marker='o')
plt.title('Elbow Method for Optimal K')
plt.xlabel('Number of Clusters')
plt.ylabel('Inertia (Sum of Squared Distances)')
plt.grid(True)
plt.tight_layout()
plt.show()


# In[32]:


from sklearn.metrics import silhouette_score
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# Define the range of clusters
K_range = range(2, 10)  # Start from 2 since silhouette score is undefined for k=1

# Store silhouette scores
silhouette_scores = []

# Loop through different values of k
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)  # Get cluster labels
    
    score = silhouette_score(X_scaled, labels)  # Compute silhouette score
    silhouette_scores.append(score)
    print(f'For K={k}, Silhouette Score={score:.3f}')  # Print score for each k

# Plot the silhouette scores
plt.figure(figsize=(8, 5))
plt.plot(K_range, silhouette_scores, marker='o', linestyle='--')
plt.xlabel('Number of Clusters (K)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score for Optimal K')
plt.show()


# In[34]:


from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Step 1: Select the relevant features for clustering
features_for_clustering = ['Happiness Score', 'Life Satisfaction Score', 'Worthwhile Score', 'Anxiety Score', "Latitude", "Longitude"]
X_cluster = df_final[features_for_clustering]

# Step 2: Standardize the features
X_scaled_cluster = scaler.fit_transform(X_cluster)

# Step 3: Apply KMeans clustering
kmeans = KMeans(n_clusters=3, random_state=42)
df_final['Cluster'] = kmeans.fit_predict(X_scaled_cluster)

# Step 4: Use PCA to reduce dimensions for visualization
pca = PCA(n_components=2)
pca_components = pca.fit_transform(X_scaled_cluster)
df_final['PCA1'] = pca_components[:, 0]
df_final['PCA2'] = pca_components[:, 1]

# Step 5: Visualize the clusters
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_final, x='PCA1', y='PCA2', hue='Cluster', palette='Set2', s=100)
plt.title('Clustering of Regions Based on Well-being Scores (K-means, K=3)')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.legend(title='Cluster')
plt.grid(True)
plt.tight_layout()
plt.show()

# Display cluster centers in original feature space
cluster_centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), 
                               columns=features_for_clustering)
cluster_centers


# In[35]:


# Apply KMeans clustering with the chosen number of clusters
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df_final['Cluster'] = kmeans.fit_predict(X_scaled)

# Visualize the clusters using a scatter plot (Latitude vs. Longitude)
plt.figure(figsize=(8, 6))
scatter = plt.scatter(df_final['Longitude'], df_final['Latitude'], c=df_final['Cluster'], cmap='viridis', s=100, edgecolor='k')
plt.title('Clustered Regions Based on Wellbeing & Geography')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.grid(True)
plt.colorbar(scatter, label='Cluster')
plt.tight_layout()
plt.show()

# Show cluster assignments with region names
df_final[['Area Name', 'Cluster']]


# In[ ]:





# In[ ]:




