from __future__ import print_function, division

import os, sys, subprocess

EOSPrefix = os.getenv("EOSPREFIX")
EOStmpArea = os.getenv("EOSTMPAREA")

def generate_list_of_root_files_in_eos_path(eos_path=None, appendPrefix=True, vetoPattern=None):
    if (eos_path is None): sys.exit("ERROR: eos_path cannot be None.")
    subprocess.check_call("mkdir -p {ETA}".format(ETA=EOStmpArea), shell=True)
    subprocess.check_call("bash -c \"/usr/bin/eos {eP} ls -a -lh {p} > {ETA}/EOS_tmpFileList.txt 2>&1\"".format(eP=EOSPrefix, p=eos_path, ETA=EOStmpArea), shell=True)
    fileList = open("{ETA}/EOS_tmpFileList.txt".format(ETA=EOStmpArea), "r")
    entriesToCheck = fileList.readlines()
    fileList.close()
    subprocess.check_call("rm -f {ETA}/EOS_tmpFileList.txt".format(ETA=EOStmpArea), shell=True)
    for lineRaw in entriesToCheck:
        fileOrDirectoryDetails = (lineRaw.strip()).split()
        if ((fileOrDirectoryDetails[-1] == ".") or (fileOrDirectoryDetails[-1] == "..")):
            continue
        else:
            fileOrDirectoryPermissionsString = fileOrDirectoryDetails[0]
            if (fileOrDirectoryPermissionsString[0] == "d"):
                directoryName = fileOrDirectoryDetails[-1]
                list_of_root_files_in_eos_subfolder_generator = generate_list_of_root_files_in_eos_path(eos_path="{p}/{dN}".format(p=eos_path, dN=directoryName), appendPrefix=appendPrefix, vetoPattern=vetoPattern)
                for root_file_in_eos_subfolder in list_of_root_files_in_eos_subfolder_generator:
                    yield root_file_in_eos_subfolder
            elif (fileOrDirectoryPermissionsString[0] == "-"):
                fileName = fileOrDirectoryDetails[-1]
                if (fileName[-5:] == ".root"):
                    fullFilePath = ""
                    if (appendPrefix):
                        fullFilePath += "{eP}".format(eP=EOSPrefix)
                    fullFilePath += "{p}/{f}".format(p=eos_path, f=fileName)
                    if (vetoPattern is None):
                        yield fullFilePath
                    else:
                        if not(vetoPattern in fullFilePath):
                            yield fullFilePath

def test():
    print("Without veto pattern:")
    root_files_generator = generate_list_of_root_files_in_eos_path("/store/user/lpcsusystealth/selections/")
    for fname in root_files_generator:
        print("Found file: {f}".format(f=fname))
    print("With veto pattern \"mediumfake\":")
    root_files_generator = generate_list_of_root_files_in_eos_path("/store/user/lpcsusystealth/selections/", vetoPattern="mediumfake")
    for fname in root_files_generator:
        print("Found file: {f}".format(f=fname))

if __name__ == "__main__":
    test()
