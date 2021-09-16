from __future__ import print_function, division

import os, sys, subprocess

def get_list_of_datasets(query_string):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"dataset dataset={q}\"".format(q=query_string), shell=True, universal_newlines=True, executable="/bin/bash"))
    datasets_list = []
    for dset in dasgoclient_output_raw.splitlines():
        datasets_list.append(dset)
    return datasets_list

def print_list_of_datasets(query_string):
    for dataset in get_list_of_datasets(query_string):
        print(dataset)

def get_number_of_events_in_dataset(dataset_name):
    dasgoclient_output_raw = str(subprocess.check_output("dasgoclient -query \"file dataset={d} | grep file.nevents\"".format(d=dataset_name), shell=True, universal_newlines=True, executable="/bin/bash"))
    total_nevents = 0
    for nevents_line in dasgoclient_output_raw.splitlines():
        nevents = int(nevents_line)
        total_nevents += nevents
    return total_nevents

def print_number_of_events_in_dataset(dataset_name):
    print("#evts in {d}: {n}".format(d=dataset_name, n=get_number_of_events_in_dataset(dataset_name)))
