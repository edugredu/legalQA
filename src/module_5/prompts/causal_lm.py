import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

class LLMTaskRunner:
    def __init__(self, model: str):
        load_dotenv()
        self.model = model
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        assert self.api_key, "OPENROUTER_API_KEY environment variable must be set."
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

    def load_prompt_template(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def load_variables_from_dir(self, inputs_dir):
        variables = {}
        for file_path in glob.glob(str(Path(inputs_dir) / "*.txt")):
            var_name = Path(file_path).stem
            with open(file_path, "r", encoding="utf-8") as f:
                variables[var_name] = f.read().strip()
        return variables

    def fill_prompt(self, template, variables):
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt: {e}")

    def call_llm(self, prompt):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content

    def write_output(self, output, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {output_path}")

    def run_task(self, prompt_path, inputs_dir=None, variables=None, output_path=None):
        template = self.load_prompt_template(prompt_path)
        if variables is None and inputs_dir is not None:
            variables = self.load_variables_from_dir(inputs_dir)
        elif variables is None:
            variables = {}
        prompt = self.fill_prompt(template, variables)
        answer = self.call_llm(prompt)
        if output_path:
            self.write_output(answer, output_path)
        return answer

# Example usage:
# runner = LLMTaskRunner()
# answer = runner.run_task(
#     prompt_path="prompts/llm_prompt.txt",
#     inputs_dir="inputs",
#     output_path="outputs/llm_output.txt"
# )
