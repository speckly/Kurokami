import pandas as pd
import os
import matplotlib.pyplot as plt

DIRECTORY = "../output/2024_03_27"
SUFFIX = "_RTX 3070.csv"

def get_low(DIRECTORY = "../output/2024_03_27", SUFFIX = "_RTX 3070.csv"):
    csv_files = [f"{DIRECTORY}/{file}" for file in os.listdir(DIRECTORY) if file.endswith(SUFFIX)]

    all_data = []
    for file in csv_files:
        df = pd.read_csv(file)
        if 'price' in df.columns:
            all_data.append(df['price'].apply(lambda x: float(eval(x)[0].replace('$', '').replace(',', ''))))
        else:
            print(f"Price column not found while parsing {file}")

    all_data = pd.concat(all_data, ignore_index=True)

    return pd.DataFrame(all_data, columns=['price'])['price'].quantile(0.1)
    # Plot the box and whisker plot of the 'price' column
    # price_df.boxplot(column='price')
    # plt.title('Boxplot of Price')
    # plt.ylabel('Price')
    # plt.show()
x = "../output"
for file in [f for f in os.listdir(x) if os.path.isdir(os.path.join(x, f))]:
    
    print(file)