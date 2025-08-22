import os
import re
import pandas as pd
from config import LOG_DIRECTORY_VALIDATOR, OUTPUT_DIRECTORY_VALIDATOR

def extract_timestamp(line):
    match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', line)
    return match.group(0) if match else ""

def extract_query_and_miners(line):
    match = re.search(r"Sending query '([^']+)' to miners tensor\(\[([^\]]+)\]", line)
    if match:
        query = match.group(1)
        miner_ids = [int(x.strip()) for x in match.group(2).split(',')]
        return query, miner_ids
    return "", []

def extract_step_block(line):
    match = re.search(r'step\((\d+)\) block\((\d+)\)', line)
    return match.groups() if match else ("", "")

def extract_responses(line):
    match = re.search(r'Received responses: (.*)', line)
    return match.group(1).strip() if match else ""

def extract_rewards_and_penalties(block_lines):
    rewards = {}
    for line in block_lines:
        reward_match = re.search(r'Rewarding miner=(\d+) with reward=([\d.]+)', line)
        if reward_match:
            rewards[int(reward_match.group(1))] = ('Rewarding', float(reward_match.group(2)))
        penalty_match = re.search(r'Penalizing miner=(\d+) with penalty=([\d.]+)', line)
        if penalty_match:
            rewards[int(penalty_match.group(1))] = ('Penalizing', float(penalty_match.group(2)))
    return rewards

def split_responses(responses_str):
    pattern = re.compile(r"Videos\(query='.*?'\s*,\s*num_videos=\d+,\s*video_metadata=.*?\)", re.DOTALL)
    return pattern.findall(responses_str)

def has_valid_metadata(response: str) -> bool:
    # Возвращает True, если video_metadata не пустое / не None
    match = re.search(r'video_metadata\s*=\s*(.*)\)', response)
    if not match:
        return False
    metadata = match.group(1).strip()
    return metadata not in ("[]", "None", "")

def extract_scores(block_text):
    pattern = re.compile(
        r'is_unique:\s*(\[[^\]]+\])[\s\S]*?'
        r'description_relevance_scores:\s*(\[[^\]]+\])[\s\S]*?'
        r'query_relevance_scores:\s*(\[[^\]]+\])[\s\S]*?'
        r'score:\s*([\d.]+)',
        re.MULTILINE
    )
    matches = pattern.findall(block_text)
    scores = []
    for match in matches:
        is_unique = sum([x.strip() == 'True' for x in match[0].strip('[]').split(',')])
        desc_scores = [float(x) for x in match[1].strip('[]').split(',')]
        query_scores = [float(x) for x in match[2].strip('[]').split(',')]
        score = float(match[3])
        scores.append({
            'is_unique': is_unique,
            'description_avg': sum(desc_scores) / len(desc_scores) if desc_scores else 0.0,
            'query_avg': sum(query_scores) / len(query_scores) if query_scores else 0.0,
            'score': score
        })
    return scores

def parse_block(block_lines, filename):
    block_text = "\n".join(block_lines)
    timestamp = extract_timestamp(block_lines[0])
    query, miner_ids = extract_query_and_miners(block_lines[0])
    step, block = extract_step_block(block_lines[-1])
    rewards = extract_rewards_and_penalties(block_lines)
    responses_line = next((line for line in block_lines if 'Received responses:' in line), "")
    responses_list = split_responses(extract_responses(responses_line))
    score_blocks = extract_scores(block_text)

    # Приводим responses_list к длине miner_ids
    while len(responses_list) < len(miner_ids):
        responses_list.append("Videos(query='', num_videos=0, video_metadata=[])")

    # Создаём соответствие score → miner_id (по reward value)
    score_to_miner = {}
    used_miners = set()
    for score_block in score_blocks:
        score_val = round(score_block["score"], 5)  # округляем до 5 знаков для сопоставления
        for miner_id, (rtype, rvalue) in rewards.items():
            if rtype == "Rewarding" and round(rvalue, 5) == score_val and miner_id not in used_miners:
                score_to_miner[miner_id] = score_block
                used_miners.add(miner_id)
                break

    rows = []
    for i, miner_id in enumerate(miner_ids):
        response = responses_list[i] if i < len(responses_list) else ""
        score_data = score_to_miner.get(miner_id, {
            'is_unique': 0,
            'description_avg': 0.0,
            'query_avg': 0.0,
            'score': 0.0
        })
        reward_type, reward_value = rewards.get(miner_id, ("", 0.0))
        penalty = reward_value if reward_type == "Penalizing" else 0.0
        reward = reward_value if reward_type == "Rewarding" else 0.0

        rows.append({
            "filename": filename,
            "timestamp": timestamp,
            "query": query,
            "miner_id": miner_id,
            "Received responses": response,
            "is_unique": score_data["is_unique"],
            "description_relevance_scores": score_data["description_avg"],
            "query_relevance_scores": score_data["query_avg"],
            "score": score_data["score"],
            "reward_type": reward_type,
            "reward_value": reward,
            "penalty": penalty,
            "step": step,
            "block": block
        })

    return rows

def split_blocks(lines):
    blocks = []
    current_block = []
    for line in lines:
        if "Sending query" in line:
            if current_block:
                blocks.append(current_block)
                current_block = []
        current_block.append(line)
        if "step(" in line and "block(" in line:
            blocks.append(current_block)
            current_block = []
    return blocks

def process_logs(directory):
    all_data = []
    for filename in os.listdir(directory):
        if filename.endswith(".log"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
                blocks = split_blocks(lines)
                for block in blocks:
                    all_data.extend(parse_block(block, filename))
    return pd.DataFrame(all_data)

if __name__ == "__main__":
    log_directory = LOG_DIRECTORY_VALIDATOR  # Укажите свою папку
    output_file = OUTPUT_DIRECTORY_VALIDATOR  # Укажите свою папку

    df = process_logs(log_directory)
    df.to_excel(output_file, index=False, engine="openpyxl")
    print(f"✅ Готово! Данные сохранены в {output_file}")
