import csv
from openai import OpenAI
import json
from datetime import datetime
import pandas as pd
import random
import re
import os

from user_inputs import user_inputs_text


client = OpenAI(api_key=("your-api-key-here"))

PROMPT_COACH_ID = "pmpt_6900847673688195be5e271c67dec86305916e175b396892"

PROMPT_FAST_ID = "pmpt_690083ffc2088190a8f29870d017d4100afefbc8dfdc5b7f"

PROMPT_SMART_ID = "pmpt_69008436316881938bd29679d2f247d209ca71bbb01e55db"

ANSWER_COUNT = "1"

def log(title, width=148, fill="="):
    decorated = title.center(width, fill)
    print(f"{decorated}")


# ✅ Randomly select partial keywords from JSON
def randomize_keywords(json_data):
    randomized = {}
    for key, values in json_data.items():
        if isinstance(values, list):
            if len(values) > 1:
                k = random.randint(1, len(values))  # Select at least one
                selected = random.sample(values, k)
            else:
                selected = values
            randomized[key] = selected
        else:
            randomized[key] = values
  
    return randomized


def process_prompts(inputs):
    results1 = []
    results2 = []
    results3 = []
    results4 = []

    keyword_variables_list = []  # ✅ For Response API keyword variable list

    for i, input_text in enumerate(inputs, 1):
        log(f"[Progress] {i}/{len(inputs)}")
        log("[User Input]")
        print(input_text)

        keyword_variables_list = []

        # ✅ First Prompt Execution
        response1 = client.responses.create(
            prompt={
                "id": PROMPT_COACH_ID,
                "variables": {
                    "input": input_text,                    
                }
            },
            input=""
        )

        log("[PROMPT COACH] Keyword Generation Success")
        print(response1.output_text)

        # ✅ JSON Parsing
        output_json = json.loads(response1.output_text)

        # ✅ Randomization
        randomized_json = randomize_keywords(output_json)
        keyword_variables_list.append({
            "keyword": randomized_json
        })

        results1.append({
            "input": input_text,
            "original_keywords": json.dumps(output_json, ensure_ascii=False),
            "randomized_keywords": json.dumps(randomized_json, ensure_ascii=False)
        })

        # ✅ CSV Formatting
        row = {"input": input_text}
        for idx, (key, value) in enumerate(randomized_json.items(), 1):
            col_name = f"Keyword_{idx}"
            if isinstance(value, list):
                val_str = ", ".join(map(str, value))
            else:
                val_str = str(value)
            row[col_name] = f"{key}: [{val_str}]"
        results2.append(row)

        keyword_value = json.dumps(keyword_variables_list, ensure_ascii=False, indent=2)

        log("[PROMPT COACH] Keyword Random Selection Done")
        print(keyword_value)

        # ✅ Second Prompt Execution
        response2 = client.responses.create(
            prompt={
                "id": PROMPT_FAST_ID,
                "variables": {
                    "answercount": ANSWER_COUNT,
                    "keyword": keyword_value,                   
                }
            },
            input=input_text
        )
        log("[FAST] Optimization Success")
        print(response2.output_text)
        output_json = json.loads(response2.output_text)
        
        row = {"input": input_text}

        results3.append(row)
        results3.append(output_json)

        response3 = client.responses.create(
            prompt={
                "id": PROMPT_SMART_ID,
                "variables": {
                    "answercount": ANSWER_COUNT,
                    "keyword": keyword_value,                   
                }
            },
            input=input_text
        )
        log("[SMART] Optimization Success")
        print(response3.output_text)
        output_json = json.loads(response3.output_text)
        
        row = {"input": input_text}

        results4.append(row)
        results4.append(output_json)
        


    # ✅ Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path1 = f"prompt_coach_result/video_pc_{timestamp}.csv"
    output_path2 = f"random_selection/video_rs_{timestamp}.csv"
    output_path3 = f"fast_result/video_fast_{timestamp}.csv"
    output_path4 = f"smart_result/video_smart_{timestamp}.csv"

    df1 = pd.DataFrame(results1)
    df1.to_csv(output_path1, index=False, encoding="utf-8-sig")
    print(f"📂 [Prompt Coach] completed! Result saved at '{output_path1}'")

    df2 = pd.DataFrame(results2)
    df2.to_csv(output_path2, index=False, encoding="utf-8-sig")
    print(f"📂 [Random Selection] completed! Result saved at '{output_path2}'")

    df3 = pd.DataFrame(results3)
    df3.to_csv(output_path3, index=False, encoding="utf-8-sig")
    print(f"📂 [FAST] completed! Result saved at '{output_path3}'")

    df4 = pd.DataFrame(results4)
    df4.to_csv(output_path4, index=False, encoding="utf-8-sig")
    print(f"📂 [SMART] completed! Result saved at '{output_path4}'")



    # ✅ Return JSON
    return json.dumps(keyword_variables_list, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_prompts(user_inputs_text)