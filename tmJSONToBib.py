#!/usr/bin/env python3

from __future__ import print_function, division

import json, requests, argparse, sys, enum, re

inputArgumentsParser = argparse.ArgumentParser(description="Convert JSON input with doi/arxiv IDs to a CMS-compabible bib file.")
inputArgumentsParser.add_argument("--json_input", required=True, help="Path to input JSON.", type=str)
inputArgumentsParser.add_argument("--bib_header_source", default="/dev/null", help="Path to file containing any header info for the bib output.", type=str)
inputArgumentsParser.add_argument("--bib_output", required=True, help="Path to output bib file.", type=str)
inputArgumentsParser.add_argument("--use_inspire_bib_ids", action="store_true", help="If this flag is passed, the bib output stores, for each reference, the bib identifier obtained from INSPIRE rather than the identifier passed in the json input.")
inputArguments = inputArgumentsParser.parse_args()

# Step 0: some basic setup
class AllowedKeys(enum.Enum): # each reference is identified either by its doi or by its arxiv id
    arxiv = 1
    doi = 2
allowed_keys_str = {
    AllowedKeys.arxiv: "arxiv",
    AllowedKeys.doi: "doi"
}

def get_inspire_restapi_format_query(inspire_key: AllowedKeys, reference_id: str) -> str:
    return ("https://inspirehep.net/api/{k}/{ident}?format=bibtex".format(k=allowed_keys_str[inspire_key], ident=reference_id))

def regex_sub(response_text: str, pattern: str, replacement: str) -> str:
    output_text = ""
    for response_line in response_text.splitlines():
        if not(response_line == ""):
            output_text += (re.sub(pattern, replacement, response_line) + "\n")
    return output_text

def post_process(response_text: str, title: str) -> str:
    # Unless flag use_inspire_bib_ids is passed, name the bib item appropriately
    if not(inputArguments.use_inspire_bib_ids):
        response_text = regex_sub(response_text, r'^@(.*)\{.*$', ((r'@\1{') + title + ','))
    return response_text

def get_bibtex_from_inspire(inspire_key: AllowedKeys, reference_id: str, title: str) -> str:
    bibtex_output = "none\n"
    inspire_restapi_format_query = get_inspire_restapi_format_query(inspire_key, reference_id)
    response = requests.get(inspire_restapi_format_query)
    if not(response.status_code == 200): # HTTP OK, got back everything we asked for
        sys.exit("Query failed. Are you sure this record exists? Query: {q}".format(q=inspire_restapi_format_query))
    response_text = post_process(response.text, title)
    return response_text

# Step 1: Load json input
json_input_data = None
with open(inputArguments.json_input, 'r') as json_input_handle:
    json_input_data = json.load(json_input_handle)

# Open output file
output_file_handle = open(inputArguments.bib_output, 'w')

# Step 2: Start building bibtex output file. First, copy over everything
# in the header file
# (potentially including records absent from the INSPIRE database
# or with incorrect bibtex info)
if not(inputArguments.bib_header_source == "/dev/null"):
    with open(inputArguments.bib_header_source, 'r') as bib_header_source_handle:
        output_file_handle.write(bib_header_source_handle.read())

# Step 2: Get BibTEX source for each input
references_from_json_input = json_input_data["references"]
print("Found {n} references.".format(n=len(references_from_json_input)))
for reference in references_from_json_input:
    if not (len(reference) == 1):
        sys.exit("ERROR: json input in unexpected format. Check this reference: {r}".format(r=str(reference)))
    title = (list(reference.keys()))[0]
    reference_string_raw = reference[title]
    reference_string_split = reference_string_raw.split(":")
    inspire_key = None
    try:
        inspire_key = AllowedKeys[reference_string_split[0]]
    except KeyError:
        sys.exit("ERROR in reference string: {s}. Must specify either \"doi\" or \"arxiv\" as identifier.".format(s=reference_string_raw))
    reference_id = ''.join(reference_string_split[1:])
    print("Getting inspire_key: {i}, reference_id: {ident}".format(i=inspire_key, ident=reference_id))
    bibtex_from_inspire = get_bibtex_from_inspire(inspire_key, reference_id, title)
    output_file_handle.write(bibtex_from_inspire)

output_file_handle.close()
print("All done!")
