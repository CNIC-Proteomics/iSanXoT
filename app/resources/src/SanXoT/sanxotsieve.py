import pdb
import getopt
import stats
import sanxot
import sys
import os
import gc
from time import strftime
# begin: jmrc
import math
import pandas as pd
import numpy as np
# end: jmrc

import pprint
pp = pprint.PrettyPrinter(indent=4)

# begin: jmrc
# TEMPORAL/DELETE!!
# INFO_PATH = ""
# end: jmrc

#######################################################

class mode:
    onlyOne = 1
    onePerHigher = 2
    byPercentage = 3
    
    def desc(x):
        if x == 1: return 'onlyOne'
        elif x == 2: return 'onePerHigher'
        elif x == 3: return 'byPercentage'
    
#------------------------------------------------------

class higherResult:
	def __init__(self, id2 = None, Xj = None, Vj = None):
		self.id2 = id2
		self.Xj = Xj
		self.Vj = Vj
		
#------------------------------------------------------

class lowerResult:
	def __init__(self, id1 = None, XiXj = None, Wj = None):
		self.id1 = id1
		self.XiXj = XiXj
		self.Wj = Wj
		
#------------------------------------------------------

class statsResult:
	# statsResult.id2 --> higher level identifier
	# statsResult.Xj --> higher level X
	# statsResult.Vj --> higher level V
	# statsResult.id1 --> lower level identifier
	# statsResult.Xi --> lower level X (log2Ratio)
	# statsResult.Vi --> lower level weight without adding variance
	# statsResult.Wij --> lower level weight including variance
	# statsResult.nij --> lower level number of elements within the higher level element
	# statsResult.Zij --> distance in sigmas
	# statsResult.FDRij --> false discovery rate
	def __init__(self, id2 = None, Xj = None, Vj = None, id1 = None, Xi = None, Vi = None, Wij = None, nij = None, Zij = None, FDRij = None):
		self.id2 = id2
		self.Xj = Xj
		self.Vj = Vj
		self.id1 = id1
		self.Xi = Xi
		self.Vi = Vi
		self.Wij = Wij
		self.nij = nij
		self.Zij = Zij
		self.FDRij = FDRij

#------------------------------------------------------
# begin: jmrc

# Function that converts the list of statsResult To DataFrame
def convert_outStats_To_DataFrame(outStats):
    
    # create a list of lists from the statsResults
    ss = [ [s.id2,s.Xj,s.Vj,s.id1,s.Xi,s.Vi,s.Wij,s.nij,s.Zij,s.absZij,s.FDRij,s.tags] for s in outStats ]
    
    # create the dataframe from the list of lists
    newOutStats = pd.DataFrame(ss, columns=['id2','Xj','Vj','id1','Xi','Vi','Wij','nij','Zij','absZij','FDRij','tags'])
    
    return newOutStats

# end: jmrc

#------------------------------------------------------

def detectRelationWithLeastFDR(statsData, FDRLimit = 0.01, modeUsed = mode.onlyOne):

	# modes
	# mode.onlyOne -> removes the relation with least FDR, if it has FDR < FDRLimit
	# mode.onePerHigher -> removes one relation for each higher level element, if it has FDR < FDRLimit
	#***
	
	relationsToRemove = []

	sortedStats = stats.sortByInstance(statsData, "FDRij", isDescendent = False)[::-1]

	if modeUsed == mode.onlyOne:
		leastFDR = sys.float_info.max
		leastFDRRow = []
		for statsRow in sortedStats:
			if statsRow.FDRij < leastFDR:
				leastFDR = statsRow.FDRij
				leastFDRRow = statsRow
		if leastFDRRow != []:
			if leastFDRRow.FDRij < FDRLimit:
				newRelationToRemove = [leastFDRRow.id2, leastFDRRow.id1]
				relationsToRemove = [newRelationToRemove]
			
	if modeUsed == mode.onePerHigher:
		for statsRow in sortedStats:
			# begin: jmrc
			# if statsRow.FDRij < FDRLimit:
			if isinstance(statsRow.FDRij, float) and statsRow.FDRij < FDRLimit:
			# end: jmrc
				higherSelection = stats.filterByElement(relationsToRemove, statsRow.id2)
				if len(higherSelection) == 0:
					# add new outlier relation
					newRelationToRemove = [statsRow.id2, statsRow.id1, statsRow.FDRij, abs(statsRow.Zij)]
					relationsToRemove.append(newRelationToRemove)
				else:
					# warning!! none should have len(higherSelection) > 1
					if len(higherSelection) == 1:
						# check which has the least FDRij, or the biggest |Zij| if FDRij == 0
						if (statsRow.FDRij < higherSelection[0][2] or (statsRow.FDRij == 0 and abs(statsRow.Zij) > higherSelection[0][3])):
							newRelationToRemove = [statsRow.id2, statsRow.id1, statsRow.FDRij, abs(statsRow.Zij)]
							relationsToRemove.remove(higherSelection[0])
							relationsToRemove.append(newRelationToRemove)

		relationsToRemove = stats.extractColumns(relationsToRemove, 0, 1)
	
	return relationsToRemove

# begin: jmrc
def detectRelationWithLeastFDR2(statsDataUnderFDR, modeUsed = mode.onlyOne, percUsed = 10):

	# modes
	# mode.onePerHigher -> removes one relation for each higher level element, if it has FDR < FDRLimit
    # mode.byPercentage -> removes the number of outliers based on the percentage of higher elements
	#***	
	
    # From the a list of relationships (lower-higher), mask the first N rows based on the given percentage
    # capture the outlier relationships between lower-higher integrations.
    def mask_first_outliers_by_percentage(x):
        # Return an array of zeros with the same shape and type as a given array
        relations = np.zeros_like(x)
        # Get the number of relationships (nij under FDR)
        num_relations_underFDR = len(relations)
        # Get the number of total relationships (nij)
        # The values have to be unique in the series.
        # If there is not value, then we return 0. If there are multiple values, we return the minimum value.
        num_relations_total = 0 if len(x.unique()) == 0 else x.unique()[0] if len(x.unique()) == 1 else x.min()
        # Get the number of relationships based on the given percentage.
        # If the maximum number is non-integer, there is no need to round it.
        # For example, if we have 47 elements, the maximum number would be 4.7, 
        # so we can eliminate up to 4 but cannot eliminate 5. We used "math.floor"
        num_masks = math.floor(num_relations_total * (percUsed/100))
        # At least one relationship is masked.
        # If the number of masked relationships is less than 1, retrieve one.
        num_masks = 1 if num_masks < 1 else num_masks
        # The number of masks can not be higher than the number of relationships (nij under FDR)
        num_masks = num_relations_underFDR if num_masks > num_relations_underFDR else num_masks
        # These integrations will be masked to true. The rest will be removed.
        # Assigns the first n elements of a list (relationships) with a value zero (false)
        relations[:num_masks] = [1] * num_masks
        # return
        return relations
        
    # Adaptation of the old algorithm that removes one relationship per integration.
    # To achieve this, we set the used percentage as 0. Therefore, we remove only one outlier per integration.
    if modeUsed == mode.onePerHigher:
        percUsed = 0
    
    # begin_DEPRECATED: jmrc
    # # Count the number of lower level for each higher level
    # count_lowers = statsDataUnderFDR.groupby('id2')['id1'].count()
    # count_lowers = count_lowers.rename('nij_after_FDR')
    # # Merge the number of lowe leves into global table
    # statsDataUnderFDR = statsDataUnderFDR.merge(count_lowers, left_on='id2', right_on='id2')
    # end_DEPRECATED: jmrc
    
    # Sort by higher level, FDR and absolute Z:
    # The FDR values are ascending. Thus, lower values are at the top.
    # The absZij values are descending. Thus, higher values are at the top.
    statsDataUnderFDR = statsDataUnderFDR.sort_values(['id2','FDRij','absZij'], ascending=[True,True,False])
    
    # the integrations are grouped by the higher level
    # for each group, mask the first N relationships based on the given percentage
    # remember how the rows have been sorted
    mask = statsDataUnderFDR.groupby(['id2'])['nij'].transform(mask_first_outliers_by_percentage).astype(bool)
    relationsToRemove = statsDataUnderFDR.loc[mask]

    # Retrieve a list with the relationships
    relationsToRemove = relationsToRemove[['id2','id1']].values.tolist()

    return relationsToRemove

# end: jmrc

#------------------------------------------------------

def detectOutliers(statsData, FDRLimit = 0.01):
		
	relationUnderFDR = []
	
	for row in statsData:
		# begin: jmrc
		# if row.FDRij < FDRLimit:
		#	relationUnderFDR.append([row.id2, row.id1])
		if isinstance(row.FDRij, float) and not math.isnan(row.FDRij):
			if row.FDRij < FDRLimit:
				relationUnderFDR.append([row.id2, row.id1])
		# end: jmrc

	return relationUnderFDR

# begin: jmrc
def detectOutliers2(statsData, FDRLimit = 0.01):
	
	# discard the records that has been excluded
	statsData = statsData[statsData['FDRij'] != 'excluded']

	# filter by the given FDR limit
	statsDataUnderFDR = statsData[statsData['FDRij'] < FDRLimit]
    
	return statsDataUnderFDR
# end: jmrc
	
#------------------------------------------------------

def removeOutliers(relations, relationsToRemove):
	
	# note that here outliers are removed independently of their tags
	# just removing all rows where id1 and id2 coincides
	
	newRelations = relations[:]

	if len(relationsToRemove) > 0:
		for eachRelation in relationsToRemove:
			#
			# while eachRelation in newRelations:
				# newRelations.remove(eachRelation)
			#
			# above previous code was simpler, but was buggy
			# as it was not removing relationsToRemove including tags
			# now, instead of removing eachRelation, it removes newRelations[i]
			# keep this for future reference
			i = 0
			while i < len(newRelations):
				if newRelations[i][0] == eachRelation[0] and newRelations[i][1] == eachRelation[1]:
					newRelations.remove(newRelations[i])
				else:
					i += 1
		
	return newRelations
	
#------------------------------------------------------

def getRelationsWithoutOutliers(data, relations, variance, FDRLimit = 0.01, modeUsed = mode.onlyOne, removeDuplicateUpper = False):

	# this method is included only for backward compatibility
	
	newRelations = relations[:]
	removedRelations = []
	startingLoop = True
	outliers = []
	while len(outliers) > 0 or startingLoop:
		
		startingLoop = False
		
		newRelations = removeOutliers(newRelations, outliers)
		removedRelations.extend(outliers)
		newVariance, dummyHigher, newStats, dummyLower, logResults, success = \
						sanxot.integrate(data = data,
								relations = newRelations,
								varianceSeed = variance,
								forceParameters = True,
								removeDuplicateUpper = removeDuplicateUpper)
		
		totOutliers = detectOutliers(newStats, FDRLimit = FDRLimit)
		outliers = detectRelationWithLeastFDR(newStats, FDRLimit = FDRLimit, modeUsed = modeUsed)
		
		print()
		if len(outliers) > 0:
			print("%i outliers found, removing %i of them, and recalculating..." % (len(totOutliers), len(outliers)))
		else:
			print("No outliers found at %f FDR." % FDRLimit)
			print()
		
		dummyHigher = []
		newStats = []
		dummyLower = []
		totOutliers = []
		gc.collect()
			
	return newRelations, removedRelations, logResults

#------------------------------------------------------

def tagRelationsWithoutOutliers(data, relations, variance, FDRLimit = 0.01, modeUsed = mode.onlyOne, removeDuplicateUpper = False, tags = "!out", outlierTag = "out", logicOperatorsAsWords = False):

	newRelations = relations[:]
	
	removedRelations = []
	startingLoop = True
	outliers = []
	while len(outliers) > 0 or startingLoop:
		
		startingLoop = False
		
		newRelations = stats.addTagToRelations(newRelations, outliers, outlierTag)

		removedRelations.extend(outliers)
		newVariance, dummyHigher, newStats, dummyLower, logResults, success = \
						sanxot.integrate(data = data,
								relations = newRelations,
								varianceSeed = variance,
								forceParameters = True,
								removeDuplicateUpper = removeDuplicateUpper,
								tags = tags,
								logicOperatorsAsWords = logicOperatorsAsWords)
		
		totOutliers = detectOutliers(newStats, FDRLimit = FDRLimit)
		outliers = detectRelationWithLeastFDR(newStats, FDRLimit = FDRLimit, modeUsed = modeUsed)
		
		print()
		if len(outliers) > 0:
			print("%i outliers found, tagging %i of them as 'out', and recalculating..." % (len(totOutliers), len(outliers)))
		else:
			print("No outliers found at %f FDR." % FDRLimit)
			print()
		
		dummyHigher = []
		newStats = []
		dummyLower = []
		totOutliers = []
		gc.collect()
			
	return newRelations, removedRelations, logResults

# begin: jmrc
def tagRelationsWithoutOutliers2(data, relations, variance, FDRLimit = 0.01, modeUsed = mode.onlyOne, percUsed = None, removeDuplicateUpper = False, tags = "!out", outlierTag = "out", logicOperatorsAsWords = False):
    
    import timeit	
    starttime = timeit.default_timer()
    
    newRelations = relations[:]
	
    removedRelations = []
    startingLoop = True
    outliers = []
    statsDataOutliers = pd.DataFrame()

    # print(f"T0: {starttime}")
    count = 1
    while len(outliers) > 0 or startingLoop:
		
        sttime = timeit.default_timer()
        newRelations = stats.addTagToRelations2(newRelations, outliers, outlierTag)
        # print(f"T1: {timeit.default_timer() - sttime}")
        
        sttime = timeit.default_timer()
        removedRelations.extend(outliers)
        # print(f"T2: {timeit.default_timer() - sttime}")
		
        sttime = timeit.default_timer()
        newVariance, dummyHigher, newStats, dummyLower, logResults, success = \
                        sanxot.integrate(data = data,
								relations = newRelations,
								varianceSeed = variance,
								forceParameters = True,
								removeDuplicateUpper = removeDuplicateUpper,
								tags = tags,
								logicOperatorsAsWords = logicOperatorsAsWords)
        # print(f"T3: {timeit.default_timer() - sttime}")
        
        # ---
        # begin_DEPRECATED: jmrc Used to compare with the old results
        # sttime = timeit.default_timer()
        # totOutliers = detectOutliers(newStats, FDRLimit = FDRLimit)
        # print(f"T4: {timeit.default_timer() - sttime}")
        
        # sttime = timeit.default_timer()
        # outliers = detectRelationWithLeastFDR(newStats, FDRLimit = FDRLimit, modeUsed = modeUsed)
        # print(f"T5: {timeit.default_timer() - sttime}")
        
        # print()
        # if len(outliers) > 0:
        #     print("%i outliers found, tagging %i of them as 'out', and recalculating..." % (len(totOutliers), len(outliers)))
        # else:
        #     print("No outliers found at %f FDR." % FDRLimit)
        #     print()
        # end_DEPRECATED: jmrc Used to compare with the old results
        # ---
        
        sttime = timeit.default_timer()
        newStats2 = convert_outStats_To_DataFrame(newStats)
        # print(f"T6: {timeit.default_timer() - sttime}")
		
        # filter by FDR and remove the 'excluded' integrations
        sttime = timeit.default_timer()
        statsDataUnderFDR = detectOutliers2(newStats2, FDRLimit = FDRLimit)
        # print(f"T7: {timeit.default_timer() - sttime}")
        
        # detect the outliers
        sttime = timeit.default_timer()
        outliers = detectRelationWithLeastFDR2(statsDataUnderFDR, modeUsed = modeUsed, percUsed = percUsed)
        # print(f"T8: {timeit.default_timer() - sttime}")
		
        print()
        if len(outliers) > 0:
            print("%i outliers found, tagging %i of them as 'out', and recalculating..." % (len(statsDataUnderFDR.index), len(outliers)), flush=True)

            # begin: jmrc
            # TEMPORAL/DELETE!!
            # df = pd.DataFrame(outliers)
            # ofile = os.path.join(INFO_PATH,f"outliers_loop_{count}.tsv")
            # df.to_csv(ofile, sep="\t", index=False)
            # ofile2 = os.path.join(INFO_PATH,f"statsData_loop_{count}.tsv")
            # statsDataUnderFDR.to_csv(ofile2, sep="\t", index=False)
            # count += 1
            # end: jmrc
            
        else:
            print("No outliers found at %f FDR." % FDRLimit, flush=True)
            print()		

        startingLoop = False

        dummyHigher = []
        newStats = []
        dummyLower = []
        totOutliers = []
        gc.collect()
			
    return newRelations, removedRelations, logResults

#------------------------------------------------------
	
def printHelp(version = None, advanced = False):

	print("""
SanXoTSieve %s is a program made in the Jesus Vazquez Cardiovascular
Proteomics Lab at Centro Nacional de Investigaciones Cardiovasculares, used to
perform automatical removal of lower level outliers in an integration
performed using the SanXoT integrator.

SanXoTSieve needs the two input files of a SanXoT integration
(see SanXoT's help): commands -d and -r, respectively.

And the resulting variance of the integration that has been performed:
commands -V (assigned from the info file of the integration.) or -v.

... and delivers two output files:

     * a new relations file (by default suffixed "_tagged"), which is
     identical to the original relations file, but tagging in the third column
     the relations marked as outlier.
     
     * the log file.
     
Usage: sanxotsieve.py -d[data file] -r[relations file] -V[info file] [OPTIONS]""" % version)

	if advanced:
		print("""
   -h, --help          Display basic help and exit.
   -H, --advanced-help Display this help and exit.
   -a, --analysis=string
                       Use a prefix for the output files. If this is not
                       provided, then the prefix will be garnered from the data
                       file.
   -b, --no-verbose    Do not print result summary after executing.
   -d, --datafile=filename
                       Data file with identificators of the lowel level in the
                       first column, measured values (x) in the second column,
                       and weights (v) in the third column.
   -D, --removeduplicateupper
                       When merging data with relations table, remove duplicate
                       higher level elements (not removed by default).
   -f, --fdrlimit=float
                       Use an FDR limit different than 0.01 (1%).
   -L, --infofile=filename
                       To use a non-default name for the log file.
   -n, --newrelfile=filename
                       To use a non-default name for the relations file
                       containing the tagged outliers.
   -o, --outlierrelfile=filename
                       To use a non-default name for the relations responsible
                       of outliers (note that outlier relations are only saved
                       when the --oldway option is active)
   -p, --place, --folder=foldername
                       To use a different common folder for the output files.
                       If this is not provided, the folder used will be the
                       same as the input folder.
   -r, --relfile, --relationsfile=filename
                       Relations file, with identificators of the higher level
                       in the first column, and identificators of the lower
                       level in the second column.
   -c, --perc-used     Remove the percentage of outliera per cycle.
                       Default is 10(%).
   -v, --var, --varianceseed=double
                       Variance used in the concerning integration.
                       Default is 0.001.
   -V, --varfile=filename
                       Get the variance value from a text file. It must contain
                       a line (not more than once) with the text
                       "Variance = [double]". This suits the info file from a
                       previous integration (see -L in SanXoT).
   --oldway            Do it the old way: instead of tagging, create two
                       separated relation files, with and without outliers.
   --outliertag=string To select a non-default tag for outliers (default: out)
   --tags=string       To define a tag to distinguish groups to perform the
                       integration. The tag can be used by inclusion, such as
                            --tags="mod"
                       or by exclusion, putting first the "!" symbol, such as
                            --tags="!out"
                       Tags should be included in a third column of the
                       relations file. Note that the tag "!out" for outliers is
                       implicit.
                       Different tags can be combined using logical operators
                       "and" (&), "or" (|), and "not" (!), and parentheses.
                       Some examples:
                            --tags="!out&mod"
                            --tags="!out&(dig0|dig1)"
                            --tags="(!dig0&!dig1)|mod1"
                            --tags="mod1|mod2|mod3"
""")
	else:
		print("""
Use -H or --advanced-help for more details.""")

	return
	
#------------------------------------------------------

def main(argv):
	
	# begin: jmrc
	version = "v0.20"
	# end: jmrc
	analysisName = ""
	analysisFolder = ""
	varianceSeed = 0.001
	FDRLimit = 0.01
	varianceSeedProvided = False
	removeDuplicateUpper = False
	tags = "!out"
	outlierTag = "out"
	logicOperatorsAsWords = False
	dataFile = ""
	relationsFile = ""
	newRelFile = ""
	removedRelFile = ""
	defaultDataFile = "data"
	defaultRelationsFile = "rels"
	defaultTaggedRelFile = "tagged"
	defaultNewRelFile = "cleaned"
	defaultRemovedRelFile = "outliers"
	defaultOutputInfo = "infoFile"
	infoFile = ""
	varFile = ""
	defaultTableExtension = ".tsv"
	defaultTextExtension = ".txt"
	defaultGraphExtension = ".png"
	verbose = True
	oldWay = False # instead of tagging outliers, separating relations files, the old way
	# begin: jmrc
	modeUsed = mode.onePerHigher
	percUsed = None
# 	modeUsed = mode.byPercentage
# 	percUsed = 10
	# end: jmrc
	logList = [["SanXoTSieve " + version], ["Start: " + strftime("%Y-%m-%d %H:%M:%S")]]

	try:
		opts, args = getopt.getopt(argv, "a:p:v:d:r:n:L:V:c:f:ubDhH", ["analysis=", "folder=", "varianceseed=", "datafile=", "relfile=", "newrelfile=", "outlierrelfile=", "infofile=", "varfile=", "perc-used=", "fdrlimit=", "one-to-one", "no-verbose", "randomise", "removeduplicateupper", "help", "advanced-help", "tags=", "outliertag=", "oldway", "word-operators"])
	except getopt.GetoptError:
		logList.append(["Error while getting parameters."])
		stats.saveFile(infoFile, logList, "INFO FILE")
		sys.exit(2)
	
	if len(opts) == 0:
		printHelp(version)
		sys.exit()

	for opt, arg in opts:
		if opt in ("-a", "--analysis"):
			analysisName = arg
		if opt in ("-p", "--place", "--folder"):
			analysisFolder = arg
		if opt in ("-v", "--var", "--varianceseed"):
			varianceSeed = float(arg)
			varianceSeedProvided = True
		elif opt in ("-d", "--datafile"):
			dataFile = arg
		elif opt in ("-r", "--relfile", "--relationsfile"):
			relationsFile = arg
		elif opt in ("-n", "--newrelfile"):
			newRelFile = arg
		elif opt in ("-o", "--outlierrelfile"):
			removedRelFile = arg
		elif opt in ("-L", "--infofile"):
			infoFile = arg
		elif opt in ("-V", "--varfile"):
			varFile = arg
		elif opt in ("-c", "--perc-used"):
			modeUsed = mode.byPercentage
			percUsed = int(arg)
		elif opt in ("-b", "--no-verbose"):
			verbose = False
		elif opt in ("--oldway"):
			oldWay = True
		elif opt in ("-f", "--fdrlimit"):
			FDRLimit = float(arg)
		elif opt in ("-D", "--removeduplicateupper"):
			removeDuplicateUpper = True
		elif opt in ("--tags"):
			if arg.strip().lower() != "!out":
				tags = "!out&(" + arg + ")"
		elif opt in ("--word-operators"):
			logicOperatorsAsWords = True
		elif opt in ("--outliertag"):
			outlierTag = "out"
		elif opt in ("-h", "--help"):
			printHelp(version)
			sys.exit()
		elif opt in ("-H", "--advanced-help"):
			printHelp(version, advanced = True)
			sys.exit()
	
# REGION: FILE NAMES SETUP
			
	if len(analysisName) == 0:
		if len(dataFile) > 0:
			analysisName = os.path.splitext(os.path.basename(dataFile))[0]
		else:
			analysisName = defaultAnalysisName

	if len(os.path.dirname(analysisName)) > 0:
		analysisNameFirstPart = os.path.dirname(analysisName)
		analysisName = os.path.basename(analysisName)
		if len(analysisFolder) == 0:
			analysisFolder = analysisNameFirstPart
			
	if len(dataFile) > 0 and len(analysisFolder) == 0:
		if len(os.path.dirname(dataFile)) > 0:
			analysisFolder = os.path.dirname(dataFile)

	# input
	if len(dataFile) == 0:
		dataFile = os.path.join(analysisFolder, analysisName + "_" + defaultDataFile + defaultTableExtension)
		
	if len(os.path.dirname(dataFile)) == 0 and len(analysisFolder) > 0:
		dataFile = os.path.join(analysisFolder, dataFile)
	
	if len(os.path.dirname(varFile)) == 0 and len(os.path.basename(varFile)) > 0:
		varFile = os.path.join(analysisFolder, varFile)
		
	if len(varFile) > 0 and not varianceSeedProvided:
		varianceSeed, varianceOk = stats.extractVarianceFromVarFile(varFile, verbose = verbose, defaultSeed = varianceSeed)
		if not varianceOk:
			logList.append(["Variance not found in text file."])
			stats.saveFile(infoFile, logList, "INFO FILE")
			sys.exit()
	
	if len(relationsFile) == 0:
		relationsFile = os.path.join(analysisFolder, analysisName + "_" + defaultRelationsFile + defaultTableExtension)
	
	if len(os.path.dirname(relationsFile)) == 0:
		relationsFile = os.path.join(analysisFolder, relationsFile)
	
	# output
	if len(newRelFile) == 0:
		if oldWay: # suffix: "cleaned"
			newRelFile = os.path.join(analysisFolder, analysisName + "_" + defaultNewRelFile + defaultTableExtension)
		else: # suffix: "tagged"
			newRelFile = os.path.join(analysisFolder, analysisName + "_" + defaultTaggedRelFile + defaultTableExtension)
	
	if len(removedRelFile) == 0:
		removedRelFile = os.path.join(analysisFolder, analysisName + "_" + defaultRemovedRelFile + defaultTableExtension)
	
	if len(os.path.dirname(newRelFile)) == 0:
		newRelFile = os.path.join(analysisFolder, newRelFile)
		
	if len(os.path.dirname(removedRelFile)) == 0:
		removedRelFile = os.path.join(analysisFolder, removedRelFile)
	
	if len(infoFile) == 0:
		infoFile = os.path.join(analysisFolder, analysisName + "_" + defaultOutputInfo + defaultTextExtension)
	
	logList.append(["Variance seed = " + str(varianceSeed)])
	logList.append(["Input data file: " + dataFile])
	logList.append(["Input relations file: " + relationsFile])
	if oldWay:
		logList.append(["Output relations file without outliers: " + newRelFile])
		logList.append(["Output relations file with outliers only: " + removedRelFile])
		logList.append(["Removing duplicate higher level elements: " + str(removeDuplicateUpper)])
		logList.append(["OldWay option activated: outliers are removed instead of tagged"])
	else:
		logList.append(["Relations file tagging outliers: " + newRelFile])
		logList.append(["Tags to filter relations: " + tags])
		logList.append(["Tag used for outliers: " + outlierTag])
		logList.append(["Mode used for the detection of outliers: " + mode.desc(modeUsed)])
		if modeUsed == mode.byPercentage:
			logList.append(["Percentage used for the detection of outliers: " + str(percUsed)])

	# pp.pprint(logList)
	# sys.exit()

    # begin: jmrc
    # TEMPORAL/DELETE!!
# 	global INFO_PATH
# 	INFO_PATH = os.path.dirname(infoFile)
    # end: jmrc

# END REGION: FILE NAMES SETUP
	
	relations = stats.loadRelationsFile(relationsFile)
	data = stats.loadInputDataFile(dataFile)
	
	if oldWay:
		# only for backward compatibility. Note that tags are not supported
		newRelations, removedRelations, logResults = \
								getRelationsWithoutOutliers(data,
										relations,
										varianceSeed,
										FDRLimit = FDRLimit,
										modeUsed = modeUsed,
										removeDuplicateUpper = removeDuplicateUpper)
	else:
		# begin: jmrc
# 		newRelations, removedRelations, logResults = \
# 								tagRelationsWithoutOutliers(data,
# 										relations,
# 										varianceSeed,
# 										FDRLimit = FDRLimit,
# 										modeUsed = modeUsed,
# 										removeDuplicateUpper = removeDuplicateUpper,
# 										tags = tags,
# 										outlierTag = outlierTag,
# 										logicOperatorsAsWords = logicOperatorsAsWords)
		newRelations, removedRelations, logResults = \
								tagRelationsWithoutOutliers2(data,
										relations,
										varianceSeed,
										FDRLimit = FDRLimit,
										modeUsed = modeUsed,
										percUsed = percUsed,
										removeDuplicateUpper = removeDuplicateUpper,
										tags = tags,
										outlierTag = outlierTag,
										logicOperatorsAsWords = logicOperatorsAsWords)
		# end: jmrc
	if oldWay:
		stats.saveFile(newRelFile, newRelations, "idsup\tidinf")
	else:
		stats.saveFile(newRelFile, newRelations, "idsup\tidinf\ttags")
		
	stats.saveFile(infoFile, logList, "INFO FILE")
	
	if oldWay:
		stats.saveFile(removedRelFile, removedRelations, "idsup\tidinf")
	
#######################################################

if __name__ == "__main__":
    # begin: jmrc
    # get the name of script with the type of step (if apply)
    script_name = os.path.splitext( os.path.basename(__file__) )[0].upper()
    if '-a' in sys.argv:
        i = sys.argv.index('-a')
        s = sys.argv[i+1]
        s = s.upper()+'_' if not s.startswith('-') else ''
        script_name = s + script_name
    print( "{} - {} - {} - start script : {}".format(script_name, os.getpid(), strftime("%m/%d/%Y %H:%M:%S %p"), " ".join([x for x in sys.argv])) )
    # end: jmrc

    main(sys.argv[1:])

    # begin: jmrc
    print( "{} - {} - {} - end script".format(script_name, os.getpid(), strftime("%m/%d/%Y %H:%M:%S %p")) )
    # end: jmrc
