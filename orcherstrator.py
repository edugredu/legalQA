from src.module_1.run_llm_prompt import run_module_1
from src.module_2.module_2 import run_module_2
import os



def process_legal_query(user_query: str) -> str:
    """
    Process a user's legal query and return a response.
    
    Args:
        user_query (str): The user's legal question
        
    Returns:
        str: The AI-generated response about EU law
    """
    # Your orchestrator logic here
    # This is where you'll integrate your models and Gen AI
    
    try:

        API_KEY = os.environ.get("OPENROUTER_API_KEY")

        examples = ["What Rules Do Companies That Handle Online Payments Have to Follow?",
                    "What Rules Do Companies Have to Follow When Sending Personal Data Outside the EU?",
                    "What Rules Do Companies Have to Follow When Selling Toys in the EU?"]
        

        ############
        ## STEP 1 ##
        ############
        
        output_1 = 'What are the legal and regulatory requirements that businesses must comply with under the European Union Toy Safety Directive (2009/48/EC), including applicable safety standards, conformity assessment procedures, labeling obligations, CE marking requirements, and other enforceable compliance measures for the sale of toys within the EU?'
        '''
        try:
            print(f"Executing step 1")
            output_1 = run_module_1(user_query, API_KEY=API_KEY)  # Call your LLM model with the user query
        except Exception as e:
            output_1 = f"Error in LLM processing: {str(e)}"
        '''
        print(f"Processing query: {user_query}\n\nAI-generated response: {output_1}")

        #The output_1 is a textual response in a legal way of writing

        ############
        ## STEP 2 ##
        ############

        results = run_module_2(user_query, K=5)

        #The output_2 is a dataframe

        ############
        ## STEP 3 ##
        ############
        print(results.head())
        output_3 = None
 
        #The output_2 is a dataframe



        # Example structure:
        # 1. Validate query is EU law related
        # 2. Process with your AI models
        # 3. Generate response
        # 4. Format and return
        
        # Placeholder response
        #response = f"Processing query: {user_query}\n\nThis is where your AI-generated legal guidance will appear."
        print()
        print(f"Retrieved documents: {output_2}")
        return output_1
        
    except Exception as e:
        return f"Error processing query: {str(e)}"


process_legal_query("What Rules Do Companies Have to Follow When Selling Toys in the EU?")  # Example query