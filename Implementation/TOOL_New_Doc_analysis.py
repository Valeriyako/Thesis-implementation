import os
import json

from TOOL_IMPLEMENTATION.client_set_and_file_prep import create_client, read_document, preprocess_text, split_into_sections
client = create_client()


with open('/Users/koshevv1/Python/Taydellinen_master.json', 'r') as f:
    taydellinen_master = json.load(f)

##################################        New Document Analysis   ##################################################
####################################################################################################################

new_document = preprocess_text(read_document("T_New_Doc/Missing_set_3.txt")) # Read and preprocess a document


##################################        Missing sections and clauses

presence_of_clauses = {}
for key, value in taydellinen_master.items():
    presence_of_clauses[key] = [{"clause": clause, "presence": False} for clause in value]




json_instruction = "You are a helpful assistant designed to output JSON."

presence_system_message = """
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



for topic, clauses in taydellinen_master.items():
    print(f"Topic: {topic}")
    example_data = f"""
        Document to analyze: {new_document}

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
                    "content": presence_system_message,
                    },
                {
                    "role": "user",
                    "content": example_data,
                    }    
                ],
            response_format={"type": "json_object"},
            )
        output = json.loads(completion_count.choices[0].message.content)

        output_key = next(iter(output))
        if len(clauses) == len(output[output_key]): #If all clauses have Boolean value, break the loop
            comparison_results = []
            if output_key in output and topic in presence_of_clauses:
                for i, (item1, item2) in enumerate(zip(output[output_key], presence_of_clauses[topic]), start=1):
                    if item1['clause'] == item2['clause']:
                        comparison_results.append(f"Clause {i}: Identical")
                    else:
                        comparison_results.append(f"Clause {i}: Not")
                        print(f"Not identical clauses: '{item1['clause']}' and '{item2['clause']}' \n")
                    if item1.get('present') == True:
                        item2['presence'] = True
            else:
                print(f"Problem with keys '{output_key}' and '{topic}' in output and presence_of_clauses. Nothing done. \n")
            print(f"Comparison results: {comparison_results} \n")

            break


for key, value in presence_of_clauses.items():
    print(f"\n Topic: {key} \n")
    for item in value:
        print(f"{item['clause']} - {item['presence']}")


missing_sections = []
missing_clauses = {}

for key, value in presence_of_clauses.items():
    number_of_clauses = len(value)
    not_present = 0
    for item in value:
        if item['presence'] == False:
            not_present += 1
            if key in missing_clauses.keys():
                missing_clauses[key].append(item['clause'])
            else:
                missing_clauses[key] = [item['clause']]
    if not_present/number_of_clauses >= 0.5:
        print(f"Topic '{key}' is missing more than 50% of clauses.")
        missing_sections.append(key)

for key, value in missing_clauses.items():
    print(f"Topic '{key}' is missing clauses:")
    for item in value:
        print(f"Clause: {item}")
    print("\n")


#################           Sections and clauses that should not be there

sections_of_new_document = []
sections_of_new_document.append([preprocess_text(section) for section in split_into_sections(read_document("/Users/koshevv1/Python/T_New_Doc/Extra_set_3.txt"))])
sections_of_new_document = [item for sublist in sections_of_new_document for item in sublist]

len(sections_of_new_document)


uncommon_system_message = """
You are a helpful assistant tasked to identify and flag uncommon sections and clauses within a new document, compared to a predefined list of common sections.
You will receive two pieces of information: a list of common sections and their clauses typically found in NDAs, and a document section of NDA to analyse. Your task is to analyze that section of a new document, compare it against the provided list of common sections, and flag any section or clauses within that section that are uncommon or not included in the list.
The wording of clauses may vary between the document and the list; therefore, it is crucial to focus the analysis on the core meaning, intent, and nuances of each clause. Specifics like names, dates, or locations are not important, only the core meaning and intent of each clause matter.

Detailed Instructions:
    1. Understand the Common Sections: Start by reviewing the list of common sections. This list serves as your reference for what is typically expected in NDAs.
    2. Analyze the New Section: Read the section from the new document provided to you. Understand its content, focus, and any specific clauses it contains.
    3. Comprehensive Section Comparison: Examine both the title and the main content of the section from the new document. Compare these with the titles and typical content of sections in the provided list. If neither the title nor a significant portion of the content closely matches any of the common sections, flag this as an uncommon section.
    4. Individual Clause Comparison: Even if the section title matches, examine the content and specific clauses within the section. Utilize semantic understanding and pay attention to context and purpose of clauses rather than literal wording. Do not over-flag clauses! Only if clause is different by more than 50% from common clauses, flag it as uncommon.
    5. Flagging uncommon content:
        - Uncommon Section: If the section and most of its content is not found in the list, describe it as 'Uncommon Section'.
        - Uncommon Clauses: Within a section that matches, identify and describe any clauses that are not part of the common setup.


Output Format:
    - If the section is uncommon, output format is: { "uncommon_section" : ["section_title": "Title of Uncommon Section", "section_content": "Full text or summary of the section's content"]}
    - If the section is common, but contains uncommon clauses, output format is: { "common_section" : ["section_title": "Title of Common Section", "uncommon_clauses": ["clause1", "clause2", ...]]}
    - If no uncommon sections or clauses are found, output format is: { "common_document" : []}


Examples:

    List of Common Sections:
        {Return of materials: ["Upon termination of the agreement, all materials must be returned or destroyed.", "The agreement specifies a time frame within which all documents must be returned or destroyed.", "The party responsible for the destruction must provide written proof of completed destruction."]}
        {Termination: ["Agreement is effective from the Effective Date and formally ends X years thereafter.", "Earlier termination is possible if communicated in writing.", "Some sections have specific expiration terms.", "Obligations for non-disclosure and restricted use of confidential information persist beyond the termination or expiration of any agreement."]}"


    Example 1:
        New section: "4. Insurance: The Tenant shall, at its own expense, maintain during the term of this Lease, comprehensive general liability insurance with coverage limits of not less than $1,000,000 per occurrence and $2,000,000 in aggregate, naming the Landlord as an additional insured."
        Output: { 
            "uncommon_section" : {
                "section_title": "Insurance", 
                "section_content": "The Tenant shall, at its own expense, maintain during the term of this Lease, comprehensive general liability insurance with coverage limits of not less than $1,000,000 per occurrence and $2,000,000 in aggregate, naming the Landlord as an additional insured."
                }

    Example 2:
        New section: "3. Return of confidential information: Upon termination of the agreement, all confidential information must be returned or destroyed. The information must be returned within 30 days following the termination of the agreement. The Receiving Party shall ensure that all physical copies of the Confidential Information are wrapped in biodegradable bubble wrap."
        Output: { 
            "common_section" : {
                "section_title": "Return of materials", 
                "uncommon_clauses": ["The Receiving Party shall ensure that all physical copies of the Confidential Information are wrapped in biodegradable bubble wrap."]
                }

    Example 3:
        New section: "Termination: The agreement becomes effective on the Effective Date and formally concludes five years later. Early termination is allowed if communicated in writing. Obligations for non-disclosure continues beyond the termination or expiration of this agreement."
        Output: { 
            "common_document" : []
            }

Helpful answer:
"""


uncommon_sections = {}
uncommon_clauses = {}

flattened_master = {key: ' '.join(value) for key, value in taydellinen_master.items()}


last_five_items_dict = sections_of_new_document[-2:]

for section in sections_of_new_document:
    print(f"Section: {section}")
    
    example_data = f"""
        A list of common sections and their corresponding clauses: {flattened_master}

        Section of a new document to be analysed: {section}
        """
    
    completion_uncommon = client.chat.completions.create(
        model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
        messages=[
            {
                "role": "system",
                "content": json_instruction,
                },
            {
                "role": "system",
                "content": uncommon_system_message,
                },
            {
                "role": "user",
                "content": example_data,
                }    
            ],
        response_format={"type": "json_object"},
        )
    output = json.loads(completion_uncommon.choices[0].message.content)
    

    print(f"Output: {output} \n")

    section_type = next(iter(output))
    if section_type == "uncommon_section":
        uncommon_sections[output[section_type]['section_title']] = output[section_type]['section_content']
        print(f"Section '{output[section_type]['section_title']}' is uncommon among NDAs. \n \n")
    elif section_type == "common_section":
        if output[section_type]['uncommon_clauses'] == []:
            print(f"Section '{output[section_type]['section_title']}' has only standard clauses. \n \n")
        else:
            uncommon_clauses[output[section_type]['section_title']] = output[section_type]['uncommon_clauses']
            print(f"Section '{output[section_type]['section_title']}' is common among NDAs, but contains uncommon clauses. \n \n")
    elif section_type == "common_document":
        print(f"Section is common among NDAs and does not contain uncommon clauses. \n \n")






