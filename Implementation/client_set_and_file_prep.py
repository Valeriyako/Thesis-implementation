# Source:
# https://version.aalto.fi/gitlab/cloud-and-apps/large-language-models/-/tree/master?ref_type=heads


########    Importing libraries, setting up the model

import os
import re

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# For all endpoints see https://www.aalto.fi/en/services/azure-openai#6-available-api-s
#path = "/v1/chat/gpt4-8k" # GPT-4 (vanilla)
path = "/v1/openai/gpt4-turbo/chat/completions" # GPT-4-Turbo
#path = "/v1/chat/gpt-35-turbo-1106" # GPT-3.5



def create_client():
    def update_base_url(request: httpx.Request) -> None:
        if request.url.path == "/chat/completions":
            request.url = request.url.copy_with(path=path)

    client = OpenAI(
        base_url="https://aalto-openai-apigw.azure-api.net",
        api_key=False, # API key not used, and rather set below
        default_headers = {
            "Ocp-Apim-Subscription-Key": os.environ.get("AZURE_KEY"),
        },
        http_client=httpx.Client(
            event_hooks={
                "request": [update_base_url],
                }
            ),
        )
    return client




############                 Reading files, splitting and preprocessing text     ############
############################################################################################################

def read_document(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None


def split_into_sections(document_text):
    # Regex to match sections starting with an empty line, a number, a dot, and a space
    # It looks for an empty line followed immediately by a number-dot-space pattern.
    sections = re.split(r'\n\s*(?=\d+\.\s*[A-Za-z][^\n]*)', document_text)

    # Clean up the sections
    # The split includes the delimiter in the resulting sections, but we need to trim leading/trailing whitespace.
    cleaned_sections = [section.strip() for section in sections if section.strip()]

    return cleaned_sections

def preprocess_text(text):
    text = re.sub(r'\n+', '\n', text).strip()  # Reduce multiple line breaks to a single one
    text = re.sub(r'\n\s*\n', '\n', text)  # Remove empty lines
    text = re.sub(r'(?<![\.\?\!:])\n', ' ', text)  # Replace line breaks that are not after a period, question mark, colon or exclamation mark
    return text

