import os
import json

from TOOL_IMPLEMENTATION.client_set_and_file_prep import create_client, read_document, preprocess_text
client = create_client()



################                         Read and preprocess the NDAs
############################################################################################################

#Change from test to final directory: "/Users/koshevv1/Python/NDAs"
directory = "/Users/koshevv1/Python/NDAs"

file_paths = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.txt')]

# Extract the names of the files without the extension
nda_names = [os.path.splitext(os.path.basename(file))[0] for file in file_paths]

#A dict to store documents, structured as {"file name": "entire content of a file", ...}
nda_dict1 = {}

#Preprocess each file, add to nda_dict
for i, name in enumerate(nda_names):
    nda_dict1[name] = [preprocess_text(read_document(file_paths[i]))]




################                         Document summarization
############################################################################################################


# Instruction for LLM to output JSON
json_instruction = "You are a helpful assistant designed to output JSON."


# Summarization instruction for LLM
system_message_document_summarization = """
You are a helpful assistant tasked with summarizing all main clauses for every section of a document. 
From a document provided to you, extract and define main sections present and then list clauses or provisions for each section. Summarize these key elements, ensuring clarity and conciseness.

Instructions:
    Identify the Main Topic: Clearly state the overall topics or sections present in the document.
    Summarize Key Clauses: Break down each section into its main clauses or provisions. Provide clear and concise summary of every clause within a section.
    Organize Information: Format the output as JSON, with each topic name as a key and an array of clauses as the associated value. Each clause should be a separate item within the array.

Output Format:
    {
        "Section Name": ["Summary of Clause 1", "Summary of Clause 2", ...],
        "Section Name": ["Summary of Clause 1", "Summary of Clause 2", ...],
        ...
    }
    
Example (part of a document):
    Review Document: "2. Definitions.  “Confidential  Information”   means  any  of  Discloser’s  (or  its  Affiliates’)  information,
    including,  without  limitation,  science,  formulas,  patterns,  compilations,  programs,  software,  devices,
    designs,  drawings,  methods,  techniques  and  processes,  financial  information  and  data,  business  plans,
    business  strategies,  marketing  plans,  customer  lists,  price  lists,  cost  information,  information  about
    employees,  descriptions  of  inventions,  process  descriptions,  descriptions  of  technical  know-how,
    information  and  descriptions  of  new  products  and  new  product  development,  scientific  and  technical
    specifications and documentation, and pending or abandoned patent applications of a party, now known or
    in possession of, or hereafter learned or acquired, that derives economic value, actual or potential, from
    not being generally known to, and not being readily ascertainable by proper means by other persons who
    can  obtain  economic  value  from  its  disclosure  or  use.  All  Confidential  Information  disclosed  in  tangible
    form  must  be  marked  as  “confidential”  or  “proprietary”  or  with  words  of  similar  import,  and  all
    Confidential Information disclosed orally must be identified as confidential at the time  of  disclosure  and
    summarized in writing within thirty (30) days of disclosure.  “Affiliate”,  with respect to any Person, means
    any other Person that, directly or indirectly, is controlled by, controls or is under common control with that
    Person,  including,  without  limitation,  any  officer,  director,  manager,  general  partner,  controlling
    stockholder or managing member of any Person.  “Control”,  with respect to any Person, means the power,
    directly  or  indirectly,  to  direct  the  management  and  policies  of  that  Person.  “Person”  shall  be  broadly
    interpreted  to  include,  without  limitation,  any  individual,  corporation,  company,  association,  partnership,
    joint venture, trust, estate, governmental agency or other entity of whatsoever kind or nature.
    3. Exceptions.  Confidential Information does not include information which: (i)  is  in  the  possession  of  the
    Recipient at the time of disclosure as shown by the Recipient’s files and records immediately prior to the
    time  of  disclosure;  (ii)  prior  or  after  the  time  of  disclosure  becomes  part  of  the  public  knowledge  or
    literature, not as a result of any inaction or action of the Recipient; (iii) is lawfully obtained from a third
    party without any breach of a confidentiality obligation to the Discloser; (iv) is approved for release by the
    Discloser in writing; or (v) is shown by written record to be developed independently by the Recipient.
    5. Mandatory  Disclosure.   In  the  event  that  Recipient  or  its  respective  directors,  officers,  employees,
    consultants  or  agents  are  requested  or  required  by  legal  process  to  disclose  any  of  Discloser’s
    Confidential Information, Recipient shall give prompt written notice (to the extent legally permissible) so
    that Discloser may seek a protective order or other appropriate relief. In the event that such protective
    order  is  not  obtained,  Recipient  shall  disclose  only  that  portion  of  the  Confidential  Information  that  its
    counsel advises that it is legally required to disclose."

    Output:
    {
        "Definitions" : ["'Confidential information' includes a broad array of information types valuable due to its secrecy.", "All confidential information disclosed in tangible form must be marked as “confidential” or “proprietary”.", "All confidential information disclosed orally must be summarized in writing within X days of disclosure.", "Definition of 'Affiliate'.", "Explanation of 'Control'.", "Definition of 'Person'."],
        "Exceptions" : ["(i) information is in the possession of the Recipient at the time of disclosure, as can be demonstrated by files.", "(ii) information was or becomes part of the public knowledge through no fault of the Recipient.", "(iii) is lawfully obtained from a third party without any breach of a confidentiality obligation.", "(iv) is approved for release by the Discloser in writing.", "(v) is shown by written record to be developed independently by the Recipient."],
        "Mandatory disclosure" : ["Procedures if Recipient is legally required to disclose Confidential Information.", "Recipient is required to give prompt written notice to Discloser so that Discloser may seek a protective order.", "If protective order is not obtained, Recipient shall disclose only the part that is legally required to be disclosed."]
    }

Helpful answer:
"""



# Function to summarize a document
def summarize_document(doc):
    # Giving LLM a document
    example_data = f"""
    Document to analyse: {doc}
    """
    completion = client.chat.completions.create(
        model= "no_effect", # the model variable must be set, but has no effect, model selection done with URL
        messages=[
            {
                "role": "system",
                "content": json_instruction,
                },
            {
                "role": "system",
                "content": system_message_document_summarization,
                },

            {
                "role": "user",
                "content": example_data,
                }
            ],
        response_format={"type": "json_object"},
        )
    output = json.loads(completion.choices[0].message.content)  # Extract the JSON output
    return output




system_message_generalization_doc = """
You are a helpful assistant tasked with generalizing specific names, dates, and other particulars of a document into generalized terms.
You will be given a summarized document. Generalize any specific details within the document to ensure broad applicability of a summary content to other similar documents. 

Generalize specifics:
    Replace specific company names with generic terms like "the company", "Discloser" and "Recipient" as contextually appropriate. Discloser is a party disclosing information, and Recipient is a party receiving information.
    Substitute exact time frames (e.g., "30 days") with more ambiguous phrases such as "in number of days", "for a specified period" or "within a designated timeframe.", whichever is contextually appropriate.
    Convert specific geographic locations into broader terms such as "the region" or "the specified state". 
    The goal is to create a version of the summary that abstracts specific details while retaining the essential information and context.

Preserve an output format given to you:
    Ensure the output is formatted with the topic names as keys and an array of generalized clauses as the associated values. Each clause should be a separate item within the array.

    Output Format:
    {
        "Section Name": ["Summary of Clause 1", "Summary of Clause 2", ...],
        "Section Name": ["Summary of Clause 1", "Summary of Clause 2", ...],
        ...
    }

Helpful answer:
"""


# Function to generalize a section
def generalize_document(document):
    # Giving LLM a document
    example_data = f"""
    Document to generalize: {document}
    """
    completion = client.chat.completions.create(
        model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
        messages=[
            {
                "role": "system",
                "content": json_instruction,
                },
            {
                "role": "system",
                "content": system_message_generalization_doc,
                },

            {
                "role": "user",
                "content": example_data,
                }
            ],
        response_format={"type": "json_object"},
        )
    output = json.loads(completion.choices[0].message.content)  # Extract the JSON output
    return output



# A dictionary to store clauses of each section of each document, structured as {"file name": {'Main section': ['First clause', 'Second clause', etc.]}, ...}
sections_and_clauses_doc = {}

#DOCUMENTATION ALERT: count of summarization runs
count_of_summarization_runs_doc = 0

# Loop through every section of every files, extracting topic and clauses from each section
for file_name, content in nda_dict1.items():
    count_of_summarization_runs_doc += 1
    doc_summary = summarize_document(content)
    generalized_doc = generalize_document(doc_summary)
    sections_and_clauses_doc[file_name] = generalized_doc
    print(f"Finished processing {file_name}")
    print(f"Summary: {generalized_doc}")



#### Importing dictionaries for further tasks

folder_path = 'T_GPT3.5'
os.makedirs(folder_path, exist_ok=True)

with open(os.path.join(folder_path, 'file_paths.json'), 'w') as f:
    json.dump(file_paths, f)

with open(os.path.join(folder_path,'nda_dict1.json'), 'w') as f:
    json.dump(nda_dict1, f)

with open(os.path.join(folder_path, 'sections_and_clauses_doc.json'), 'w') as f:
    json.dump(sections_and_clauses_doc, f)


#### Importing end result dictionaries for analysation


with open(os.path.join(folder_path, '1_Entire_Summary.txt'), 'w') as f:
    for file_name, content in sections_and_clauses_doc.items():
        f.write(f"File: {file_name}\n\n")
        for section, clauses in content.items():
            f.write(f"Section: {section}\n")
            for clause in clauses:
                f.write(f"{clause}\n")
            f.write("\n")  # Add an extra newline after each section


with open(os.path.join(folder_path, 'Execution_counter.txt'), 'w') as f:
    f.write("The file consists of run counts for different tasks.\n")
    f.write(f"To summarize entire document (1_Entire_Summary), it took: {count_of_summarization_runs_doc} runs.\n")
    f.write("\n")
    f.write("\n")
    f.write("\n")




############################################################################################################
#If not produced in sections


new = {}
for content in nda_dict1['NDAX']:
    doc_summary = summarize_document(content)
    generalized_doc = generalize_document(doc_summary)
    new = generalized_doc
    print(f"Finished processing {file_name}")
    print(f"Summary: {generalized_doc}")



for file_name, content in new.items():
    print(f"Section: {file_name}\n")
    for clause in content:
        print(f"{clause}")
    print("\n")  # Add an extra newline after each section
    

sections_and_clauses_doc['NDAX'] = new




