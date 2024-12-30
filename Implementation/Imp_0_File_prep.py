#
# Copyright (C) Valeriya Koshevaya
#
# SPDX-License-Identifier: MIT
#



# Source for client code:
# https://version.aalto.fi/gitlab/cloud-and-apps/large-language-models/-/tree/master?ref_type=heads


########    Importing libraries, setting up the model

import os
import re

import httpx
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# For all endpoints see https://www.aalto.fi/en/services/azure-openai#6-available-api-s
path = "" # Add endpoint here (e.g., GPT-4-Turbo)



def create_client():
    def update_base_url(request: httpx.Request) -> None:
        if request.url.path == "/chat/completions":
            request.url = request.url.copy_with(path=path)

    client = OpenAI(
        base_url="<your_base_url>",
        api_key=False, # Replace with your actual API key handling method
        default_headers = {
            "Ocp-Apim-Subscription-Key": "<your_subscription_key>",
        },
        http_client=httpx.Client(
            event_hooks={
                "request": [update_base_url], # Customize as needed
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

