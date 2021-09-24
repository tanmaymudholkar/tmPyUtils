from __future__ import print_function, division

import os, sys, subprocess, re, math, json

XSEC_FRACTIONAL_ERROR_TOLERANCE = 0.01

def get_number_of_events_in_dataset(dataset_name):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"file dataset={d} | grep file.nevents\"".format(d=dataset_name), shell=True, universal_newlines=True, executable="/bin/bash"))
    total_nevents = 0
    for nevents_line in dasgoclient_output_raw.splitlines():
        nevents = int(nevents_line)
        total_nevents += nevents
    return total_nevents

def print_number_of_events_in_dataset(dataset_name):
    print("#evts in {d}: {n}".format(d=dataset_name, n=get_number_of_events_in_dataset(dataset_name)))

def get_list_of_datasets(query_string):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"dataset dataset={q}\"".format(q=query_string), shell=True, universal_newlines=True, executable="/bin/bash"))
    datasets_list = []
    for dset in dasgoclient_output_raw.splitlines():
        datasets_list.append(dset)
    return datasets_list

def print_list_of_datasets(query_string):
    for dataset in get_list_of_datasets(query_string):
        print(dataset)

def print_list_of_datasets_with_nevts(query_string):
    n_events_list = []
    print("Number of events (unsorted):")
    for dataset in get_list_of_datasets(query_string):
        n_events = get_number_of_events_in_dataset(dataset)
        print("{d}: {n}".format(d=dataset, n=n_events))
        n_events_list.append((dataset, n_events))
    max_length_dname = max([len(dataset) for dataset, n_events in n_events_list])
    max_length_nevents = max([len(str(n_events)) for dataset, n_events in n_events_list])
    print("="*200)
    print("Number of events (sorted):")
    for dataset_name, n_events in sorted(n_events_list, key=(lambda d_n_pair: d_n_pair[1]), reverse=True):
        print(("{d:>" + str(max_length_dname) + "}: {n:<" + str(max_length_nevents) + "}").format(d=dataset_name, n=n_events))

def get_mcm_prepid_for_dataset(dataset_name):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"mcm dataset={d}\"".format(d=dataset_name), shell=True, universal_newlines=True, executable="/bin/bash"))
    if (len(dasgoclient_output_raw.splitlines()) != 1): sys.exit("ERROR: multiple prepIDs for pattern: {p}".format(p=dataset_name))
    return str((dasgoclient_output_raw.splitlines())[0])

def parse_xsec_info_output(xsec_info_output, printDebug=False):
    if printDebug: print("Starting to parse xsec process output...")
    xsec_re = re.compile(r"^After filter: final cross section = ([^ ]*) \+- ([^ ]*) pb$")
    eq_lumi_re = re.compile(r"^After filter: final equivalent lumi for 1M events \(1/fb\) = ([^ ]*) \+- ([^ ]*)$")
    xsec = None
    eq_lumi = None
    for output_line in xsec_info_output.splitlines():
        xsec_re_match = xsec_re.match(output_line)
        if xsec_re_match:
            if printDebug: print("Line matching \"xsec_re\": {o}".format(o=output_line))
            xsec_value = float(xsec_re_match.group(1))
            xsec_error = float(xsec_re_match.group(2))
            if (math.fabs(xsec_error/xsec_value) > XSEC_FRACTIONAL_ERROR_TOLERANCE): sys.exit("ERROR: too large an uncertainty in cross-section. Measured: {v} +- {e}, fractional uncertainty = {u}.".format(v=xsec_value, e=xsec_error, u=math.fabs(xsec_error/xsec_value)))
            if (xsec is None):
                if printDebug: print("Found xsec: {x} +- {xe}".format(x=xsec_value, xe=xsec_error))
                xsec = xsec_value
            else:
                sys.exit("ERROR: multiple lines seem to contain xsec value.")
        eq_lumi_re_match = eq_lumi_re.match(output_line)
        if eq_lumi_re_match:
            if printDebug: print("Line matching \"eq_lumi_re\": {o}".format(o=output_line))
            eq_lumi_value = float(eq_lumi_re_match.group(1))
            eq_lumi_error = float(eq_lumi_re_match.group(2))
            if (math.fabs(eq_lumi_error/eq_lumi_value) > XSEC_FRACTIONAL_ERROR_TOLERANCE): sys.exit("ERROR: too large an uncertainty in equivalent lumi. Measured: {v} +- {e}, fractional uncertainty = {u}.".format(v=eq_lumi_value, e=eq_lumi_error, u=math.fabs(eq_lumi_error/eq_lumi_value)))
            if (eq_lumi is None):
                if printDebug: print("Found eq_lumi: {e} +- {ee}".format(e=eq_lumi_value, ee=eq_lumi_error))
                eq_lumi = eq_lumi_value
            else:
                sys.exit("ERROR: multiple lines seem to contain eq_lumi value.")
    if ((xsec is None) or (eq_lumi is None)): sys.exit("ERROR: either cross-section or equivalent_lumi not found.")
    # The script runs over 1 million events. So we expect
    # cross_section*equivalent_lumi = 1000000
    # However, someone decided that cross_section would be measured in pb
    # and equivalent lumi in (1/fb). So we expect
    # (cross_section/pb)*(equivalent_lumi/(1/fb)) = 1000
    # UPDATE: this only seems to work for some datasets, so commenting out for now...
    # cross_check = math.fabs((xsec*eq_lumi/1000.0) - 1.0)
    # if (cross_check > XSEC_FRACTIONAL_ERROR_TOLERANCE): sys.exit("ERROR: cross-section={x} and equivalent_lumi={l} fail sanity check. Expected their product to be 1000, but found: {p}".format(x=xsec, l=eq_lumi, p=xsec*eq_lumi))
    # return (xsec, eq_lumi)
    return xsec

def get_xsec_info_for_dataset(dataset_name, identifier, printDebug=True):
    # Unlike most other functions in tmPyUtils modules, this particular function is not
    # isolated well enough from other analysis steps
    # In particular, it requires setting up my git repo for the "official" cross-section tool
    if printDebug: print("Running over dataset {d} with id={i}".format(d=dataset_name, i=identifier))
    dataset_nevents = get_number_of_events_in_dataset(dataset_name)
    if printDebug: print("nevents in dataset: {n}".format(n=dataset_nevents))
    cwd = os.getcwd()
    dataset_mcm_id = get_mcm_prepid_for_dataset(dataset_name)
    if ("CMSSW_BASE" in os.environ):
        sys.exit("ERROR: xsec utility requires you to start from a \"fresh\" environment. Currently CMSSW_BASE is set to: {v}".format(v=os.environ["CMSSW_BASE"]))
    xsec_scram_arch = os.environ["XSEC_SCRAM_ARCH"]
    path_xsec_cmssw = os.environ["PATH_XSEC_CMSSW"]
    path_xsec_scripts = os.environ["PATH_XSEC_SCRIPTS"]
    xsec_info_output = str(subprocess.check_output("cd {c}/Utilities/calculateXSectionAndFilterEfficiency && ./tmGetXSecWrapper.sh {m} {i} {sa} {cmssw} {ps}".format(c=cwd, m=dataset_mcm_id, i=identifier, sa=xsec_scram_arch, cmssw=path_xsec_cmssw, ps=path_xsec_scripts), shell=True, stderr=subprocess.STDOUT, executable="/bin/bash", universal_newlines=True))
    xsec = parse_xsec_info_output(xsec_info_output)
    if printDebug: print("xsec: {x}".format(x=xsec))
    return (xsec, dataset_nevents)

def save_dataset_xsec_info_into_json(dataset_name, identifier, output_path):
    xsec, nevents = get_xsec_info_for_dataset(dataset_name, identifier)
    output_dict = {
        "xsec": xsec,
        "nevents": nevents
    }
    with open(output_path, 'w') as json_output_file_handle:
        json.dump(output_dict, json_output_file_handle, indent=4, separators=(',', ': '))
    # json.dump for some reason doesn't save output with a newline at the end
    with open(output_path, 'a') as json_output_file_handle:
        json_output_file_handle.write("\n")
