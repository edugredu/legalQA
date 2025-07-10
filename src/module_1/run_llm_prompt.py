import os
import glob
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

PROMPT_PATH = Path(__file__).parent / "prompts/llm_prompt.txt"
#INPUTS_DIR = Path(__file__).parent / "inputs"
#OUTPUTS_DIR = Path(__file__).parent / "outputs"
MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b:free")
#API_KEY = os.environ.get("OPENROUTER_API_KEY")

#assert API_KEY, "OPENROUTER_API_KEY environment variable must be set."

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
        extra_headers={
            # Optionally set your site info for openrouter.ai rankings
            # "HTTP-Referer": "https://your-site.example.com",
            # "X-Title": "Your Site Name",
        },
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

def write_output(output, outputs_dir):
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_file = outputs_dir / "llm_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Output written to {output_file}")

def run_module_1(promptInput, API_KEY=None):
    try:
        assert API_KEY, "OPENROUTER_API_KEY environment variable must be set."
        template = load_prompt_template(PROMPT_PATH)
        variables = {'user_query': promptInput}
        prompt = fill_prompt(template, variables)
        answer = call_openrouter_llm(prompt, API_KEY, model=MODEL)
        return answer
    
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

'''
def main():
    try:
        template = load_prompt_template(PROMPT_PATH)
        variables = load_inputs(INPUTS_DIR)
        prompt = fill_prompt(template, variables)
        answer = call_openrouter_llm(prompt, API_KEY, model=MODEL)
        write_output(answer, OUTPUTS_DIR)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
'''
