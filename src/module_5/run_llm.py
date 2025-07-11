from time import time

def run_llm_pipeline_with_variables(prompt_variables, 
                                   prompt_file="prompts/llm_prompt.txt",
                                   outputs_dir="outputs",
                                   model=None,
                                   api_key=None):
    """
    LLM pipeline that accepts variables directly instead of loading from input files.
    
    Args:
        prompt_variables: Dictionary with variable names and their values
        prompt_file: Path to the prompt template file
        outputs_dir: Directory to save output
        model: OpenRouter model to use
        api_key: OpenRouter API key
    
    Returns:
        str: The LLM response content
    """
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    from openai import OpenAI
    
    # Load environment variables
    load_dotenv()
    
    # Setup paths and configuration
    base_path = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    PROMPT_PATH = base_path / prompt_file
    OUTPUTS_DIR = base_path / outputs_dir
    MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b:free")
    API_KEY = os.environ.get("OPENROUTER_API_KEY")
    
    assert API_KEY, "OPENROUTER_API_KEY environment variable must be set or provided as parameter."
    
    # Helper functions
    def load_prompt_template(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def fill_prompt(template, variables):
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing variable for prompt: {e}")
    
    def call_openrouter_llm(prompt, api_key, model):
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
    
    def write_output(output, outputs_dir):
        outputs_dir.mkdir(parents=True, exist_ok=True)
        output_file = outputs_dir / f"llm_output{int(time())}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Output written to {output_file}")
        return output_file
    
    # Main execution logic
    try:
        template = load_prompt_template(PROMPT_PATH)
        prompt = fill_prompt(template, prompt_variables)
        answer = call_openrouter_llm(prompt, API_KEY, MODEL)
        output_file = write_output(answer, OUTPUTS_DIR)
        return answer
    except Exception as e:
        print(f"Error: {e}")
        raise e



def call_llm_with_processed_data(
                                prompt_file="prompts/llm_prompt.txt",
                                outputs_dir="outputs",
                                model=None,
                                prompt_variables=None):
    """
    Simple function to call LLM directly with already processed text data.
    
    Args:
        processed_text: Your already processed text string
        prompt_file: Path to prompt template
        outputs_dir: Directory for output files
        model: OpenRouter model to use
        api_key: OpenRouter API key
    
    Returns:
        str: The LLM response
    """

    
    # Call the LLM pipeline directly
    return run_llm_pipeline_with_variables(
        prompt_variables=prompt_variables,
        prompt_file=prompt_file,
        outputs_dir=outputs_dir,
        model=model,
    )
