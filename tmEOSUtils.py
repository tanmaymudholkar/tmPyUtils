from __future__ import print_function, division

import os, sys, subprocess, tmGeneralUtils

EOSPrefix = os.getenv("EOSPREFIX")
EOStmpArea = os.getenv("EOSTMPAREA")

def generate_list_of_files_in_eos_path(eos_path=None, appendPrefix=True, vetoPattern=None, restrictToROOTFiles=True, fetchSizeInfo=False):
    if (eos_path is None): sys.exit("ERROR: eos_path cannot be None.")
    subprocess.check_call("mkdir -p {ETA}".format(ETA=EOStmpArea), shell=True)
    subprocess.check_call("bash -c \"/usr/bin/eos {eP} ls -a -l {p} > {ETA}/EOS_tmpFileList.txt 2>&1\"".format(eP=EOSPrefix, p=eos_path, ETA=EOStmpArea), shell=True)
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
                list_of_files_in_eos_subfolder_generator = generate_list_of_files_in_eos_path(eos_path="{p}/{dN}".format(p=eos_path, dN=directoryName), appendPrefix=appendPrefix, vetoPattern=vetoPattern, restrictToROOTFiles=restrictToROOTFiles, fetchSizeInfo=fetchSizeInfo)
                if (fetchSizeInfo):
                    for file_size_pair in list_of_files_in_eos_subfolder_generator:
                        yield (file_size_pair[0], file_size_pair[1])
                else:
                    for file_in_eos_subfolder in list_of_files_in_eos_subfolder_generator:
                        yield file_in_eos_subfolder
            elif (fileOrDirectoryPermissionsString[0] == "-"):
                fileName = fileOrDirectoryDetails[-1]
                isCandidateToYield = True
                if (restrictToROOTFiles): isCandidateToYield = (fileName[-5:] == ".root")
                if isCandidateToYield:
                    fullFilePath = ""
                    if (appendPrefix):
                        fullFilePath += "{eP}".format(eP=EOSPrefix)
                    fullFilePath += "{p}/{f}".format(p=eos_path, f=fileName)
                    if (fetchSizeInfo):
                        size = int(0.5 + float(fileOrDirectoryDetails[4]))
                        if (vetoPattern is None):
                            yield (fullFilePath, size)
                        else:
                            if not(vetoPattern in fullFilePath):
                                yield (fullFilePath, size)
                    else:
                        if (vetoPattern is None):
                            yield fullFilePath
                        else:
                            if not(vetoPattern in fullFilePath):
                                yield fullFilePath

def get_eos_file_size_in_bytes(fullFilePath):
    filePathFormatted = fullFilePath.replace("/", "_")
    subprocess.check_call("bash -c \"/usr/bin/eos {eP} ls -a -l {fFP} > {ETA}/tmpFileDetails_{fPF}.txt 2>&1\"".format(eP=EOSPrefix, fFP=fullFilePath, fPF=filePathFormatted, ETA=EOStmpArea), shell=True)
    fileDetails = open("{ETA}/tmpFileDetails_{fPF}.txt".format(ETA=EOStmpArea, fPF=filePathFormatted), "r")
    fileDetailsContents = fileDetails.readlines()
    fileDetails.close()
    subprocess.check_call("rm -f {ETA}/tmpFileDetails_{fPF}.txt".format(ETA=EOStmpArea, fPF=filePathFormatted), shell=True)
    if (not(len(fileDetailsContents)) == 1): sys.exit("ERROR: details file contains more than one line.")
    return (int(0.5 + float((fileDetailsContents[0].strip().split())[4])))

def generate_dirsizes_info(eos_path=None):
    if (eos_path is None): sys.exit("ERROR: eos_path cannot be None.")
    subprocess.check_call("mkdir -p {ETA}".format(ETA=EOStmpArea), shell=True)
    subprocess.check_call("bash -c \"/usr/bin/eos {eP} ls -a -lh {p} > {ETA}/EOS_tmpFolderList.txt 2>&1\"".format(eP=EOSPrefix, p=eos_path, ETA=EOStmpArea), shell=True)
    fileList = open("{ETA}/EOS_tmpFolderList.txt".format(ETA=EOStmpArea), "r")
    entriesToCheck = fileList.readlines()
    fileList.close()
    subprocess.check_call("rm -f {ETA}/EOS_tmpFolderList.txt".format(ETA=EOStmpArea), shell=True)
    for lineRaw in entriesToCheck:
        fileOrDirectoryDetails = (lineRaw.strip()).split()
        if ((fileOrDirectoryDetails[-1] == ".") or (fileOrDirectoryDetails[-1] == "..")):
            continue
        else:
            fileOrDirectoryPermissionsString = fileOrDirectoryDetails[0]
            if (fileOrDirectoryPermissionsString[0] == "d"):
                directoryName = fileOrDirectoryDetails[-1]
                print("Getting size info for folder: {f}".format(f=directoryName))
                directory_total_size = 0
                list_of_files_in_eos_subfolder_generator = generate_list_of_files_in_eos_path(eos_path="{p}/{dN}".format(p=eos_path, dN=directoryName), appendPrefix=False, restrictToROOTFiles=False, fetchSizeInfo=True)
                for file_size_pair in list_of_files_in_eos_subfolder_generator:
                    directory_total_size += file_size_pair[1]
                yield (directoryName, directory_total_size)
            elif (fileOrDirectoryPermissionsString[0] == "-"):
                fileName = fileOrDirectoryDetails[-1]
                print("Getting size info for file: {f}".format(f=fileName))
                fullFilePath = "{p}/{f}".format(p=eos_path, f=fileName)
                yield (fileName, get_eos_file_size_in_bytes(fullFilePath))

def print_eos_dirsizes(eos_path=None):
    if (eos_path is None): sys.exit("ERROR: eos_path cannot be None.")
    nameSizeDict = {}
    namesList = []
    totalSize = 0
    for nameSizePair in generate_dirsizes_info(eos_path=eos_path):
        name = nameSizePair[0]
        size = nameSizePair[1]
        namesList.append(name)
        nameSizeDict[name] = size
        totalSize += size
    nameLength = 3 + max(len(name) for name in namesList)
    for name in namesList:
        print("{n}: {s}".format(n=tmGeneralUtils.alignFixedWidthStringLeft(nameLength, name), s=tmGeneralUtils.get_bytesize_human_readable(size_in_bytes_raw=nameSizeDict[name])))
    print("-"*100)
    print("{tSS}: {tS}".format(tSS=tmGeneralUtils.alignFixedWidthStringLeft(nameLength, "Total size") ,tS=tmGeneralUtils.get_bytesize_human_readable(size_in_bytes_raw=totalSize)))

def test():
    print("Without veto pattern:")
    files_generator = generate_list_of_files_in_eos_path("/store/user/lpcsusystealth/selections/")
    for fname in files_generator:
        print("Found file: {f}".format(f=fname))
    print("With veto pattern \"mediumfake\":")
    files_generator = generate_list_of_files_in_eos_path("/store/user/lpcsusystealth/selections/", vetoPattern="mediumfake")
    for fname in files_generator:
        print("Found file: {f}".format(f=fname))
    print("Printing EOS dirsizes in folder /store/user/lpcsusystealth/statistics/:")
    print_eos_dirsizes(eos_path="/store/user/lpcsusystealth/statistics/")

if __name__ == "__main__":
    test()
