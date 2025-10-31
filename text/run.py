import csv
from openai import OpenAI
import json
from datetime import datetime
import pandas as pd
import random
import re
import os

from user_inputs import user_inputs_text

client = OpenAI(api_key=("REMOVED"))

PROMPT_COACH_ID = "pmpt_6900847673688195be5e271c67dec86305916e175b396892"
PROMPT_FAST_ID = "pmpt_690083ffc2088190a8f29870d017d4100afefbc8dfdc5b7f"
PROMPT_SMART_ID = "pmpt_69008436316881938bd29679d2f247d209ca71bbb01e55db"
ANSWER_COUNT = "1"


def log(title, width=148, fill="="):
    decorated = title.center(width, fill)
    print(f"{decorated}")


# ✅ JSON 정제 및 안전 파싱
def safe_json_loads(text):
    try:
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
        return json.loads(text)
    except json.JSONDecodeError:
        print("⚠️ JSONDecodeError 발생 — 원문을 그대로 저장합니다.")
        return {"error": "invalid_json", "raw_output": text}


# ✅ 랜덤 키워드 선택
def randomize_keywords(json_data):
    randomized = {}
    for key, values in json_data.items():
        if isinstance(values, list):
            if len(values) > 1:
                k = random.randint(1, len(values))
                selected = random.sample(values, k)
            else:
                selected = values
            randomized[key] = selected
        else:
            randomized[key] = values
    return randomized


def process_prompts(inputs):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ✅ 폴더 자동 생성
    os.makedirs("prompt_coach_result", exist_ok=True)
    os.makedirs("random_selection", exist_ok=True)
    os.makedirs("fast_result", exist_ok=True)
    os.makedirs("smart_result", exist_ok=True)

    # ✅ 결과 파일 경로
    output_path1 = f"prompt_coach_result/text_pc_{timestamp}.csv"
    output_path2 = f"random_selection/text_rs_{timestamp}.csv"
    output_path3 = f"fast_result/text_fast_{timestamp}.csv"
    output_path4 = f"smart_result/text_smart_{timestamp}.csv"

    # ✅ 초기화 (헤더 생성)
    pd.DataFrame(columns=["input", "output"]).to_csv(output_path1, index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["input", "output"]).to_csv(output_path2, index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["input", "output"]).to_csv(output_path3, index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["input", "output"]).to_csv(output_path4, index=False, encoding="utf-8-sig")

    # ✅ 입력 루프 시작
    for i, input_text in enumerate(inputs, 1):
        log(f"[Progress] {i}/{len(inputs)}")
        print(f"[User Input] {input_text}")

        try:
            # ✅ 1단계: PROMPT COACH
            response1 = client.responses.create(
                prompt={"id": PROMPT_COACH_ID, "variables": {"input": input_text}},
                input="",
                service_tier="priority",
            )
            log("[PROMPT COACH] Keyword Generation Success")
            print(response1.output_text)

            output_json = safe_json_loads(response1.output_text)
            randomized_json = randomize_keywords(output_json)

            # ✅ 결과 저장
            row_pc = {
                "input": input_text,
                "output": json.dumps({
                    "original_keywords": output_json,
                    "randomized_keywords": randomized_json
                }, ensure_ascii=False)
            }
            pd.DataFrame([row_pc]).to_csv(output_path1, mode="a", header=False, index=False, encoding="utf-8-sig")

            # ✅ 랜덤 키워드만 별도 저장
            keyword_variables_list = [{"keyword": randomized_json}]
            keyword_value = json.dumps(keyword_variables_list, ensure_ascii=False, indent=2)
            pd.DataFrame([{"input": input_text, "output": keyword_value}]).to_csv(
                output_path2, mode="a", header=False, index=False, encoding="utf-8-sig"
            )

        except Exception as e:
            print(f"❌ PROMPT COACH 오류 발생: {e}")
            pd.DataFrame([{"input": input_text, "output": f"Error: {e}"}]).to_csv(
                output_path1, mode="a", header=False, index=False, encoding="utf-8-sig"
            )
            continue  # 다음 입력으로 진행

        # ✅ 2단계: FAST
        try:
            response2 = client.responses.create(
                prompt={
                    "id": PROMPT_FAST_ID,
                    "variables": {"answercount": ANSWER_COUNT, "keyword": keyword_value},
                },
                input=input_text,
                service_tier="priority",
            )
            log("[FAST] Optimization Success")
            print(response2.output_text)

            output_json = safe_json_loads(response2.output_text)
            row_fast = {"input": input_text, "output": json.dumps(output_json, ensure_ascii=False)}
            pd.DataFrame([row_fast]).to_csv(output_path3, mode="a", header=False, index=False, encoding="utf-8-sig")

        except Exception as e:
            print(f"❌ FAST 실행 오류 발생: {e}")
            pd.DataFrame([{"input": input_text, "output": f"Error: {e}"}]).to_csv(
                output_path3, mode="a", header=False, index=False, encoding="utf-8-sig"
            )

        # ✅ 3단계: SMART
        try:
            response3 = client.responses.create(
                prompt={
                    "id": PROMPT_SMART_ID,
                    "variables": {"answercount": ANSWER_COUNT, "keyword": keyword_value},
                },
                input=input_text,
                service_tier="priority",
            )
            log("[SMART] Optimization Success")
            print(response3.output_text)

            output_json = safe_json_loads(response3.output_text)
            row_smart = {"input": input_text, "output": json.dumps(output_json, ensure_ascii=False)}
            pd.DataFrame([row_smart]).to_csv(output_path4, mode="a", header=False, index=False, encoding="utf-8-sig")

        except Exception as e:
            print(f"❌ SMART 실행 오류 발생: {e}")
            pd.DataFrame([{"input": input_text, "output": f"Error: {e}"}]).to_csv(
                output_path4, mode="a", header=False, index=False, encoding="utf-8-sig"
            )

    print("\n✅ 전체 입력 처리 완료!")
    print(f"📂 Prompt Coach 결과: {output_path1}")
    print(f"📂 Random Selection 결과: {output_path2}")
    print(f"📂 FAST 결과: {output_path3}")
    print(f"📂 SMART 결과: {output_path4}")


if __name__ == "__main__":
    process_prompts(user_inputs_text)
