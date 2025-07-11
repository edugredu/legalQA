from src.module_1.run_llm_prompt import run_module_1
from src.module_2.module_2 import run_module_2
from src.module_3.apiLaw import mod3_response
from src.module_4.module_4 import module_4
from src.module_5.sequence_filterer import SequenceFilterer
from src.module_5.run_llm import run_llm_pipeline_with_variables
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
        
        for example in examples:
            print(f"Processing example: {example}")
            
            ####################################################################
            ## STEP 1  Translates the user query into a legal question domain ##
            ####################################################################
            output_1 = run_module_1(example, API_KEY=API_KEY)  # Call your LLM model with the example query
            print(f"AI-generated response for example: {output_1}\n")


        #output_1 = 'What are the legal and regulatory requirements that businesses must comply with under the European Union Toy Safety Directive (2009/48/EC), including applicable safety standards, conformity assessment procedures, labeling obligations, CE marking requirements, and other enforceable compliance measures for the sale of toys within the EU?'
            #output_1 = 'What are the legal and regulatory requirements that businesses must comply with under the European Union Toy Safety Directive (2009/48/EC), including applicable safety standards, conformity assessment procedures, labeling obligations, CE marking requirements, and other enforceable compliance measures for the sale of toys within the EU?'
    

            #################################################################
            ## STEP 2 Find the relevvant laws according to the legal query ##
            #################################################################

            print("Getting relevant laws for the query...")
            output_2 = run_module_2(user_query, K=5)
            print(f"Relevant laws found for query '{user_query}':")
            print(output_2)

            ###############################################
            ## STEP 3 Retrieve the full text of the laws ##
            ###############################################
            print("Retrieving full text of laws...")
            output_3 = mod3_response(output_2)
            print("Full text of laws retrieved successfully.")
            print(output_3)
        
            ####################################################################################
            ## STEP 4 Filter by laws and articles based on semantic similarity with the query ##
            ####################################################################################

            
        
            print("Getting the most relevant sections for each law...")
            output_4 = module_4(output_3, output_1)
            print("Most relevant sections for each law:")
            print(output_4.head())

            #####################################################################################
            ## STEP 5 Aggregate and summarize the relevant articles ##
            #####################################################################################

            # Initialize the filterer
            print("Aggregating and summarizing relevant articles...")
            filterer = SequenceFilterer(minimum_length_limit=20, max_added_word_limit=10000)
            output_5 = filterer.aggregate_all_articles(df=output_4, title_df=output_3, source_column='filtered_json')
            output_5 = filterer.generate_text_prompt(output_5)

            print("Aggregated and summarized relevant articles:")
            print(output_5)

            ###########################################################
            ## STEP 6 Generate the final answer based on our context ##
            ###########################################################


            user_query = output_1
            summarized_laws = output_5
        
            response = run_llm_pipeline_with_variables(
            prompt_variables={
                "user_query": user_query,
                "summarized_laws": summarized_laws
            }
            )

        # Example structure:
        # 1. Validate query is EU law related
        # 2. Process with your AI models
        # 3. Generate response
        # 4. Format and return
        
        # Placeholder response
        #response = f"Processing query: {user_query}\n\nThis is where your AI-generated legal guidance will appear."
        return response
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        return f"Error processing query: {str(e)}"


#process_legal_query("What Rules Do Companies Have to Follow When Selling Toys in the EU?")  # Example query