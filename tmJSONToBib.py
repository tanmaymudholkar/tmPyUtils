#!/usr/bin/env python3

from __future__ import print_function, division

import json, requests, argparse, sys, enum

inputArgumentsParser = argparse.ArgumentParser(description="Convert JSON input "
                                               "with doi/arxiv IDs to a CMS-compabible bib file.")
inputArgumentsParser.add_argument("--json_input", required=True,
                                  help="Path to input JSON.", type=str)
inputArgumentsParser.add_argument("--bib_header_source",
                                  help="Path to file containing any "
                                  "header info for the bib output.",
                                  type=str)
inputArgumentsParser.add_argument("--bib_output", required=True,
                                  help="Path to output bib file.", type=str)
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

def get_bibtex_from_inspire(inspire_key: AllowedKeys, reference_id: str) -> str:
    bibtex_output = "none\n"
    inspire_restapi_format_query = get_inspire_restapi_format_query(inspire_key, reference_id)
    response = requests.get(inspire_restapi_format_query)
    if not(response.status_code == 200): # HTTP OK, got back everything we asked for
        sys.exit("Query failed. Are you sure this record exists? Query: {q}".format(q=inspire_restapi_format_query))
    return response.text

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
    inspire_key = AllowedKeys[reference_string_split[0]]
    reference_id = ''.join(reference_string_split[1:])
    print("Getting inspire_key: {i}, reference_id: {ident}".format(i=inspire_key, ident=reference_id))
    bibtex_from_inspire = get_bibtex_from_inspire(inspire_key, reference_id)
    output_file_handle.write(bibtex_from_inspire)

output_file_handle.close()
print("All done!")