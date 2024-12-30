import os
import json

from TOOL_IMPLEMENTATION.client_set_and_file_prep import create_client, read_document, split_into_sections, preprocess_text
client = create_client()


################                         Read, split and preprocess the NDAs
############################################################################################################

#Change from test to final directory: "/Users/koshevv1/Python/NDAs"
directory = "/Users/koshevv1/Python/NDAs"

file_paths = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.txt')]

# Extract the names of the files without the extension
nda_names = [os.path.splitext(os.path.basename(file))[0] for file in file_paths]

#A dict to store sections of documents, structured as {"file name": ['section 1', 'section 2', ...], ...}
nda_dict2 = {}

#Divide each document into sections and preprocess the text, add to nda_dict
for i, name in enumerate(nda_names):
    nda_dict2[name] = [preprocess_text(section) for section in split_into_sections(read_document(file_paths[i]))]


## DOCUMENTATION ALERT: number of sections in each document
print("Number of sections in each document:")
for key, value in nda_dict2.items():
    print(f"{key}: {len(value)}")





################                         Section summarization
############################################################################################################


# Instruction for LLM to output JSON
json_instruction = "You are a helpful assistant designed to output JSON."


# Summarization instruction for LLM
system_message_section_summarization = """
You are a helpful assistant tasked with summarizing main clauses of a document section. 
From a document section provided to you, extract and define its main topic and then list its clauses or provisions. Summarize these key elements, ensuring clarity and conciseness.

Instructions:
    Identify the Main Topic: Clearly state the overall topic of the section.
    Summarize Key Clauses: Break down the section into its main clauses or provisions. Summarize these clauses clearly and concisely.
    Organize Information: Present each clause as a separate item within an array. This format should maintain clarity and organization.

Output Format:
    Provide the output in a JSON format, with the topic name as a key and an array of summarized clauses as the value.
    
Example 1:
    Review Section: "2. Definitions.  “Confidential  Information”   means  any  of  Discloser’s  (or  its  Affiliates’)  information,
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
    joint venture, trust, estate, governmental agency or other entity of whatsoever kind or nature."

    Output: 
    {"Definitions" : ["'Confidential information' includes a broad array of information types valuable due to its secrecy.", "All confidential information disclosed in tangible form must be marked as “confidential” or “proprietary”.", "All confidential information disclosed orally must be summarized in writing within X days of disclosure.", "Definition of 'Affiliate'.", "Explanation of 'Control'.", "Definition of 'Person'."]}

Example 2:
    Review Section: "3. Exceptions.  Confidential Information does not include information which: (i)  is  in  the  possession  of  the
    Recipient at the time of disclosure as shown by the Recipient’s files and records immediately prior to the
    time  of  disclosure;  (ii)  prior  or  after  the  time  of  disclosure  becomes  part  of  the  public  knowledge  or
    literature, not as a result of any inaction or action of the Recipient; (iii) is lawfully obtained from a third
    party without any breach of a confidentiality obligation to the Discloser; (iv) is approved for release by the
    Discloser in writing; or (v) is shown by written record to be developed independently by the Recipient."

    Output:
    {"Exceptions" : ["(i) information is in the possession of the Recipient at the time of disclosure, as can be demonstrated by files.", "(ii) information was or becomes part of the public knowledge through no fault of the Recipient.", "(iii) is lawfully obtained from a third party without any breach of a confidentiality obligation.", "(iv) is approved for release by the Discloser in writing.", "(v) is shown by written record to be developed independently by the Recipient."]}

Example 3:
    Review Section: "5. Mandatory  Disclosure.   In  the  event  that  Recipient  or  its  respective  directors,  officers,  employees,
    consultants  or  agents  are  requested  or  required  by  legal  process  to  disclose  any  of  Discloser’s
    Confidential Information, Recipient shall give prompt written notice (to the extent legally permissible) so
    that Discloser may seek a protective order or other appropriate relief. In the event that such protective
    order  is  not  obtained,  Recipient  shall  disclose  only  that  portion  of  the  Confidential  Information  that  its
    counsel advises that it is legally required to disclose."

    Output:
    {"Mandatory disclosure" : ["Procedures if Recipient is legally required to disclose Confidential Information.", "Recipient is required to give prompt written notice to Discloser so that Discloser may seek a protective order.", "If protective order is not obtained, Recipient shall disclose only the part that is legally required to be disclosed."]}


Helpful answer:
"""



# Function to summarize a section
def summarize_sections(section):
    # Giving LLM a section
    example_data = f"""
    Document section to analyse: {section}
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
                "content": system_message_section_summarization,
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


# Generalization instruction for LLM
system_message_generalization = """
You are a helpful assistant tasked with generalizing specific names, dates, and other particulars of a document section into generalized terms.
You will be given a summarized section of a document. Generalize any specific details within the section to ensure broad applicability of a summary content to other similar sections. 

Generalize specifics:
    Replace specific company names with generic terms like "the company", "Discloser" and "Recipient" as contextually appropriate. Discloser is a party disclosing information, and Recipient is a party receiving information.
    Substitute exact time frames (e.g., "30 days") with more ambiguous phrases such as "in number of days", "for a specified period" or "within a designated timeframe.", whichever is contextually appropriate.
    Convert specific geographic locations into broader terms such as "the region" or "the specified state". 
    The goal is to create a version of the summary that abstracts specific details while retaining the essential information and context.

Preserve an output format given to you:
    Ensure the output is formatted with the topic name as a key and an array of generalized clauses as the value. Each clause should be a separate item within the array.

Helpful answer:
"""


# Function to generalize a section
def generalize_sections(section):
    # Giving LLM a section
    example_data = f"""
    Document section to generalize: {section}
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
                "content": system_message_generalization,
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
sections_and_clauses = {}

#DOCUMENTATION ALERT: count of summarization runs
count_of_summarization_runs = 0

# Loop through every section of every files, extracting topic and clauses from each section
for file_name, sections in nda_dict2.items():
    current = {}
    for section in sections:
        count_of_summarization_runs += 1
        section_summary = summarize_sections(section)
        generalized_section = generalize_sections(section_summary)
        current.update(generalized_section)
    sections_and_clauses[file_name] = current
    print(f"Finished processing {file_name}")
    print(f"New sections added: {current}")




################                         Refining Miscellaneous Part


# Instruction for LLM to divide Miscellaneous section into separate topics
system_message_miscellaneous = """
You are a helpful assistant tasked with categorizing 'Miscellaneous' section of a Non-Disclosure Agreement (NDA) into distinct topics.
Analyze the provided "Miscellaneous" section of a NDA and categorize its content into distinct topics. 
Examples of potential topics include, but are not limited to: Entire Agreement, No Waiver, Amendments, Injunctive Relief, Assignment, Notice, No obligation, Severability, Export compliance, Limitation of liability. There may be other topics within the text, so if you identify any additional topics, include these as well.
For each topic, extract and list the specific clauses or statements that fall under that topic. Note that each topic may have one or more clauses associated with it.

Expected Output: 
    Provide a JSON object where each key represents a topic and each value is a list of clauses or statements related to that topic extracted from the 'Miscellaneous' section. The format should be as follows:
    {
        "Topic 1": ["Clause 1", "Clause 2", ...],
        "Topic 2": ["Clause 1", "Clause 2", ...],
        ...
    }

Helpful answer:
"""


for file_name, inner_dict in sections_and_clauses.items():
    if 'Miscellaneous' in inner_dict:
        print(f"Outer Key: {file_name}")
        
        miscellaneous_part = inner_dict['Miscellaneous']
        miscellaneous_part_str = ' '.join(miscellaneous_part)

        miscellaneous_completion = client.chat.completions.create(
            model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
            messages=[
                {
                    "role": "system",
                    "content": json_instruction,
                    },
                {   
                    "role": "system",
                    "content": system_message_miscellaneous,
                    },
                {
                    "role": "user",
                    "content": miscellaneous_part_str,
            }
            ],
        response_format={"type": "json_object"},
        )
        output = json.loads(miscellaneous_completion.choices[0].message.content)
        print(f"Output for {file_name}: {output} \n")

        # Delete 'Miscellaneous' key from inner_dict
        del inner_dict['Miscellaneous']

        # Add output as new keys and values to inner_dict
        inner_dict.update(output)



#### Importing dictionaries for further tasks

folder_path = 'T_GPT3.5'
os.makedirs(folder_path, exist_ok=True)


with open(os.path.join(folder_path, 'nda_dict2.json'), 'w') as f:
    json.dump(nda_dict2, f)

with open(os.path.join(folder_path, 'sections_and_clauses.json'), 'w') as f:
    json.dump(sections_and_clauses, f)


#### Importing end result dictionaries for analysation

with open(os.path.join(folder_path, '2_Section_Summary.txt'), 'w') as f:
    for file_name, content in sections_and_clauses.items():
        f.write(f"File: {file_name}\n\n")
        for section, clauses in content.items():
            f.write(f"Section: {section}\n")
            for clause in clauses:
                f.write(f"{clause}\n")
            f.write("\n")  # Add an extra newline after each section


with open(os.path.join(folder_path, 'Execution_counter.txt'), 'a') as f:
    f.write(f"Summarization by sections (2_section_summary) \n")
    f.write("Number of sections in each document: \n")
    for key, value in nda_dict2.items():
        f.write(f"{key}: {len(value)} \n")
    f.write("\n")
    f.write(f"To summarize documents by sections (2_section_summary), it took: {count_of_summarization_runs} runs.\n")
    f.write("\n")
    f.write("\n")
    f.write("\n")

