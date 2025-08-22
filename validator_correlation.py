import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import OUTPUT_DIRECTORY_VALIDATOR

df = pd.read_excel(OUTPUT_DIRECTORY_VALIDATOR)

# Корреляции между числовыми полями
corr = df[['is_unique', 'description_relevance_scores', 'query_relevance_scores', 'score', 'reward_value']].corr()

# Отобразим корреляционную матрицу
plt.figure(figsize=(10, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Корреляции между признаками и наградой (reward)")
plt.show()

# Посмотрим, где reward < 0.2
low_reward = df[df['reward_value'] < 0.2]
print(low_reward[['query', 'description_relevance_scores', 'query_relevance_scores', 'score', 'reward_value']])
