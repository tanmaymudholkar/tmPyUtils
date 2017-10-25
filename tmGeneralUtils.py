from __future__ import print_function, division

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
