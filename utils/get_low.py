import pandas as pd
import os
import matplotlib.pyplot as plt

def get_low(DIRECTORY = "../output/", SUFFIX = "_RTX 3070.csv", GRAPH = False): # Do not use True when in prod
    csv_files = [f"{DIRECTORY}/{folder}/{file}" for folder in os.listdir(DIRECTORY) 
    if os.path.isdir(os.path.join(DIRECTORY, folder)) for file in os.listdir(os.path.join(DIRECTORY, folder)) if file.endswith(SUFFIX)]
    
    all_data = []
    for file in csv_files:
        df = pd.read_csv(file)
        if 'price' in df.columns:
            all_data.append(df['price'].apply(lambda x: float(eval(x)[0].replace('$', '').replace(',', ''))))
        else:
            print(f"Price column not found while parsing {file}")

    all_data = pd.concat(all_data, ignore_index=True)
    price_df = pd.DataFrame(all_data, columns=['price'])
    
    if GRAPH:
        price_df.boxplot(column='price')
        plt.title('Boxplot of Price')
        plt.ylabel('Price')
        plt.show() # Interrupts the return but ok, suffer then, im lazy

    return price_df['price'].quantile(0.1)

    

if __name__ == "__main__":
    DIRECTORY = "../output/"
    SUFFIX = "_RTX 3070.csv"
    print(f"The 10% low for RTX 3070 is {get_low(DIRECTORY=DIRECTORY, SUFFIX=SUFFIX, GRAPH=True)}")