#!/usr/bin/env python

#Copyright (C) 2011 by Glenn Hickey
#
#Released under the MIT license, see LICENSE.txt
#!/usr/bin/env python

"""Create the multi_cactus xml and directory structure from a workflow template
""" 
import os
from optparse import OptionParser
import xml.etree.ElementTree as ET
import copy

from sonLib.bioio import newickTreeParser
from sonLib.bioio import printBinaryTree
from cactus.progressive.multiCactusProject import MultiCactusProject
from cactus.progressive.multiCactusTree import MultiCactusTree
from cactus.progressive.experimentWrapper import ExperimentWrapper

def createMCProject(tree, options):
    mcTree = MultiCactusTree(tree, options.subtreeSize)
    mcTree.nameUnlabeledInternalNodes(options.prefix)
    mcTree.computeSubtreeRoots()
    mcProj = MultiCactusProject()
    mcProj.mcTree = mcTree
    for name, node in mcProj.mcTree.subtreeRoots.items():
        expPath = "%s/%s/%s_experiment.xml" % (options.path, name, name)
        mcProj.expMap[name] = os.path.abspath(expPath)
    return mcProj

# Make the subdirs for each subproblem:  name/ and name/name_DB
# and write the experiment files
# and copy over a config with updated reference field
def createFileStructure(mcProj, expTemplate, options):
    os.makedirs(options.path)
    mcProj.writeXML(os.path.join(options.path, "%s_project.xml" % options.name))
    baseConfig = expTemplate.getConfigPath()
    baseConfigXML = ET.parse(baseConfig).getroot()
    seqMap = expTemplate.seqMap
    portOffset = 0
    for name, expPath in mcProj.expMap.items():
        path = os.path.join(options.path, name)
        seqMap[name] = os.path.join(path, "%s_reference.fa" % name)
    for name, expPath in mcProj.expMap.items():
        path = os.path.join(options.path, name)
        subtree = mcProj.mcTree.extractSubTree(name)
        exp = copy.deepcopy(expTemplate)
        exp.setDbDir(os.path.join(path, "%s_DB" % name))
        if expTemplate.getDbType() == "kyoto_tycoon" and \
            os.path.splitext(name)[1] != ".kch":
            exp.setDbName("%s.kch" % name)
        else:
            exp.setDbName(name)
        if expTemplate.getDbType() == "kyoto_tycoon":
            exp.setDbPort(expTemplate.getDbPort() + portOffset)
            portOffset += 1
        exp.setReferencePath(os.path.join(path, "%s_reference.fa" % name))
        exp.setMAFPath(os.path.join(path, "%s.maf" % name))
        exp.updateTree(subtree, seqMap)
        exp.setConfigPath(os.path.join(path, "%s_config.xml" % name))
        os.makedirs(exp.getDbDir())
        exp.writeXML(expPath)
        configElem = copy.deepcopy(baseConfigXML)
        refElem = configElem.find("reference")
        refElem.attrib["reference"] = name
        ET.ElementTree(configElem).write(exp.getConfigPath()) 

def main():
    usage = "usage: %prog [options] <experiment> <output project path>"
    description = "Setup a multi-cactus project using an experiment xml as template"
    parser = OptionParser(usage=usage, description=description)
    parser.add_option("--subtreeSize", dest="subtreeSize", type="int", 
                      help="Max number of sequences to align at a time [default=2]", 
                      default=2)
    parser.add_option("--ancestorPrefix", dest="prefix", type="string",
                      help="Name to assign unlabeled tree nodes default=[Anc]",
                      default="Anc")
    
    options, args = parser.parse_args()
    
    if len(args) != 2:
        parser.print_help()
        raise RuntimeError("Wrong number of arguments")

    options.expFile = args[0]    
    options.path = os.path.abspath(args[1])
    options.name = os.path.basename(options.path)

    if os.path.isdir(options.path) or os.path.isfile(options.path):
        raise RuntimeError("Output project path %s exists\n" % options.path)
    
    expTemplate = ExperimentWrapper(ET.parse(options.expFile).getroot()) 
    mcProj = createMCProject(expTemplate.getTree(), options)
    createFileStructure(mcProj, expTemplate, options)
   # mcProj.check()
    return 0
    

if __name__ == '__main__':    
    main()