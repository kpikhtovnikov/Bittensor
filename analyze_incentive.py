import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from config import OUTPUT_DIRECTORY_MINER

def plot_incentive(df):
    plt.figure(figsize=(12,6))
    for uid, group in df.groupby('uid'):
        plt.plot(group['timestamp'], group['incentive'], marker='o', label=f'UID {uid}')
    plt.xlabel('Время')
    plt.ylabel('Incentive')
    plt.title('Изменение Incentive во времени')
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gcf().autofmt_xdate()
    plt.show()

def analyze_intervals(df):
    df_sorted = df.sort_values(['uid', 'timestamp']).copy()
    df_sorted['time_diff'] = df_sorted.groupby('uid')['timestamp'].diff().dt.total_seconds()
    
    print(df_sorted[['uid', 'timestamp', 'incentive', 'time_diff']])
    
    plt.figure(figsize=(10,5))
    for uid, group in df_sorted.groupby('uid'):
        group['time_diff'].dropna().plot(kind='hist', bins=30, alpha=0.5, label=f'UID {uid}')
    
    plt.xlabel('Интервал между измерениями (сек)')
    plt.ylabel('Количество')
    plt.title('Распределение интервалов между оценками Incentive')
    plt.legend()
    plt.show()

def main():
    # Загрузка данных
    df = pd.read_excel(OUTPUT_DIRECTORY_MINER)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%Y %I:%M:%S %p')

    
    plot_incentive(df)
    analyze_intervals(df)

if __name__ == '__main__':
    main()
