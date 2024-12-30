#
# Copyright (C) Valeriya Koshevaya
#
# SPDX-License-Identifier: MIT
#



import os
import json

from Imp_0_File_prep import create_client, read_document, preprocess_text
client = create_client()


with open('T_GPT4/sections_and_clauses.json', 'r') as f:
    sections_and_clauses = json.load(f)

with open('T_GPT4/file_paths.json', 'r') as f:
    file_paths = json.load(f)

##################################             MASTER LISTS    ##################################################
#################################################################################################################

# Instruction for LLM to output JSON
json_instruction = "You are a helpful assistant designed to output JSON."


###########                         Creating list of similar sections
############################################################################################################


example_sections2 = sections_and_clauses['NDA1'].copy() #This will contain example of each separate section
dict_of_sections2 = {key : [{'topic' : key, 'source': 'NDA1'}] for key in sections_and_clauses['NDA1'].keys()} #This dict is a list of similar sections, with source NDA for each section title (that will be merged later)
    

system_message_section_similarities = """  
You are a helpful assistant tasked with analyzing the summarized content of a section from an NDA document to determine its similarity to existing sections from a reference list. 
Focus on the actual content and intent of clauses when evaluating similarity of sections. Even if the specific clauses are not identical, but as long as they discuss the same topic, they should be grouped together under the same category.

Requirements:
    1. Assess the semantic content and underlying intent of the sections to ensure that the new section aligns closely with any existing sections in terms of meaning and intent.
    2. If none of the existing sections is sufficiently similar, flag the new section as a potential new category.
    3. If the new section expands significantly on the content of an existing section by adding more details about the same topic, it should still remain categorized under that existing section. However, if the new section introduces multiple topics that are different from those in the existing section, it should be categorized as a new section.
    4. If the new section addresses only a small subset of the topics covered in a broader existing section, categorize it as a new section. Aim for detailed and specific categorization rather than broad 'umbrella' sections that cover multiple topics. For example, if the new section discusses 'entire agreement' but the existing section includes 'entire agreement', 'waiver', 'publicity', and other topics, categorize the new section as a new section.

    
Output structure:
    Generate the output in JSON format. If a sufficient similarity is found with an existing section, output the exact name of that section as listed in the reference; otherwise, output 'New section' if the analysed section was not similar enough with any existing sections.
    Output template: {"result": "Name of similar existing section" or "New section" }


Helpful result of comparison:

"""

sections_without_nda1_2 = {key : value for key, value in sections_and_clauses.items() if key != 'NDA1'} #sections of NDA1 were used to create example list of sections


#Actual comparison of sections
for file_name, file_content in sections_without_nda1_2.items():
    for section, clauses in file_content.items():
        
        example_data_sections = f""" 
        List of existing sections and their clauses: {example_sections2}

        Name of a new section: {section}
        Clauses of a new section to be analyzed: {clauses}
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
                    "content": system_message_section_similarities,
                    },
                {
                    "role": "user",
                    "content": example_data_sections,
                }
                ],
            response_format={"type": "json_object"},
            )
        output = json.loads(completion.choices[0].message.content)
        potential_section = next(iter(output.values()))
        print(f"Output for section '{section}': {potential_section} \n")

        if potential_section == "New section":
            if section in dict_of_sections2: #To avoid updating keys, check if section already exists in dict
                print(f"Title '{section}' was in dict, but added as a new section.")
                print(f"Added as \"{section} ({file_name})\" \n")
                dict_of_sections2[f"{section} ({file_name})"] = [{'topic' : section, 'source': file_name}] #Have to name key differently
                example_sections2[f"{section} ({file_name})"] = clauses
            else: #This is the normal case, that the section is completely new for dict
                dict_of_sections2[section] = [{'topic' : section, 'source': file_name}]
                example_sections2[section] = clauses
        elif potential_section in dict_of_sections2: #If the section is already in dict, append the new section to it as a collection of synonyms
            dict_of_sections2[potential_section].append({'topic': section, 'source': file_name})
        else:
            print(f"Something went wrong, section was {section} from file {file_name}, and output was {potential_section} \n")
            
# Check the reslult
for key, value in dict_of_sections2.items():
    print(f"{key}")
    for i in value:
        print(f"    {i}")



###########                         Removing dublicate clauses from sections
############################################################################################################


### Separating sections with one and multiple appearance in the documents
single_sections21 = {key: value for key, value in dict_of_sections2.items() if len(value) == 1}
sections_to_summarize21 = {key: value for key, value in dict_of_sections2.items() if len(value) > 1}



###########                         Title selection

message_master_title = """
You are a helpful assistant tasked to select the most appropriate title for a section of a Non Disclosure agreement (NDA). 
You will be provided with a list of titles that all describe a similar section of an NDA. Determine the best title based on the following criteria:
    1. Frequency: Identify the title that appears most frequently in the provided list, as frequency indicates common usage in NDAs. Ensure that the most frequently used wording is included in the final title choice.
    2. Descriptive Enhancement (optional): Consider whether integrating elements from other titles could result in a more descriptive and comprehensive title. Add relevant wording from other titles only if it enhances the title’s clarity and accurately reflects the content of the section. However, strive for a concise and clear title. If incorporating new words, ensure grammatical coherence by using commas, 'and', or other appropriate conjunctions to maintain fluency.

Output Format: {"Title": "Chosen best title for the section"}

Helpful answer:
"""


def master_title_selection(titles):
    completion_master_title = client.chat.completions.create(
        model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
        messages=[
            {
                "role": "system",
                "content": json_instruction,
                },
            {
                "role": "system",
                "content": message_master_title,
                },

            {
                "role": "user",
                "content": " ".join(titles),
                }
            ],
        response_format={"type": "json_object"},
        )
    output = json.loads(completion_master_title.choices[0].message.content)
    return list(output.values())[0]




###########                         Method 1: All sections at once



message_master_all_sec_at_once = """
You are a helpful assistant tasked to analyze, organize and streamline clauses from the same section of multiple Non-Disclosure Agreements (NDAs) into a single, structured and collectively exhaustive output.
You will be provided with a list of clauses from a specific section. It is crucial to ensure that each unique key point or meaning within these clauses is distinctly and clearly represented in the final list.

Detailed Instructions:
    1. Review and Compare: Conduct a detailed review of each provided clause. Identify similarities and differences across clauses, with particular focus on their content and intended purposes.
    2. Present each key point separately: List each clause as an independent item in the output. Do not merge clauses into a single lengthy sentence. 
    3. Avoid Repetition: Prevent redundancy by removing duplicate clause meanings. However, include variations of clauses that introduce different perspectives or additional details.
    4. Capture All Variants: While excluding exact duplicates, make sure to include all variants of clauses that convey different nuances or conditions. This ensures a comprehensive representation of the section’s intent across multiple documents.
    5. Ensure Comprehensiveness and Organization: Present each key point of clauses as a separate entry in a list. The final list must be comprehensive, capturing all essential information from the provided list without omitting any key points. Provide a section with a title that accurately reflects the content of the clauses.

Expected Output:
    { "Section title" : ["Clause 1", "Clause 2", "Clause 3", ...]}

Example 1:
    "Input: ["Upon termination of the agreement, all materials provided by the Company must be returned by the Recipient within 30 days.", "All confidential materials must be returned or destroyed at the end of the contract period.", "The party responsible for the destruction shall provide a written record evidencing the completion of such destruction.", "All materials provided by the Company must be returned by the Recipient within 30 days of contract termination."]
    Output: {Return of materials: ["Upon termination of the agreement, all materials must be returned or destroyed.", "The agreement specifies a time frame within which all documents must be returned or destroyed.", "The party responsible for the destruction must provide written proof of completed destruction."]}

Example 2:
    Input: ["This agreement applies to disclosures made from the Effective Date to one year after, or earlier if termination is communicated in writing.", "Rights and obligations detailed in Sections 5 and 6 have specific expiration terms as outlined in those sections.", "The agreement formally ends three years from the Effective Date, except for restricted use of information which extends beyond that period.", "The agreement shall commence on the effective date and continue for five years, unless earlier terminated in writing.", "The receiving Party's obligations for non-disclosure and restricted use of Confidential Information will persist beyond the termination or expiration of any Services Agreement."]
    Output: { Termination: ["Agreement is effective from the Effective Date and formally ends X years thereafter.", "Earlier termination is possible if communicated in writing.", "Some sections have specific expiration terms.", "Obligations for non-disclosure and restricted use of confidential information persist beyond the termination or expiration of any agreement."]}"

Helpful answer:

"""


# Dictionary for final Master List of all sections at once
master_all_at_once2 = {}

#DOCUMENTATION ALERT: count of sections processed at once
count_all_sections_at_once2 = 0


#Iterating over the sections that have multiple appearances (to make Master list of clauses)
for main_key, values in sections_to_summarize21.items(): 
    count_all_sections_at_once2 += 1
    clauses = [] #Will store clauses from all documents for a specific section
    topics = [] #storing synonyms of that section title used in different documents
    for value in values:
        source = value['source']
        topic = value['topic']
        topics.append(topic)
        if source in sections_and_clauses: #Use NDA file name to access its sections and clauses
            if topic in sections_and_clauses[source]: #Use topic to access its clauses
                clauses.append(sections_and_clauses[source][topic]) #Collect clauses to the list
            else:
                print(f"Topic '{topic}' not found in {source}")
        else:
            print(f"Source '{source}' not found in sections_and_clauses")
    clauses = [clause for sublist in clauses for clause in sublist] #Flatten the list for LLM input
    print(f"(If want to make checks) Main key: {main_key}. Clauses: {clauses} \n")

    section_title = master_title_selection(topics)
    print(f"Final title for {main_key} (including titles {topics}): {section_title} \n")

    if section_title in master_all_at_once2: #Error check, if master list already has this section title
        print(f"Error: Duplicate title '{section_title}' identified.")
        print("Will be used key '{section_title} ({main_key})' instead.")
        section_title = f"{section_title} ({main_key})"


    completion_master_all = client.chat.completions.create(
        model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
        messages=[
            {
                "role": "system",
                "content": json_instruction,
                },
            {
                "role": "system",
                "content": message_master_all_sec_at_once,
                },

            {
                "role": "user",
                "content": " ".join(clauses),
                }
            ],
        response_format={"type": "json_object"},
        )
    output = json.loads(completion_master_all.choices[0].message.content)

    identified_topics = [] #Error check that actually only one section is identified

    for key, value in output.items(): #Part of error check, calculating how many topics LLM produced
        identified_topics.append(key) 

    for key, value in output.items(): #Adding to master dict
        if len(identified_topics) == 1: #All good, only one section identified
            master_all_at_once2[section_title] = value
            print(f"Final output for {main_key}: \n {section_title}: {master_all_at_once2[section_title]} \n")
        else:
            print(f"Error: Multiple topics identified: {identified_topics} for {main_key}")
            print("Will be added separately as subsections.")
            master_all_at_once2[f"{section_title} ({key})"] = value
            print(f"One of {len(identified_topics)} outputs for {main_key}: \n {section_title} ({key}): {master_all_at_once2[f'{section_title} ({key})']} \n")
    


###########               Assessing similarity of previously single sections to new merged sections

unique_sections_all_2 = {} #Will be added to Master as is
sections_to_be_merged_all_2 = {} #Will be compared and possibly merged with existing sections

# Using system_message2 to determine similarities between new section and existing sections
#Checking each single section at a time
for key, values in single_sections21.items():
    for value in values:
        source = value['source']
        topic = value['topic']
        clauses = sections_and_clauses[source][topic]
        print(f"{key}. clauses: {clauses} \n")

        example_data_all = f""" 
        List of existing sections and their clauses: {master_all_at_once2} 

        Title of a new section: {topic}
        Clauses of a new section to analyse: {clauses}
        """

        completion_singles = client.chat.completions.create(
            model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
            messages=[
                {
                    "role": "system",
                    "content": json_instruction,
                    },
                {   
                    "role": "system",
                    "content": system_message_section_similarities,
                    },
                {
                    "role": "user",
                    "content": example_data_all,
                }
                ],
            response_format={"type": "json_object"},
            )
        output = json.loads(completion_singles.choices[0].message.content)
        potential_section = next(iter(output.values()))
        print(f"Output for section '{topic}': {potential_section} \n")

        if potential_section == "New section":
            print(f"The section {topic} is a unique section and can be added to the Master list as is.")
            print(f"Its content is: {clauses}")
            unique_sections_all_2[topic] = clauses
        else:
            print(f"The section {topic} is similar to {potential_section}.")
            print(f"Its clauses are: {clauses}")
            print(f"The existing section: {master_all_at_once2[potential_section]} \n \n")
            sections_to_be_merged_all_2[potential_section] = {'topic': topic, 'clauses': clauses}




################            Adding unique sections to Master list

# Making a copy of master just in case
master_all_at_once2_copy2 = master_all_at_once2.copy()

#Adding unique sections that are worth adding
for topic, clauses in unique_sections_all_2.items():
    print(f"{topic}: {clauses} \n")
    if topic in master_all_at_once2_copy2:
        print(f"Topic already exists!")


# Structure of code for adding
# master_all_at_once2_copy2['topic'] = unique_sections_all_2['topic']
master_all_at_once2_copy2['Right to Disclose'] = unique_sections_all_2['Right to Disclose']
master_all_at_once2_copy2['Legal Fees'] = unique_sections_all_2['Legal Fees']
master_all_at_once2_copy2['Interpretation'] = unique_sections_all_2['Interpretation']
master_all_at_once2_copy2['Preservation of Privileges'] = unique_sections_all_2['Preservation of Privileges']
master_all_at_once2_copy2['Export Compliance'] = unique_sections_all_2['Export Compliance']
master_all_at_once2_copy2['Background'] = unique_sections_all_2['Background']


################            Merging rest of the sections to Master list


for key, value in sections_to_be_merged_all_2.items():
    print(f"Section for potential merging: {value} \n")
    print(f"It can be merged with {key}: {master_all_at_once2[key]} \n")

#(In theory, these are keys of sections_to_be_merged, but since I don't want to merge all keys, I'm selecting the ones I want to update)
sections_to_update21 = ['Purpose of Disclosure and Scope of NDA']

for key in sections_to_update21:
    topic_to_update = sections_to_be_merged_all_2[key]['topic']
    clauses_to_update = sections_to_be_merged_all_2[key]['clauses']
    print(f"Updating '{key}' with the topic '{topic_to_update}' and clauses: {clauses_to_update}")
    print(f"Current content: {master_all_at_once2_copy2[key]} \n")

    text_to_update = f"""
    First set of clauses: {master_all_at_once2_copy2[key]}
    Second set of clauses: {clauses_to_update}
    """

    completion_master_inparts = client.chat.completions.create(
            model="no_effect", # the model variable must be set, but has no effect, model selection done with URL
            messages=[
                {
                    "role": "system",
                    "content": json_instruction,
                    },
                {
                    "role": "system",
                    "content": message_master_all_sec_at_once,
                    },

                {
                    "role": "user",
                    "content": text_to_update,
                    }
                ],
            response_format={"type": "json_object"},
            )
    output = json.loads(completion_master_inparts.choices[0].message.content)

    identified_topics = [] #Error check that actually only one section is identified

    for llm_key, value in output.items(): #Part of error check, calculating how many topics LLM produced
        identified_topics.append(llm_key) 

    for llm_key, value in output.items(): #Adding to master dict
        if len(identified_topics) == 1: #All good, only one section identified
            master_all_at_once2_copy2[key] = value
            print(f"Final output for {key}: {master_all_at_once2_copy2[key]} \n")
        else:
            print(f"Error: Multiple topics identified: {identified_topics} for {key}")
            print("Will not do anything.")





################                      COUNTING SECTIOS AND CLAUSES
############################################################################################################

# Numbering clauses in the Master list
for key, value_list in master_all_at_once2_copy2.items():
    master_all_at_once2_copy2[key] = [f"{i+1}. {item}" for i, item in enumerate(value_list)]


# New dictionary to store counts of clauses
clauses_count_all_at_once_2 = {}
for key, value in master_all_at_once2_copy2.items():
    clauses_count_all_at_once_2[key] = [{"clause": clause, "count": 0} for clause in value]


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
    for topic, clauses in master_all_at_once2_copy2.items():
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
                if output_key in output and topic in clauses_count_all_at_once_2:
                    for i, (item1, item2) in enumerate(zip(output[output_key], clauses_count_all_at_once_2[topic]), start=1):
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


for key, value in clauses_count_all_at_once_2.items():
    print(f"Topic: {key}")
    for item in value:
        print(f"{item['clause']} - {item['count']} \n")







#### Importing end result dictionaries for analysation



folder_path = 'T_GPT4'
os.makedirs(folder_path, exist_ok=True)

with open(os.path.join(folder_path, 'dict_of_sections2.json'), 'w') as f:
    json.dump(dict_of_sections2, f)


with open(os.path.join(folder_path, 'master_all_at_once2_copy2.json'), 'w') as f:
    json.dump(master_all_at_once2_copy2, f)


with open(os.path.join(folder_path, 'clauses_count_all_at_once_2.json'), 'w') as f:
    json.dump(clauses_count_all_at_once_2, f)



# Think about output style!


with open(os.path.join(folder_path, '21_Section_All.txt'), 'w') as f:
    for key, value in clauses_count_all_at_once_2.items():
        f.write(f"Topic: {key} \n\n")
        for item in value:
            f.write(f"{item['clause']} - {item['count']} \n")
        f.write("\n")


with open(os.path.join(folder_path, 'Execution_counter.txt'), 'a') as f:
    f.write(f"21_Section One \n")
    f.write("\n")
    f.write(f"To summarize section all sections (comparing all sections of the same topic at once), it took: {count_all_sections_at_once2} runs.\n")
    f.write("\n")
    f.write("\n")
    f.write("\n")


with open(os.path.join(folder_path, 'dict_of_synonym_sections2.txt'), 'w') as f:
    for key, value in dict_of_sections2.items():
        f.write(f"{key}: \n\n")
        for item in value:
            f.write(f"    {item} \n")
        f.write("\n")



