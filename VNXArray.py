import os

__author__ = 'mcowger'

from pyxml2obj import XMLin,XMLout
import subprocess
import pprint
import logging

class VNXObject:
    def __str__(self):
        return self.__class__.__name__ + "\n" + pprint.pformat(vars(self),width=120,depth=4)
class SystemCache(VNXObject):
    readCacheState = ""
    writeCacheState = ""
    cachePageSize = 0
    writeCacheMirrored = ""
    lowWatermark = 0
    highWatermark = 0
    prctDirtyCachePages = 0
    prctCachePagesOwned = 0
    readCacheSize = {}
    writeCacheSize = {}
    systemBufferSize = {}
    readCacheSize['SPA'] = 0
    readCacheSize['SPB'] = 0
    writeCacheSize['SPA'] = 0
    writeCacheSize['SPB'] = 0
    systemBufferSize['SPA'] = 0
    systemBufferSize['SPB'] = 0
class ServiceProcessor(VNXObject):
    name = ""
    cabinet = ""
    serial = ""
    signature = ""
    revision = ""
    memoryInMB = 0
    scsiid = None
    time = ""
class ControllerPair(VNXObject):
    name = ""
    model = ""
    modelType = ""
    serial = ""
    physicalNode = ""
    promRev = ""
    SPs = None
    cache = None
    arrayUid = ""
class LUN(VNXObject):
    number = 0
    name = ""
    state = ""
    RAIDType = ""
    raidGroupID = ""
    currentOwner = ""
    defaultOwner = ""
    prctRebuilt = 100
    prctBound = 100
    capacityMB = 0
    uid = ""
    private = False
class Disk(VNXObject):
    ID = ""
    vendorId = ""
    productId = ""
    productRevision = ""
    lun = ""
    type = ""
    state = ""
    serial = ""
    capacityMB = 0
    private = False
    numReads = 0
    numWrites = 0
    numLuns = 0
    raidGroupId = 0
    partNumber = ""
    userCapacity = ""
    currentSpeed = ""
    maximumSpeed = ""
    driveType = ""
class RaidGroup(VNXObject):
    ID = 0
    type = ""
    luns = ""
    maxDisks = 0
    maxLuns = 0
    rawCapacityBlocks = 0
    logicalCapacityBlocks = 0
    freeCapacityBlocks = 0
    lunExpansionEnabled = False
    legalRaidTypes = ""
    disks = []
class VNXArray(VNXObject):
    controllerPair = None
    luns = None
    disks = None
    rgs = None
    exePath = "/opt/Navisphere/bin/naviseccli"

    def setExePath(self,path):
        exePath = path
        self.logger.info("Setting exePath to " + exePath)
    def _getSPs(self):
        SPA = ServiceProcessor()
        SPB = ServiceProcessor()
        xmltree = self._getArrayData("getsp")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        SPA.name = baselevel[0]['NAME'].encode('ascii', 'ignore')
        SPA.cabinet = baselevel[1]['VALUE'].encode('ascii', 'ignore')
        SPA.signature = baselevel[2]['VALUE'].encode('ascii', 'ignore')
        SPA.revision = baselevel[4]['VALUE'].encode('ascii', 'ignore')
        SPA.serial = baselevel[5]['VALUE'].encode('ascii', 'ignore')
        SPA.memoryInMB = baselevel[6]['VALUE'].encode('ascii', 'ignore')
        SPA.scsiid = baselevel[7]['VALUE'].encode('ascii', 'ignore')
        SPB.name = baselevel[8]['NAME'].encode('ascii', 'ignore')
        SPB.cabinet = baselevel[9]['VALUE'].encode('ascii', 'ignore')
        SPB.signature = baselevel[10]['VALUE'].encode('ascii', 'ignore')
        SPB.revision = baselevel[12]['VALUE'].encode('ascii', 'ignore')
        SPB.serial = baselevel[13]['VALUE'].encode('ascii', 'ignore')
        SPB.memoryInMB = baselevel[14]['VALUE'].encode('ascii', 'ignore')
        SPB.scsiid = baselevel[15]['VALUE'].encode('ascii', 'ignore')
        return([SPA,SPB])
    def _getControllers(self):
        controller = ControllerPair()
        xmltree = self._getArrayData("getagent")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        controller.name = baselevel[1]['VALUE']
        controller.model = baselevel[9]['VALUE']
        controller.modelType = baselevel[10]['VALUE']
        controller.serial = baselevel[13]['VALUE']
        controller.promRev= baselevel[11]['VALUE']
        controller.physicalNode = baselevel[4]['VALUE']
        controller.SPs = self._getSPs()
        xmltree = self._getArrayData("getsptime")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        controller.SPs[0].time = baselevel[0]['VALUE']
        controller.SPs[1].time = baselevel[1]['VALUE']
        xmltree = self._getArrayData("getarrayuid")
        controller.arrayUid = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']['VALUE'].encode('ascii', 'ignore').split()[-1]
        cache = SystemCache()
        xmltree = self._getArrayData("getcache")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        cache.readCacheState = baselevel[0]['VALUE'].encode('ascii', 'ignore')
        cache.writeCacheState = baselevel[1]['VALUE'].encode('ascii', 'ignore')
        cache.cachePageSize = int(baselevel[2]['VALUE'].encode('ascii', 'ignore'))
        cache.writeCacheMirrored = baselevel[3]['VALUE'].encode('ascii', 'ignore')
        cache.lowWatermark = int(baselevel[4]['VALUE'].encode('ascii', 'ignore'))
        cache.highWatermark = int(baselevel[5]['VALUE'].encode('ascii', 'ignore'))
        cache.prctDirtyCachePages = int(baselevel[6]['VALUE'].encode('ascii', 'ignore'))
        cache.prctCachePagesOwned = int(baselevel[7]['VALUE'].encode('ascii', 'ignore'))
        cache.systemBufferSize['SPA'] = int(baselevel[17]['VALUE'].encode('ascii', 'ignore').replace(" MB",""))
        cache.systemBufferSize['SPB'] = int(baselevel[18]['VALUE'].encode('ascii', 'ignore').replace(" MB",""))
        cache.readCacheSize['SPA'] = int(baselevel[29]['VALUE'].encode('ascii', 'ignore'))
        cache.readCacheSize['SPB'] = int(baselevel[30]['VALUE'].encode('ascii', 'ignore'))
        cache.writeCacheSize['SPA'] = int(baselevel[31]['VALUE'].encode('ascii', 'ignore'))
        cache.writeCacheSize['SPB'] = int(baselevel[32]['VALUE'].encode('ascii', 'ignore'))
        controller.cache = cache

        return controller
    def _getLiveData(self,command):
        self.logger.info("Entering getLiveData: " + command)
        navisecclipath = self.exePath
        rawcmd = [navisecclipath,"-User", self.arrayUser ,"-Password",self.arrayPass,"-scope",str(self.arrayScope), "-Xml", "-h",self.arrayIp,command]
        xml =  subprocess.Popen(rawcmd, stdout=subprocess.PIPE, shell=False).stdout.read()
        self.logger.info("Exiting getLiveData")
        return XMLin(xml)
    def _getStoredData(self,command):
        self.logger.info("Entering getStoredData")
        handle = open(command,'r')
        self.logger.info("Exiting getStoredData")
        return XMLin("".join(handle.readlines()))
    def _getArrayData(self,datakey):
        self.logger.info("Entering getArrayData: " + datakey)
        acceptablekeys = ["getagent","getcontrol","getlun","getsptime","getcrus","getunusedluns","getarrayuid","getdisk","getrg","getcache","getlog","getsp"]
        if (datakey in acceptablekeys):
            if (self.live):
                return self._getLiveData(datakey)
            else:
                return self._getStoredData(datakey)
        else:
            raise Exception('Gack - thats not an acceptable command:' + datakey + '  Acceptable commands are: ' + " ".join(acceptablekeys))
    def _getLUNs(self):
        self.logger.info("Entering getLUNs")
        xmltree = self._getArrayData("getlun")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        currentLUN = None
        allLUNs = []
        for line in baselevel:
            if line['NAME'] == "LOGICAL UNIT NUMBER":
                #We are at a new LUN section.
                #Lets add what we have already to the array of LUNs, then continue
                if currentLUN != None: allLUNs.append(currentLUN);
                currentLUN = LUN()
                currentLUN.number = line['VALUE']
                self.logger.info("Parsing LUN" + currentLUN.number)
            elif line['NAME'] == "Name": currentLUN.Name = line['VALUE'];
            elif line['NAME'] == "RAID Type": currentLUN.RAIDType = line['VALUE'];
            elif line['NAME'] == "RAIDGroup ID": currentLUN.raidGroupID = line['VALUE'];
            elif line['NAME'] == "State": currentLUN.state = line['VALUE'];
            elif line['NAME'] == "Current owner": currentLUN.currentOwner = line['VALUE'];
            elif line['NAME'] == "Default Owner": currentLUN.defaultOwner = line['VALUE'];

            elif line['NAME'] == "Prct Rebuilt":
                try:
                    currentLUN.prctRebuilt = int(line['VALUE'])
                except ValueError:
                    currentLUN.prctRebuilt = 0


            elif line['NAME'] == "Prct Bound": currentLUN.prctBound = int(line['VALUE']);
            elif line['NAME'] == "LUN Capacity(Megabytes)": currentLUN.capacityMB = int(line['VALUE']);

            elif line['NAME'] == "UID": currentLUN.uid = line['VALUE'];
            elif line['NAME'] == "Is Private": currentLUN.private = bool(line['VALUE']);
            else: pass
        self.logger.info("Exiting getLUNs")
        return allLUNs
    def _getDisks(self):
        self.logger.info("Entering getDisks")
        currentDisk = None
        allDisks = []
        xmltree = self._getArrayData("getdisk")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        for line in baselevel:

            if line['NAME'].find("Enclosure") > -1:
                if currentDisk != None: allDisks.append(currentDisk);
                currentDisk = Disk()
                currentDisk.ID = line['NAME']
                self.logger.info("Parsing disk: " + currentDisk.ID)
            elif line['NAME'] == "Vendor Id": currentDisk.vendorId = line['VALUE'];
            elif line['NAME'] == "Product Id": currentDisk.productId = line['VALUE'];
            elif line['NAME'] == "Product Revision": currentDisk.productRevision = line['VALUE'];
            elif line['NAME'] == "Lun": currentDisk.lun = line['VALUE'];
            elif line['NAME'] == "Type": currentDisk.type = line['VALUE'];
            elif line['NAME'] == "State": currentDisk.state = line['VALUE'];
            elif line['NAME'] == "Serial Number": currentDisk.serial = line['VALUE'];
            elif line['NAME'] == "Capacity": currentDisk.capacityMB = line['VALUE'];
            elif line['NAME'] == "Private": currentDisk.private = bool(line['VALUE']);
            elif line['NAME'] == "Number of Reads": currentDisk.numReads = line['VALUE'];
            elif line['NAME'] == "Number of Writes": currentDisk.numWrites = line['VALUE'];
            elif line['NAME'] == "Number of Luns": currentDisk.numLuns = line['VALUE'];
            elif line['NAME'] == "Raid Group ID":
                try:
                    currentDisk.raidGroupId = int(line['VALUE'])
                except ValueError:
                    currentDisk.raidGroupId = -1
            elif line['NAME'] == "Drive Type": currentDisk.driveType = line['VALUE'];
            elif line['NAME'] == "Current Speed": currentDisk.currentSpeed = line['VALUE'];
            elif line['NAME'] == "Maximum Speed": currentDisk.maximumSpeed = line['VALUE'];
            elif line['NAME'] == "User Capacity": currentDisk.userCapacity = line['VALUE'];
            else: pass
        self.logger.info("Exiting getDisks")
        return allDisks
    def _getRaidGroups(self):
        self.logger.info("Entering getRGs")
        xmltree = self._getArrayData("getrg")
        baselevel = xmltree['MESSAGE']['SIMPLERSP']['METHODRESPONSE']['PARAMVALUE']['VALUE']['PARAMVALUE']
        currentRG = None
        allRGs = []
        for line in baselevel:
            if line['NAME'] == "RaidGroup ID":
                if currentRG != None: allRGs.append(currentRG);
                currentRG = RaidGroup()
                currentRG.ID = int(line['VALUE'])
                self.logger.info("Parsing RG: " + str(currentRG.ID))
            elif line['NAME'] == "List of luns": currentRG.luns = line['VALUE'];
            elif line['NAME'] == "Max Number of disks": currentRG.maxDisks = line['VALUE'];
            elif line['NAME'] == "Max Number of luns": currentRG.maxLuns = line['VALUE'];
            elif line['NAME'] == "Raw Capacity (Blocks)": currentRG.rawCapacityBlocks = int(line['VALUE']);
            elif line['NAME'] == "Logical Capacity (Blocks)": currentRG.logicalCapacityBlocks = int(line['VALUE']);
            elif line['NAME'] == "Free Capacity (Blocks,non-contiguous)": currentRG.freeCapacityBlocks = int(line['VALUE']);
            elif line['NAME'] == "Lun Expansion enabled": currentRG.lunExpansionEnabled = bool(line['VALUE']);
            elif line['NAME'] == "Legal RAID types": currentRG.legalRaidTypes = line['VALUE'];
            else: pass
        return allRGs
        controllerPair = None
        luns = None
        disks = None
        rgs = None
        live = False
    def _correlateDisksToRGs(self):
        self.logger.info("Correlating Disks to RGs")
        for disk in self.disks:
            for rg in self.rgs:
                self.logger.info("Attempting matching for disk: " + disk.ID + " RG: " + str(disk.raidGroupId) + " and RG: " + str(rg.ID))
                if rg.ID == disk.raidGroupId:
                    rg.disks.append(disk.ID)
                    self.logger.info("Matched disk " + str(disk.ID) + " to RG " + str(rg.ID))


    def __init__(self,arrayIp,arrayUser,arrayPass,arrayScope=0,live=True):
        logging.basicConfig(format='%(asctime)-6s: %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info("Entering VNXArray")
        self.arrayIp = arrayIp
        self.arrayUser = arrayUser
        self.arrayPass = arrayPass
        self.arrayScope = arrayScope
        self.live = live
        if self.rgs == None: self.rgs = self._getRaidGroups();
        if self.controllerPair == None: self.controllerPair = self._getControllers();
        if self.luns == None: self.luns = self._getLUNs();
        if self.disks == None: self.disks = self._getDisks();

        self._correlateDisksToRGs();

        self.logger.info("Finished with Init")









