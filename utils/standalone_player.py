
import pandas as pd
import os

csv_path = '/docker/bags/'

csv_file = os.path.join(csv_path, 'df_msgs_info_all.csv')

df = pd.read_csv(csv_file)
df = df.iloc[1: , :]  # remove first row of headers

df = df.reset_index()

for index, row in df.iterrows():
    # print(row['c1'], row['c2'])
    print(row)