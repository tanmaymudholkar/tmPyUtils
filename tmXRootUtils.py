import sys
if (sys.version_info.major < 3): sys.exit("Must be using py3 onwards. Current version info: {v}".format(v=sys.version_info))
if (sys.version_info.minor < 7): sys.exit("Must be using python 3.7 onwards. Current version info: {v}".format(v=sys.version_info))

import os, subprocess
from typing import List, Tuple

import tmProgressBar

def Parse_xrdfs_ls_OutputLine(xrdfs_ls_output_line: str) -> Tuple[bool, str]:
    output_line_split = (xrdfs_ls_output_line.strip()).split()
    if not(len(output_line_split) == 5): sys.exit("ERROR: Unable to parse xrdfs line: {l}".format(l=xrdfs_ls_output_line))
    is_directory = (output_line_split[0][0] == 'd')
    full_path = output_line_split[4]
    return (is_directory, full_path)

def Query_xrdfs_adler32(xrd_prefix: str, file_full_path: str) -> str:
    query_output = subprocess.check_output("xrdfs {p} query checksum {f}".format(p=xrd_prefix, f=file_full_path), shell=True, text=True, executable="/bin/bash")
    query_output_split = (query_output.strip()).split()
    if not(len(query_output_split) == 2): sys.exit("ERROR: Unable to parse xrdfs checksum output: {o}".format(o=query_output))
    if not(query_output_split[0] == "adler32"): sys.exit("ERROR: xrdfs checksum returns it in an unexpected format: {f}".format(f=query_output_split[0]))
    return query_output_split[1]

def GetLocal_adler32(local_file_path: str) -> str:
    adler32_output = subprocess.check_output("xrdadler32 {f}".format(f=local_file_path), shell=True, text=True, executable="/bin/bash")
    adler32_output_split = (adler32_output.strip()).split()
    if not(len(adler32_output_split) == 2): sys.exit("ERROR: adler32 output not in expected format: {o}".format(o=adler32_output))
    if not(adler32_output_split[1] == local_file_path): sys.exit("ERROR: adler32 output not in expected format: {o}".format(o=adler32_output))
    return adler32_output_split[0]

def GetListOfFilesInDirectory(xrd_prefix: str, directory_path_without_xrd_prefix: str) -> List[Tuple[str, str]]:
    xrdfs_ls_output = subprocess.check_output("xrdfs {p} ls -l -R {d}".format(p=xrd_prefix, d=directory_path_without_xrd_prefix), shell=True, text=True, executable="/bin/bash")
    list_of_files = []
    for line in xrdfs_ls_output.splitlines():
        if (len(line) == 0): continue
        is_directory, full_path = Parse_xrdfs_ls_OutputLine(line)
        if is_directory: continue
        adler32_checksum_value = Query_xrdfs_adler32(xrd_prefix, full_path)
        if not(full_path[:len(directory_path_without_xrd_prefix)] == directory_path_without_xrd_prefix):
            sys.exit("ERROR: xrdfs ls output path {p} does not start with expected directory: {d}".format(p=full_path, d=directory_path_without_xrd_prefix))
        partial_path = full_path[len(directory_path_without_xrd_prefix):] # get path relative to parent directory
        while (partial_path[0] == "/"):
            partial_path = partial_path[1:] # remove any leading slashes
        list_of_files.append((partial_path, adler32_checksum_value))
    return list_of_files

def CloneDirectoryLocally(xrd_prefix_remote: str, remote_path_without_xrd_prefix: str, path_local: str, print_verbose: bool) -> None:
    if not(os.path.isdir(path_local)): subprocess.check_call("mkdir -p {p}".format(p=path_local), shell=True, executable="/bin/bash")
    file_details = GetListOfFilesInDirectory(xrd_prefix_remote, remote_path_without_xrd_prefix)
    progressBar = tmProgressBar.tmProgressBar(counterMaxValue=len(file_details))
    file_index = 1
    file_index_refresh_freq = max(1, len(file_details)//100)
    progressBar.initializeTimer()
    for relative_path, checksum_value in file_details:
        needs_update = True
        if print_verbose: print("Copying: {r}".format(r=relative_path))
        if os.path.isfile("{o}/{r}".format(o=path_local, r=relative_path)):
            local_checksum_value = GetLocal_adler32("{o}/{r}".format(o=path_local, r=relative_path))
            if (local_checksum_value == checksum_value):
                needs_update = False
        if print_verbose:
            if needs_update:
                print("File {o}/{r} does not exist or has and has the wrong checksum. Copying...".format(o=path_local, r=relative_path))
            else:
                print("File {o}/{r} already exists and has the right checksum. Skipping!".format(o=path_local, r=relative_path))
        if not(needs_update): continue
        xrd_copy_command = "xrdcp --silent --nopbar --force --path --streams 15 {pref}//{parent}/{relpath} {outputdir}/{relpath}".format(pref=xrd_prefix_remote, parent=remote_path_without_xrd_prefix, relpath=relative_path, outputdir=path_local)
        subprocess.check_call(xrd_copy_command, shell=True, executable="/bin/bash")
        local_checksum_value = GetLocal_adler32("{o}/{r}".format(o=path_local, r=relative_path))
        if (not(checksum_value == local_checksum_value)): sys.exit("ERROR: Checksums do not match after copying file with relative path: {p}".format(p=relative_path))
        if ((file_index % file_index_refresh_freq == 0) or (file_index == (len(file_details)-1))): progressBar.updateBar(file_index/len(file_details))
        file_index += 1
    progressBar.terminate()

def test():
    list_of_files_test = GetListOfFilesInDirectory(xrd_prefix="root://cmseos.fnal.gov", directory_path_without_xrd_prefix="/store/user/tmudholk/test")
    print("Files found:")
    for file_info in list_of_files_test:
        print("Found: {i}".format(i=file_info))
    CloneDirectoryLocally(xrd_prefix_remote="root://cmseos.fnal.gov", remote_path_without_xrd_prefix="/store/user/tmudholk/test", path_local="../test_tmXrootUtils", print_verbose=True)

if __name__ == "__main__":
    test()
