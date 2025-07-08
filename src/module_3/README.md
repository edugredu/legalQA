# legalQA


## Modules of the project

1. Rrephrasing user input -> Adriana 
     INPUT: User query OUPUT: string rephrased
2. Retrieving relevant laws -> Hamish
     OUTPUT: Df with relevant rows
3. Retrieving whole laws’ texts ->  Eduardo
     INPUT: lawsToBeConsidered.csv with columns celex_id,reference,summary
     OUTPUT: lawsWithText.csv with columns celex_id,reference,summary,structured_text
4. Extract relevant paragraphs from the texts -> Fahad - Fabio
     OUTPUT: Df with new column that contains relevant paragraphs
5. Generation of the answer according to the relevant texts
    OUPUT: String with the response
6. LLM as a Judge -> Fabio - Fahad
    OUTPUT: Yes/no decision