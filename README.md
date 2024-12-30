# Thesis-implementation
This repository contains the implementation developed as part of a thesis on integrating Large Language Models (LLMs) into Contract Lifecycle Management (CLM).

The thesis and a full description of the methodology, rationale, and findings can be accessed here:

The code is published under MIT license.


The implementation focuses on evaluating key LLM capabilities in the context of CLM. Specifically, it tests the following functionalities:

## Summarization Methods
1. Document-Level Summarization: Summarizing the entire contract as a single text input.
2. Section-Level Summarization: Summarizing each section of the contract independently.

## Synthesis Methods
1. Document-wide Synthesis: Synthesizing insights from the entire document text at once.
2. Sectional Synthesis: Synthesizing all instances of the same section (e.g., "Payment Terms") across multiple documents simultaneously.
3. Incremental Synthesis: Combining information two sections at a time, progressively building the synthesized output.


Together, these methods form five distinct summarization-synthesis combinations that are being implemented.

## Document Analysis
A new document analysis is performed to evaluate LLM's ability to:
1. Identify Missing Common Clauses: Detect which clauses from a predefined reference list are absent in a new document.
2. Detect Atypical Clauses: Identify clauses present in the new document that are not included in the reference list, highlighting potentially unusual or unexpected content.
