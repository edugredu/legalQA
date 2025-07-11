import re

def clean_llm_response(response: str) -> str:
    """
    Remove thinking sections from LLM responses to provide clean output.
    
    Args:
        response (str): Raw LLM response that may contain thinking sections
        
    Returns:
        str: Cleaned response with thinking sections removed
    """
    
    # Remove XML-style thinking tags (most common pattern)
    response = re.sub(r'', '', response, flags=re.DOTALL)
    response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
    
    # Remove other common thinking patterns
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    response = re.sub(r'\[thinking\].*?\[/thinking\]', '', response, flags=re.DOTALL)
    
    # Remove lines that start with thinking indicators
    thinking_patterns = [
        r'^Let me think.*?$',
        r'^I need to think.*?$', 
        r'^Thinking:.*?$',
        r'^.*?\(thinking\).*?$'
    ]
    
    for pattern in thinking_patterns:
        response = re.sub(pattern, '', response, flags=re.MULTILINE | re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)  # Remove triple+ newlines
    response = response.strip()
    
    return response
