from __future__ import print_function, division

import sys

def alignFixedWidthFloatLeft(width, precision, number):
        if not(isinstance(number, float)): sys.exit("alignFixedWidthFloatLeft called with non-float object: {o}".format(o=number))
        formatter = ""
        if (width == 0):
            formatter = "{{n:.{p}f}}".format(p=precision)
        else:
            formatter = "{{n:<{w}.{p}f}}".format(w=width, p=precision)
        returnString = formatter.format(n=number)
        return returnString

def alignFixedWidthStringLeft(width, inputString):
        if not(isinstance(inputString, str)): sys.exit("alignFixedWidthStringLeft called with non-string object: {o}".format(o=inputString))
        formatter = ""
        formatter = "{{s:<{w}}}".format(w=width)
        returnString = formatter.format(s=inputString)
        return returnString

def check_dict_keys_against_list(targetDict, targetList):
    return (set(targetDict.keys()) == set(targetList))

def prettyPrintDictionary(inputDict, valueFormatSpecification="", keyPrintOrder=[]):
    stringLengths = [len(str(key)) for key in inputDict.keys()]
    maxStringLength = max(stringLengths)
    keyFormatSpecification = " >{width}".format(width=maxStringLength)
    if (len(keyPrintOrder) == 0): keyPrintOrder = inputDict.keys()
    for key in keyPrintOrder:
        printStatement = "{keyName!s:" + keyFormatSpecification + "}: "
        if (valueFormatSpecification == ""):
            printStatement += "{dictionaryContent}"
        else:
            printStatement += "{dictionaryContent:" + valueFormatSpecification + "}"
        print(printStatement.format(keyName=key, dictionaryContent=inputDict[key]))

def getConfigurationFromFile(inputFilePath):
    configuration = {}
    configurationFileObject = open(inputFilePath, "r")
    for line in configurationFileObject:
        splitLine = line.split()
        parameterType = splitLine[0]
        whitespaceRemovedNameValueString = "".join(splitLine[1:])
        nameValuePair = whitespaceRemovedNameValueString.split("=")
        if not(len(nameValuePair) == 2): sys.exit("ERROR: unable to parse the following as \"type arg=value\": {line}, or, split: {sL}. Attempted parameter type: {pT}, name-value pair string: {nVPS}, name-value pair: {nVP}".format(line=line, sL=splitLine, pT=parameterType, nVPS=whitespaceRemovedNameValueString, nVP=str(nameValuePair)))
        if parameterType == "int":
            value = int(nameValuePair[1])
        elif parameterType == "float":
            value = float(nameValuePair[1])
        elif parameterType == "string":
            value = nameValuePair[1]
        else:
            sys.exit("Unrecognized parameter type: {pT}".format(pT=parameterType))
        configuration[nameValuePair[0]] = value
    configurationFileObject.close()
    return configuration

def writeConfigurationParametersToFile(configurationParametersList, outputFilePath):
    outputFileObject = open(outputFilePath, "w")
    for configurationParameters in configurationParametersList:
        if not(len(configurationParameters) == 3): sys.exit("ERROR: configuration parameters {cP} not in format (type, name, value)".format(cP=str(configurationParameters)))
        parameterType = configurationParameters[0]
        if not(parameterType in ["int", "float", "string"]): sys.exit("ERROR: Unrecognized parameter type from configuration parameters: {cP}, containing type: {t}".format(cP=str(configurationParameters), t=parameterType))
        parameterName = configurationParameters[1]
        parameterValue = configurationParameters[2]
        outputFileObject.write("{t} {name}={value}\n".format(t=parameterType, name=parameterName, value=parameterValue))
    outputFileObject.close()
