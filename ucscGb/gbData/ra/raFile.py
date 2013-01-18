import sys, string
import re
from ucscGb.gbData.ordereddict import OrderedDict
from ucscGb.gbData.ra.raStanza import RaStanza
from ucscGb.gbData import ucscUtils
import collections

class RaFile(OrderedDict):
    '''
    Stores a Ra file in a set of entries, one for each stanza in the file.

    To make a RaFile, it is usually easiest to just pass it's path:
        rafile = ra.RaFile('kent/src/hg/.../wgEncodeSomeRaFile.ra')

    The data is read in and organized as a collection of stanzas. Ra files
    store the stanza by it's name, so to access a specific stanza, say:
        somestanza = rafile['wgEncodeSomeStanzaName']

    Once you have a stanza, you may want specific data about that stanza.
    Stanzas are, as ra files, organized as a collection of terms. Therefore
    to get the description of the stanza, we can say:
        somedescription = somestanza['description']

    You can also access a stanza's name from the stanza itself, since by the
    nature of ra files, the first key is it's name. Therefore for most ra
    files the following holds true:
        somestanza.name = somestanza['metaObject'] = 'wgEncodeSomeStanzaName'

    Although the above is useful if you want one thing, it's usually more
    helpful to be able to loop and query on the stanza. To add a term named
    'foobar' to every stanza in a ra file:
        for stanza in rafile.values():
            stanza['foobar'] = 'some value'

    Note that I iterated over values. It can also be useful to iterate over
    a stanza's keys:
        for key in rafile.keys():
            print key

    Note that ra files are order preserving. Added entries are appended to the
    end of the file. This allows you to print out a ra file easily:
        print rafile

    Most of the time you don't want to do something with all stanzas though,
    instead you want to filter them. The included filter method allows you to
    specify two functions (or lambda expressions). The first is the 'where'
    predicate, which must take in one stanza, and return true/false depending
    on whether you want to take that stanza. The second is the 'select'
    predicate, which takes in the stanza, and returns some subset or superset
    of the stanza as a list. Using filter is preferable to for loops where
    there are no side effects, or to filter data before iterating over it as
    opposed to using if statements in the loop. To get all stanzas with one
    experiment ID for instance, we would do something like this:
        stanzas = rafile.filter(lambda s: s['expId'] == '123', lambda s: s)

    Note that you don't have to ensure 'expId' is in the stanza, it will
    silently fail. Let's look at another example, say you want to find all
    stanza's with an geoSampleAccession that are also fastq's
        submittedfastqs = rafile.filter(
            lambda s: 'geoSampleAccession' in s and s['fileName'].endswith('.fastq'),
            lambda s: s)

    We don't always have to just return the stanza in the second parameter
    however. If we wanted to, for each stanza, return the file associated
    with that stanza, we could easily do that as well. This would return a
    simple list of the string filenames in a ra file:
        files = rafile.filter(lambda s: 1, lambda s: s['fileName'])

    Note that once again, we don't have to ensure 'fileName' exists. Also note
    that lambda s: 1 means always return true. Lambda expressions are always
    preferable to functions unless the expression would need to be reused
    multiple times. It is also best to reduce the set of stanzas as much as
    possible before operating over them.

    Filtering allows you to eliminate a lot of code.
    '''

    @property
    def filename(self):
        return self._filename
    
    def __init__(self, filePath=None, key=None):
        OrderedDict.__init__(self)
        if filePath != None:
            self.read(filePath, key)

    def read(self, filePath, key=None):
        '''
        Reads an rafile stanza by stanza, and internalizes it. Don't override
        this for derived types, instead override readStanza.
        '''
        self._filename = filePath
        file = open(filePath, 'r')

        #entry = None
        stanza = list()
        keyValue = ''

        reading = 1
        
        while reading:
            line = file.readline()
            if line == '':
                reading = 0
        
            line = line.strip()
            if len(stanza) == 0 and (line.startswith('#') or (line == '' and reading)):
                OrderedDict.append(self, line)
                continue

            if line != '':
                stanza.append(line)
            elif len(stanza) > 0:
                if keyValue == '':
                    keyValue, name, entry = self.readStanza(stanza, key)
                else:
                    testKey, name, entry = self.readStanza(stanza, key)
                    if entry != None and keyValue != testKey:
                        raise KeyError('Inconsistent Key ' + testKey)

                if entry != None:
                    if name != None or key == None:
                        if name in self:
                            raise KeyError('Duplicate Key ' + name)
                        self[name] = entry

                stanza = list()

        file.close()


    def readStanza(self, stanza, key=None):
        '''
        Override this to create custom stanza behavior in derived types.
        
        IN
        stanza: list of strings with keyval data
        key: optional key for selective key filtering. Don't worry about it

        OUT
        namekey: the key of the stanza's name
        nameval: the value of the stanza's name
        entry: the stanza itself
        '''
        entry = RaStanza()
        if entry.readStanza(stanza, key) == None:
            return None, None, None
        entry = RaStanza()
        val1, val2 = entry.readStanza(stanza, key)
        return val1, val2, entry


    def write(self, filename):
        file = open(filename, 'w')
        file.write(str(self))
        
    def iter(self):
        pass


    def iterkeys(self):
        for item in self._OrderedDict__ordering:
            if not(item.startswith('#') or item == ''):
                yield item


    def itervalues(self):
        for item in self._OrderedDict__ordering:
            if not (item.startswith('#') or item == ''):
                yield self[item]


    def iteritems(self):
        for item in self._OrderedDict__ordering:
            if not (item.startswith('#') or item == ''):
                yield item, self[item]
            else:
                yield [item]


    def append(self, item):
        OrderedDict.append(self, item)


    def filter(self, where, select):
        '''
        select useful data from matching criteria

        where: the conditional function that must be met. Where takes one
        argument, the stanza and should return true or false
        select: the data to return. Takes in stanza, should return whatever
        to be added to the list for that stanza.

        For each stanza, if where(stanza) holds, it will add select(stanza)
        to the list of returned entities. Also forces silent failure of key
        errors, so you don't have to check that a value is or is not in the stanza.
        '''

        ret = list()
        for stanza in self.itervalues():
            try:
                if where(stanza):
                    ret.append(select(stanza))
            except KeyError:
                continue
        return ret

    def filter2(self, where):
        '''
        select useful data from matching criteria
        Filter2 returns a Ra dictionary. Easier to use but more memory intensive.

        where: the conditional function that must be met. Where takes one
        argument, the stanza and should return true or false
        select: the data to return. Takes in stanza, should return whatever
        to be added to the list for that stanza.

        For each stanza, if where(stanza) holds, it will add select(stanza)
        to the list of returned entities. Also forces silent failure of key
        errors, so you don't have to check that a value is or is not in the stanza.
        '''
        ret = RaFile()
        for stanza in self.itervalues():
            try:
                if where(stanza):
                        ret[stanza.name] = stanza
            except KeyError:
                continue
        return ret

    def mergeRa(self, other):
        '''
        Input:
            Two RaFile objects
        Output:
            A merged RaFile

        Common stanzas and key-val pairs are collapsed into
        one with identical values being preserved,
        differences are marked with a >>> and <<<
        '''

        mergedKeys = ucscUtils.mergeList(list(self), list(other))
        selfKeys = set(self)
        otherKeys = set(other)
        newCommon = RaFile()
        p = re.compile('^\s*#')
        p2 = re.compile('^\s*$')
        for i in mergedKeys:
            if p.match(i) or p2.match(i):
                newCommon.append(i)
                continue
            if i not in selfKeys:
                newCommon[i] = other[i]
                continue
            if i not in otherKeys:
                newCommon[i] = self[i]
                continue
            if i in otherKeys and i in selfKeys:
                newStanza = RaStanza()
                selfStanzaKeys = set(self[i].iterkeys())
                otherStanzaKeys = set(other[i].iterkeys())
                stanzaKeys = ucscUtils.mergeList(list(self[i]), list(other[i]))
                for j in stanzaKeys:
                    if p.match(j):
                        newStanza.append(j)
                        continue
                    if j not in selfStanzaKeys:
                        newStanza[j] = other[i][j]
                        continue
                    if j not in otherStanzaKeys:
                        newStanza[j] = self[i][j]
                        continue
                    if j in selfStanzaKeys and j in otherStanzaKeys:
                        if self[i][j] == other[i][j]:
                            newStanza[j] = self[i][j]
                        else:
                            in_j = '>>>>>%s' % j
                            out_j = '<<<<<%s' % j
                            newStanza[out_j] = self[i][j]
                            newStanza[in_j] = other[i][j]
                newCommon[i] = newStanza
        return newCommon


    def summaryDiff(self, other):
        '''
        Input:
            RaFile object being compared.
        Output: RaFile with differences.

        Returns ***partial*** stanzas of ***anything*** different
        from the self dictionary compared to the other dictionary.
        For versatility, it only returns stanzas from the self Ra file. In other
        words, it returns the self dictionary lines that are either not present
        in or different from the other dictionary.

        To obtain full set of differences, run summaryDiff twice
        ra1 = this.summaryDiff(that)
        and
        ra2 = that.summaryDiff(this)
        '''
        this = RaFile()
        RetThis = RaFile()
        for stanza in self.itervalues():
            if stanza.name not in other.keys():
                RetThis[stanza.name] = stanza
            else:
                if stanza.difference(other[stanza.name]):
                    RetThis[stanza.name] = stanza.difference(other[stanza.name])
        return RetThis

    def changeSummary(self, otherRa):
        '''
        Input:
            Two RaFile objects
        Output:
            Dictionary showing differences between stanzas, list of added and dropeed stanzas
        '''
        retDict = collections.defaultdict(list)
        addList = set(self.iterkeys()) - set(otherRa.iterkeys())
        dropList = set(otherRa.iterkeys()) - set(self.iterkeys())
        common = set(self.iterkeys()) & set(otherRa.iterkeys())

        p = re.compile('^\s*#')
        for stanza in common:
            if p.match(stanza):
                continue
            for key in self[stanza]:
                if p.match(key):
                    continue
                if key in otherRa[stanza]:
                    if self[stanza][key] != otherRa[stanza][key]:
                        retDict[stanza].append("Changed %s from %s -> %s" %(key, otherRa[stanza][key], self[stanza][key]))
                else:
                    retDict[stanza].append("Added %s -> %s" %(key, self[stanza][key]))
            for key in otherRa[stanza]:
                if p.match(key):
                    continue
                if key not in self[stanza]:
                    retDict[stanza].append("Dropped %s -> %s" %(key, otherRa[stanza][key]))
        return retDict, addList, dropList

    def diffFilter(self, select, other):
        '''
        Input:
            Lambda function of desired comparison term
            RaFile object being compared.
        Output: RaFile with differences.

        Filter returns ***full*** stanzas of a ***select function*** from
        the self dictionary compared to the other dictionary. For
        versatility, it only returns stanzas from the self Ra file. In other
        words, it only returns self dictionary stanzas with the function term
        that are either not found in or different from the other
        dictionary.

        To obtain full set of differences, run diffFilter twice
        ra1 = this.diffFilter(select function, that)
        and
        ra2 = that.diffFilter(select function, this)
        '''
        this = RaFile()
        RetThis = RaFile()
        thisSelectDict = dict()
        thatSelectDict = dict()
        #Build 2 dict of stanzas to later compare line-by-line
        for stanza in self.itervalues():
            try:
                if select(stanza):
                    this[stanza.name] = stanza #'this' only records stanzas of the self dict
                    thisSelectDict[stanza.name] = select(stanza)
            except KeyError:
                continue
        for stanza in other.itervalues():
            #Exact code as filter2 but kept for clarity.
            try:
                if select(stanza):
                    thatSelectDict[stanza.name] = select(stanza)
            except KeyError:
                continue
        #Compare this and that dict
        for stanza in this.itervalues():
            if stanza.name not in thatSelectDict:
                RetThis[stanza.name] = stanza
            elif thisSelectDict[stanza.name] != thatSelectDict[stanza.name]:
                RetThis[stanza.name] = stanza
        return RetThis

    def updateDiffFilter(self, term, other):
        '''
        Replicates updateMetadata.
        Input:
            Term
            Other raFile

        Output:
            Merged RaFile
                Stanzas found in 'self' and 'other' that have the 'Term' in 'other'
                are overwritten (or inserted if not found) into 'self'. 
                Final merged dictionary is returned.
        '''
        ret = self
        common = set(self.iterkeys()) & set(other.iterkeys())
        for stanza in common:
            if term not in self[stanza] and term not in other[stanza]:
                continue
            if term in self[stanza] and term not in other[stanza]:
                    del ret[stanza][term]
                    continue
            if term in other[stanza]:
                #Remake stanza to keep order of terms
                tempStanza = RaStanza()
                tempStanza._name = stanza
                selfKeys = list(self[stanza].iterkeys())
                otherKeys = list(other[stanza].iterkeys())
                newOther = list()
                #filter out keys in other that aren't in self, or the term we're interested in
                for i in otherKeys:
                    if not i in selfKeys and i != term:
                        continue
                    else:
                        newOther.append(i)
                #merge self keylist and filtered other list
                masterList = ucscUtils.mergeList(newOther, selfKeys)
                for i in masterList:
                    if i == term:
                        tempStanza[i] = other[stanza][i]
                    else:
                        tempStanza[i] = self[stanza][i]
            ret[stanza] = tempStanza
        return ret

    def printTrackDbFormat(self):
        '''
        Converts a .ra file into TrackDb format.
        Returns a printable string.
        '''
        retstring = ""
        parentTrack = ""
        tier = 0
        commentList = []
        p = re.compile('^.*parent')
        p2 = re.compile('^.*subTrack')
        for stanza in self:
            if stanza == "":
                if commentList:
                    for line in commentList:
                        for i in range(tier):
                            retstring += "    "
                        retstring += line + "\n"
                    commentList = []
                    retstring += "\n"
                continue
            if stanza.startswith("#"):
                commentList.append(stanza)
                continue
            keys = self[stanza].keys()
            parentKey = "NOKEYFOUND"
            for key in keys:
                if p.search(key):
                    parentKey = key
                if p2.search(key):
                    parentKey = key
            if parentKey in keys:
                if parentTrack not in self[stanza][parentKey] or parentTrack == "":
                    parentTrack = self[stanza]['track']
                    tier = 1
                else:
                    tier = 2
            if commentList:
                for line in commentList:
                    for i in range(tier):
                        retstring += "    "
                    retstring += line + "\n"
                commentList = []
            for line in self[stanza]:
                for i in range(tier):
                    retstring += "    "
                if line.startswith("#"):
                    retstring += line + "\n"
                else:
                    retstring += line + " " + self[stanza][line] + "\n"
            retstring += "\n"
        return retstring

    def __str__(self):
        str = ''
        for item in self.iteritems():
            if len(item) == 1:
                str += item[0].__str__() + '\n'
            else:
                str += item[1].__str__() + '\n'
        return str #.rsplit('\n', 1)[0]



