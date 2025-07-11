import os
import glob
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

PROMPT_PATH = Path(__file__).parent / "llm_prompt.txt"
MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b:free")

def load_prompt_template(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_inputs(inputs_dir):
    variables = {}
    for file_path in glob.glob(str(inputs_dir / "*.txt")):
        var_name = Path(file_path).stem
        with open(file_path, "r", encoding="utf-8") as f:
            variables[var_name] = f.read().strip()
    return variables

def fill_prompt(template, variables):
    try:
        return template.format(**variables)
    except KeyError as e:
        raise ValueError(f"Missing variable for prompt: {e}")

def call_openrouter_llm(prompt, api_key, model=MODEL):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    completion = client.chat.completions.create(
        extra_headers={},
        extra_body={},
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return completion.choices[0].message.content

def run_module_1(promptInput, API_KEY=None):
    try:
        assert API_KEY, "OPENROUTER_API_KEY environment variable must be set."
        template = load_prompt_template(PROMPT_PATH)
        variables = {'initial_query': promptInput}
        prompt = fill_prompt(template, variables)
        answer = call_openrouter_llm(prompt, API_KEY, model=MODEL)
        return answer
    
    except Exception as e:
        print(f"Error: {e}")
        exit(1)