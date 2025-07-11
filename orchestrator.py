import os
from src.module_1 import run_module_1
from src.module_2 import run_module_2
from src.module_3 import run_module_3
from src.module_4 import run_module_4
from src.module_5 import run_module_5

def process_legal_query(user_query: str) -> str:
    """
    Process a user's legal query and return a response.
    
    Args:
        user_query (str): The user's legal question
        
    Returns:
        str: The AI-generated response about EU law
    """
    
    try:

        API_KEY = os.environ.get("OPENROUTER_API_KEY")

        ####################################################################################
        ########## STEP 1  Translates the user query into a legal question domain ##########
        ####################################################################################
        
        output_1 = run_module_1(user_query, API_KEY=API_KEY)

        ####################################################################################
        ############ STEP 2 Find the relevvant laws according to the legal query ###########
        ####################################################################################

        output_2, titles = run_module_2(output_1, K=5)
        
        ####################################################################################
        #################### STEP 3 Retrieve the full text of the laws #####################
        ####################################################################################
        
        output_3 = run_module_3(output_2)

        ####################################################################################
        ## STEP 4 Filter by laws and articles based on semantic similarity with the query ##
        ####################################################################################

        output_4 = run_module_4(output_3, output_1)

        #####################################################################################
        ############### STEP 5 Generate the final answer based on our context ###############
        #####################################################################################

        output_5 = run_module_5(output_4, output_3, output_1)

        return output_5, titles
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return f"Error processing query: {str(e)}"