import os
import json

from TOOL_IMPLEMENTATION.client_set_and_file_prep import create_client, read_document, preprocess_text
client = create_client()

with open('T_GPT3.5/sections_and_clauses_doc.json', 'r') as f:
    sections_and_clauses_doc = json.load(f)

with open('T_GPT3.5/file_paths.json', 'r') as f:
    file_paths = json.load(f)

##################################             MASTER LISTS    ##################################################
#################################################################################################################



################                         Comparison of entire documents at a time
############################################################################################################

# Instruction for LLM to output JSON
json_instruction = "You are a helpful assistant designed to output JSON."

message_comp_entire_docs = """
You are a helpful assistant tasked with analyzing, organizing, and streamlining sections and clauses from two Non-Disclosure Agreement (NDA) documents into a single, structured and collectively exhaustive output.
You will be provided with two summarised Non-Disclosure Agreements. It is crucial to ensure that each unique key point from the documents is distinctly and accurately represented in the final output.

Detailed Instructions:
    1.	Review and Compare: Conduct a detailed review of each section and its associated clauses in the provided NDAs. Identify similarities and differences across sections and clauses, with particular focus on their content and intended purposes.
    2.	Combine similar sections: Merge sections that address similar topics. Focus on the actual content and intent behind the clauses within sections when evaluating their similarity. Even if the specific clauses are not identical, but as long as they discuss the same topic, the respective sections should be combined.
    3.	Present each key point separately: Within the merged sections, ensure each key point is presented separately. Do not merge clauses into a single lengthy sentence. Instead, list each clause as an independent item in the output. 
    4.	Avoid Repetition: Prevent redundancy by removing duplicate clause meanings. However, include variations that introduce differend perspectives or additional details.
    5.	Capture All Variants: While avoiding exact duplicates, make sure to include all variants of clauses that express different nuances or conditions. This ensures a comprehensive representation of each section's intended meaning across the documents.
    6.	Ensure Comprehensiveness and Organization: Organize each key point of clauses as a separate entry in a list. The final list should be comprehensive, capturing all essential information from the original documents without missing any key points or clauses. Assign a title to each section by choosing one of the original titles. Choose a title that better describes the content of that section.

Output Format:
    {
        "Section Name": ["Clause 1", "Clause 2", ...],
        "Section Name": ["Clause 1", "Clause 2", ...],
        ...
    }

Example:
    First document: {Return of materials: ["Upon termination of the agreement, all materials provided by the Company must be returned by the Recipient within 30 days.", "The party responsible for the destruction shall provide a written record evidencing the completion of such destruction.",], Termination: ["This agreement applies to disclosures made from the Effective Date to one year after, or earlier if termination is communicated in writing.", "Rights and obligations detailed in Sections 5 and 6 have specific expiration terms as outlined in those sections.", "The agreement formally ends three years from the Effective Date, except for restricted use of Confidential information which extends beyond that period."]}
    Second document: {Return of information: ["All materials provided by the Company must be returned or destroyed by the Recipient within 30 days of contract termination.", "All confidential materials must be returned or destroyed at the end of the contract period."], Term: ["The agreement shall commence on the effective date and continue for five years, unless earlier terminated in writing.", "The receiving Party's obligations for non-disclosure and restricted use of Confidential Information will persist beyond the termination or expiration of any Services Agreement."]}

    Output: {
        Return of materials: ["Upon termination of the agreement, all materials must be returned or destroyed.", "The agreement specifies a time frame within which all documents must be returned or destroyed.", "The party responsible for the destruction must provide written proof of completed destruction."], 
        Term: ["Agreement is effective from the Effective Date and formally ends X years thereafter.", "Earlier termination is possible if communicated in writing.", "Some sections have specific expiration terms.", "Obligations for non-disclosure and restricted use of confidential information persist beyond the termination or expiration of any agreement."]
        }


Helpful answer:

"""


#For first document to be compared we take NDA1, during for-loops this will be updated with output of LLM (so content of all documents analysed that far in the loop)
master_entire_docs = sections_and_clauses_doc['NDA1'].copy()
sections_without_nda1_1 = {key : value for key, value in sections_and_clauses_doc.items() if key != 'NDA1'} #sections of NDA1 were used to create example list of sections


#DOCUMENTATION ALERT: count of entire document runs
count_entire_doc_runs = 0


for file_name, sectins_and_clauses in sections_without_nda1_1.items(): #Iterate over all documents except the first one
    count_entire_doc_runs += 1
    data_two_docs = f"""
    First document: {master_entire_docs}
    Second document: {sectins_and_clauses}
    """
    
    completion_master_entire_docs = client.chat.completions.create(
        model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
        messages=[
            {
                "role": "system",
                "content": json_instruction,
                },
            {
                "role": "system",
                "content": message_comp_entire_docs,
                },

            {
                "role": "user",
                "content": data_two_docs,
                }
            ],
        response_format={"type": "json_object"},
        )
    output = json.loads(completion_master_entire_docs.choices[0].message.content)
    master_entire_docs = output
    print(f"Output after {file_name}: \n {output} \n")




################                      COUNTING SECTIOS AND CLAUSES
############################################################################################################

# Numbering clauses in the Master list
for key, value_list in master_entire_docs.items():
    master_entire_docs[key] = [f"{i+1}. {item}" for i, item in enumerate(value_list)]


# New dictionary to store counts of clauses
clauses_count_entire_doc = {}
for key, value in master_entire_docs.items():
    clauses_count_entire_doc[key] = [{"clause": clause, "count": 0} for clause in value]


counting_system_message = """
You are a helpful assistant tasked to analyze a document to determine the presence of each clause from a provided list.
You will receive two pieces of information: an entire document to be analyzed, and a list of clauses that address the same topic. Although all the clauses address the same topic, it is possible that some of them are located within other sections of the document. Therefore, it is essential to examine the entire document for the presence of each clause.
The wording of clauses may vary between the document and the list; therefore, it is crucial to focus the analysis on the core meaning, intent, and nuances of each clause. Specifics like names, dates, or locations are not important, only the core meaning and intent of each clause matter.

Detailed Instructions:
    1. Check Clause Presence: Thoroughly examine each clause. Assess whether the document, even with differing wording, covers the intent or content of each clause.
    2. Return Boolean Values: For each clause, return 'true' if the clause's content or intent is found in the document, and 'false' if it is not.
    3. Output Format: Maintain the original order and wording of the clauses. Construct output as a JSON object, pairing each clause with a Boolean value indicating its presence. For every clause, only add Boolean value; all other text should remain unchanged. See example output below for reference.

Example of output format:

    "Part of document to analyze: "This agreement ensures that all materials related to the project must be returned or securely destroyed within 30 days following the termination of the project. A penalty will be imposed if this requirement is not met."

    "Dictionary of clauses": 
    { "Return of materials": [
            "1. Upon termination of the agreement, all materials must be returned or destroyed.",
            "2. The agreement specifies a time frame within which all documents must be returned or destroyed.",
            "3. The party responsible for the destruction must provide written proof of completion."
        ]}

    Output:
    { "Return of materials": [
        {"clause": "1. Upon termination of the agreement, all materials must be returned or destroyed.", "present" : True},
        {"clause": "2. The agreement specifies a time frame within which all documents must be returned or destroyed.", "present" : True},
        {"clause": "3. The party responsible for the destruction must provide written proof of completion.", "present" : False}
    ]}"

Helpful answer:
"""



for document in file_paths:
    document_text = preprocess_text(read_document(document))
    print(f"Document: {os.path.splitext(os.path.basename(document))[0]} \n")
    for topic, clauses in master_entire_docs.items():
        print(f"Topic: {topic}")
        example_data_count = f"""
        Document to analyze: {document_text}

        Section title: {topic}
        Clauses to analyze: {clauses}
        """
        #While-loop ensures that all clauses have Boolen value
        while True:
            completion_count = client.chat.completions.create(
                model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
                messages=[
                    {
                        "role": "system",
                        "content": json_instruction,
                        },
                    {
                        "role": "system",
                        "content": counting_system_message,
                        },

                    {
                        "role": "user",
                        "content": example_data_count,
                    }
                    ],
                response_format={"type": "json_object"},
                )
            output = json.loads(completion_count.choices[0].message.content)

            output_key = next(iter(output))
            if len(clauses) == len(output[output_key]): #If all clauses have Boolean value, break the loop
                comparison_results = []
                if output_key in output and topic in clauses_count_entire_doc:
                    for i, (item1, item2) in enumerate(zip(output[output_key], clauses_count_entire_doc[topic]), start=1):
                        if item1['clause'] == item2['clause']:
                            comparison_results.append(f"Clause {i}: Identical")
                        else:
                            comparison_results.append(f"Clause {i}: Not")
                            print(f"Not identical clauses: '{item1['clause']}' and '{item2['clause']}' \n")
                        if item1.get('present') == True:
                            item2['count'] += 1
                else:
                    print(f"Problem with keys '{output_key}' and '{topic}' in output and clauses_count. Nothing done. \n")
                print(f"Comparison results: {comparison_results} \n")

                break



for key, value in clauses_count_entire_doc.items():
    print(f"Topic: {key}")
    for item in value:
        print(f"{item['clause']} - {item['count']} \n")






#### Importing end result dictionaries for analysis

#### Importing dictionaries for further tasks

folder_path = 'T_GPT3.5'
os.makedirs(folder_path, exist_ok=True)

with open(os.path.join(folder_path, 'master_entire_docs.json'), 'w') as f:
    json.dump(master_entire_docs, f)

with open(os.path.join(folder_path, 'clauses_count_entire_doc.json'), 'w') as f:
    json.dump(clauses_count_entire_doc, f)

# Think about output style!

with open(os.path.join(folder_path, '11_Entire_Entire.txt'), 'w') as f:
    for key, value in clauses_count_entire_doc.items():
        f.write(f"Topic: {key} \n\n")
        for item in value:
            f.write(f"{item['clause']} - {item['count']} \n")
        f.write("\n")


with open(os.path.join(folder_path, 'Execution_counter.txt'), 'a') as f:
    f.write(f"11_Entire Entire \n")
    f.write("\n")
    f.write(f"To summarize entire entire (comparing entire documents at a time), it took: {count_entire_doc_runs} runs.\n")
    f.write("\n")
    f.write("\n")
    f.write("\n")

