import re, pathlib, sys
import argparse

class CppIncludeOrganizer (object):
    def __init__(self, file):
        self._file = file

    def _massSearch (self, parentSourcesDir, includes) -> list :
        fileNamesToDirsDict = dict ()
        for include in includes:
            filenamesAndDirs = include.split ("/")
            if filenamesAndDirs[-1] not in fileNamesToDirsDict:
                fileNamesToDirsDict[filenamesAndDirs[-1]] = dict ()
            if "includes" not in fileNamesToDirsDict[filenamesAndDirs[-1]]:
               fileNamesToDirsDict[filenamesAndDirs[-1]]["includes"] = dict ()
            fileNamesToDirsDict[filenamesAndDirs[-1]]["includes"][include] = list ()
            if len (filenamesAndDirs) > 1:
                fileNamesToDirsDict[filenamesAndDirs[-1]]["includes"][include] = filenamesAndDirs[0:-1]

        

        massSearchResultDict = dict ()
        for pattern in ["*.h", "*.hpp"]:
            for location in pathlib.Path(parentSourcesDir).rglob(pattern):
                if location.is_file () and location.name in fileNamesToDirsDict:
                    includes = fileNamesToDirsDict[location.name]["includes"]
                    for include, dirs in includes.items ():
                        locations = set ()
                        dirNotFound = False
                        for ind in range (len (dirs)) :
                            dirPos = str (location).find (dirs[ind])
                            if dirPos == -1:
                                dirNotFound = True
                                break
                        if not dirNotFound:
                            locations.add (location)

                        if dirNotFound and include in massSearchResultDict and len (massSearchResultDict[include]) > 0:
                            continue

                        print (".", end='', flush=True)

                        if (len (locations) > 1):
                            break

                        if include not in massSearchResultDict:
                            massSearchResultDict[include] = set ()
                        massSearchResultDict[include] = massSearchResultDict[include].union (locations)
        
        massSearchResultList = list ()
        for key, value in massSearchResultDict.items ():
            massSearchResultList.append ({"locations": value, "include" : key})
        return massSearchResultList


    def organizedPrint (self):

        parentSourcesDir = None
        while True: 
            if not parentSourcesDir:
                parentSourcesDir = self._file.parent
            else:
                parentSourcesDir = parentSourcesDir.parent
            if parentSourcesDir.name == "Sources" and (parentSourcesDir / "BuildNum.dat").is_file ():
                break

        strParentSourcesDir = str (parentSourcesDir)

        includeRegexString  = r"\s*#include\s*\"(.*)\"\s*"
        includeRegex   		= re.compile (includeRegexString)

        includes = set ()
        with open(self._file,'r') as fin:
            lines = fin.read ().splitlines()
            for line in lines:
                match = includeRegex.search (line)
                if match:
                    includes.add (match.group(1))

        print(f'Processing {len(includes)} includes', end='', flush=True)

        searchResults = self._massSearch (parentSourcesDir, includes)

        theDict = dict ()
        for searchResult in searchResults:
            subdirs = set ()
            for location in searchResult["locations"]:
                strLocation = str (location)
                subdir = strLocation [len(strParentSourcesDir) + 1:]
                subdir = subdir[0: subdir.find ("\\")]
                subdirs.add (subdir)

            subdirs = sorted (list (subdirs))

            if len (subdirs) == 1:
                subdir = list (subdirs)[0]
                if subdir not in theDict:
                    theDict[subdir] = set ()

                theDict[subdir].add (searchResult["include"])
            elif len (subdirs) > 1:
                toPrint = f"more Source Units found for {searchResult['include']} . Select which to use!"
                ind = 1
                for subdir in subdirs:
                    toPrint += f"\n{ind}  - {subdir}"
                    ind += 1
                toPrint += "\n"
                print (toPrint)

                

                try:
                    selected = int(input('Enter the number: '))
                    if selected not in range(1,len(subdirs) + 1):
                        print("Number out of range!")
                        selected = None
                except ValueError:
                    print("Not an integer!")
                    selected = None

                if selected is not None:
                    subdir = subdirs[selected - 1]
                    if subdir not in theDict:
                        theDict[subdir] = set ()
                    theDict[subdir].add (searchResult["include"])
                else:
                    moreLocationsDirName = f'MORE: {" or ".join (subdirs)}' 
                    if moreLocationsDirName not in theDict:
                        theDict[moreLocationsDirName] = set ()
                    theDict[moreLocationsDirName].add (searchResult["include"])
            else:
                toPrint = f"No Source Units found for {searchResult['include']} . Enter a name for it!"
                print (toPrint)

                try:
                    sourceUnitName = input('Enter the name: ')
                    if len (sourceUnitName) == 0:
                        sourceUnitName = None
                except Exception:
                    print("Error!")
                    sourceUnitName = None

                unknownDirName = sourceUnitName if sourceUnitName is not None else "???"
                if unknownDirName not in theDict:
                    theDict[unknownDirName] = set ()
                theDict[unknownDirName].add (searchResult["include"])
        
        print(f'DONE\n', flush=True)

        for key in theDict:
            foundName = None
            for item in theDict[key]:
                if self._file.stem.lower () == pathlib.Path (item).stem.lower ():
                    print (f"#include \"{item}\"")
                    print ("")
                    foundName = item
                    break
            if foundName:
                theDict[key].remove (foundName)
                break

        for key in sorted (theDict, key=str.casefold):
            if len (theDict[key]) > 0:
                print (f"// from {key}")
                for item in sorted (theDict[key]):
                    print (f"#include \"{item}\"")
                print ("")

        systemIncludeRegexString = r"\s*#include\s*\<(.*)\>\s*"
        systemIncludeRegex   		= re.compile (systemIncludeRegexString)
 
        systemIncludes = set ()

        with open(self._file,'r') as fin:
            lines = fin.read ().splitlines()
            for line in lines:
                match = systemIncludeRegex.search (line)
                if match:
                    systemIncludes.add (match.group(1))
        
        for systemInclude in sorted(list(systemIncludes)):
            print (f"#include <{systemInclude}>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--file', metavar="<SourceFileName>", required=True, help="C/C++ Source File")
    args = vars (parser.parse_args ())

    maybeFile = pathlib.Path (args['file'])

    if not maybeFile.is_file:
        sys.exit (1)

    cppIncludeOrganizer = CppIncludeOrganizer (maybeFile)
    cppIncludeOrganizer.organizedPrint ()
