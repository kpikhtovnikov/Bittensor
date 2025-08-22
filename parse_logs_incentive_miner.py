import os
import re
import pandas as pd
from datetime import datetime
import openpyxl
from config import LOG_DIRECTORY_MINER, OUTPUT_DIRECTORY_MINER

def parse_logs(directory):
    # Регулярные выражения для извлечения данных
    timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    incentive_pattern = re.compile(r'Incentive:([\d.]+)')
    uid_pattern = re.compile(r'UID:(\d+)')
    
    results = []
    
    for filename in os.listdir(directory):
        if filename.endswith('.rtf'):  # Обрабатываем логи и текстовые файлы
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    if "Incentive:" in line and "UID:" in line:
                        # Извлекаем timestamp
                        ts_match = timestamp_pattern.search(line)
                        timestamp = ts_match.group(1) if ts_match else None
                        
                        # Извлекаем incentive
                        inc_match = incentive_pattern.search(line)
                        incentive = float(inc_match.group(1)) if inc_match else None
                        
                        # Извлекаем UID
                        uid_match = uid_pattern.search(line)
                        uid = uid_match.group(1) if uid_match else None
                        
                        if timestamp and incentive and uid:
                            # Форматируем имя файла согласно примеру
                            formatted_filename = f"UID {uid}.rtf"
                            
                            # Преобразуем timestamp в нужный формат (без миллисекунд)
                            try:
                                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                                formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                formatted_timestamp = timestamp
                            
                            results.append({
                                'filename': formatted_filename,
                                'timestamp': formatted_timestamp,
                                'incentive': incentive
                            })
    
    return pd.DataFrame(results)

# Основной скрипт
if __name__ == "__main__":
    log_directory = LOG_DIRECTORY_MINER
    output_file = OUTPUT_DIRECTORY_MINER
    
    df = parse_logs(log_directory)
    
    if not df.empty:
        # Используем ExcelWriter для тонкой настройки
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # Получаем доступ к листу
            worksheet = writer.sheets['Data']
            
            # Находим индекс столбца 'timestamp' (нумерация с 1)
            col_idx = df.columns.get_loc('timestamp') + 1
            
            # Устанавливаем текстовый формат для всего столбца
            for row in range(1, len(df) + 2):  # +2: заголовок + все строки данных
                cell = worksheet.cell(row=row, column=col_idx)
                cell.number_format = '@'  # Формат "Текст" в Excel
                
        print(f"Успешно экспортировано {len(df)} записей в {output_file}")
    else:
        print("Данные не найдены")