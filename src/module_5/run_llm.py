from time import time
from src.module_5.sequence_filterer import SequenceFilterer

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
    
    # Main execution logic
    try:
        template = load_prompt_template(PROMPT_PATH)
        prompt = fill_prompt(template, prompt_variables)
        answer = call_openrouter_llm(prompt, API_KEY, MODEL)
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


#lawsDF = output_3
#filteredDF = output_4

def module_5(filteredDF, lawsDF, user_query):

    filterer = SequenceFilterer(minimum_length_limit=20, max_added_word_limit=10000)
    summarized_laws = filterer.aggregate_all_articles(df=filteredDF, title_df=lawsDF, source_column='filtered_json')
    summarized_laws = filterer.generate_text_prompt(summarized_laws)

    response = run_llm_pipeline_with_variables(
        prompt_variables={
            "user_query": user_query,
            "summarized_laws": summarized_laws
        }
    )

    return response