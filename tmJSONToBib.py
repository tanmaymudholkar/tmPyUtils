#!/usr/bin/env python3

from __future__ import print_function, division

import json, requests, argparse, sys, enum, re, time

inputArgumentsParser = argparse.ArgumentParser(description="Convert JSON input with doi/arxiv IDs to a CMS-compabible bib file.")
inputArgumentsParser.add_argument("--json_input", required=True, help="Path to input JSON.", type=str)
inputArgumentsParser.add_argument("--bib_header_source", default="/dev/null", help="Path to file containing any header info for the bib output.", type=str)
inputArgumentsParser.add_argument("--bib_output", required=True, help="Path to output bib file.", type=str)
inputArguments = inputArgumentsParser.parse_args()

# For example, save the following (omitting the double quotes) in a file named example.json:
"""
{
    "references": [
        "doi:10.1016/j.physletb.2015.03.017",
        "doi:10.1140/epjc/s10052-011-1554-0",
        "arxiv:hep-ex/9902006"
    ]
}
"""
# and then run: ./tmJSONToBib.py --json_input example.json --bib_output example.bib

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
    inspire_restapi_format_query = get_inspire_restapi_format_query(inspire_key, reference_id)
    response = requests.get(inspire_restapi_format_query)
    time.sleep(1.0) # API imposes rate limit of 2 per second, this is to keep the rate well below that limit
    if not(response.status_code == 200): # HTTP OK, got back everything we asked for
        sys.exit("Query failed. Are you sure this record exists? Query: {q}".format(q=inspire_restapi_format_query))
    return response.text

def post_process(response_text: str) -> str:
    output_text = ""
    for response_line_uncorrected in response_text.splitlines():
        if not(response_line_uncorrected == ""):
            response_line = response_line_uncorrected
            # ignore all "number" fields
            if (re.search(r'[nN][uU][mM][bB][eE][rR] *=', response_line)):
                continue
            # if "pages" field has a page range, use only the first page (CMS guideline)
            if (re.search(r'[pP][aA][gG][eE][sS] *=', response_line)):
                response_line = re.sub(r'([0-9]*)-{1,2}[0-9]*', r'\1', response_line)
            # surround special characters in the "author" field with curly braces
            if (re.search(r'[aA][uU][tT][hH][oO][rR] *=', response_line)):
                special_character_signatures = (r'`' + r"'" + r'\^"H~oclrv=')
                response_line = re.sub((r'\\([' + special_character_signatures + '])([a-zA-Z])'), (r'{\\\1\2}'), response_line)
            output_text += (response_line + "\n")
    return output_text

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

# Step 3: Get BibTEX source for each input
references_from_json_input = json_input_data["references"]
print("Found {n} references.".format(n=len(references_from_json_input)))
references_written = []
for reference in references_from_json_input:
    if (reference in references_written):
        sys.exit("ERROR: duplicate reference: {r}".format(r=reference))
    reference_string_split = reference.split(":")
    inspire_key = None
    try:
        inspire_key = AllowedKeys[reference_string_split[0]]
    except KeyError:
        sys.exit("ERROR in reference string: {s}. Must specify either \"doi\" or \"arxiv\" as identifier.".format(s=reference))
    reference_id = ''.join(reference_string_split[1:])
    print("Getting inspire_key: {i}, reference_id: {ident}".format(i=inspire_key, ident=reference_id))
    bibtex_from_inspire = post_process(get_bibtex_from_inspire(inspire_key, reference_id))
    references_written.append(reference)
    output_file_handle.write(bibtex_from_inspire)

output_file_handle.close()
print("All done!")
