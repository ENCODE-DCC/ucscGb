import subprocess
import pipes

from ucscGb.qa.tables.genePredQa import GenePredQa
from ucscGb.qa.tables.tableQa import TableQa
from ucscGb.qa.tables.pslQa import PslQa
from ucscGb.qa.tables.positionalQa import PositionalQa
from ucscGb.qa.tables.pointerQa import PointerQa

def getTrackType(db, table):
    """Looks for a track type via tdbQuery."""
    cmd = ["tdbQuery", "select type from " + db + " where track='" + table +
           "' or table='" + table + "'"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmdout, cmderr = p.communicate()
    if p.returncode != 0:
        # keep command arguments nicely quoted
        cmdstr = " ".join([pipes.quote(arg) for arg in cmd])
        raise Exception("Error from: " + cmdstr + ": " + cmderr)
    if cmdout:
        tableType = cmdout.split()[1]
    else:
        tableType = None
    return tableType

pslTypes = frozenset(["psl"])
genePredTypes = frozenset(["genePred"])
otherPositionalTypes = frozenset(["axt", "bed", "chain", "clonePos", "ctgPos", "expRatio", "maf",
                                  "netAlign", "rmsk", "sample", "wigMaf", "wig", "bedGraph",
                                  "chromGraph", "factorSource", "bedDetail", "pgSnp", "altGraphX",
                                  "ld2", "bed5FloatScore", "bedRnaElements", "broadPeak", "gvf",
                                  "narrowPeak", "peptideMapping"])
pointerTypes = frozenset(["bigWig", "bigBed", "bam", "vcfTabix"])

def tableQaFactory(db, table, reporter, sumTable):
    """Returns tableQa object according to trackDb track type.""" 
    tableType = getTrackType(db, table)
    if not tableType:
        return TableQa(db, table, tableType, reporter, sumTable)
    elif tableType in pslTypes:
        return PslQa(db, table, tableType, reporter, sumTable)
    elif tableType in genePredTypes:
        return GenePredQa(db, table, tableType, reporter, sumTable)
    elif tableType in otherPositionalTypes:
        return PositionalQa(db, table, tableType, reporter, sumTable)
    elif tableType in pointerTypes:
        return PointerQa(db, table, tableType, reporter, sumTable)
    else:
        raise Exception(db + table + " has unknown track type " + tableType)

