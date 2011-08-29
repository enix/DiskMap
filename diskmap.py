#!/usr/bin/env python

import subprocess, re, os, sys


sas2ircu = "/usr/sbin/sas2ircu"


def run(cmd, *args):
    args = tuple([ str(i) for i in args ])
    return subprocess.Popen((cmd,) + args,
                            stdout=subprocess.PIPE).communicate()[0]

def cleandict(mydict, *toint):
    result = {}
    for k in mydict.keys():
        result[k] = long(mydict[k]) if k in toint else mydict[k]
    return result

class Disk(object):
    def __init__(self):
        pass

class Enclosure(object):
    def __init__(self):
        self.disks = {}
    def attach(self, disk):
        self.disks[disk.id] = disk


class StorageManager(object):
    def __init__(self):
        self.enclosures = {}
        self.controllers = {}

    def discover_controllers(self):
        """ Discover controller present in the computer """
        tmp = run(sas2ircu, "LIST")
        tmp = re.findall("(\n +[0-9]+ +.*)", tmp)
        for ctrl in tmp:
            ctrl = ctrl.strip()
            m = re.match("(?P<index>[0-9]) +(?P<adaptertype>[^ ].*[^ ]) +(?P<vendorid>[^ ]+) +"
                         "(?P<deviceid>[^ ]+) +(?P<pciadress>[^ ]*:[^ ]*) +(?P<subsysvenid>[^ ]+) +"
                         "(?P<subsysdevid>[^ ]+) *", ctrl)
            if m:
                m = cleandict(m.groupdict(), "index")
                self.controllers[m["index"]] = ctrl

    def discover_enclosures(self, *ctrls):
        """ Discover enclosure wired to controller. If no controller specified, discover them all """
        if not ctrls:
            ctrls = self.controllers.keys()
        for ctrl in ctrls:
            tmp = run(sas2ircu, ctrl, "DISPLAY")
            for m in re.finditer("Enclosure# +: (?P<index>[^ ]+)\n +"
                                 "Logical ID +: (?P<logicalid>[^ ]+)\n +"
                                 "Numslots +: (?P<numslot>[0-9]+)", tmp):
                m = cleandict(m.groupdict(), "index", "numslot")
                m["controller"] = ctrl
                self.enclosures[m["logicalid"]] = m
            for m in re.finditer("Device is a Hard disk\n +"
                                 "Enclosure # +: (?P<enclosure>[^\n]+)\n +"
                                 "Slot # +: (?P<slot>[^\n]+)\n +"
                                 "State +: (?P<state>[^\n]+)\n +"
                                 "Size .in MB./.in sectors. +: (?P<sizemb>[^/]+)/(?P<sizesector>[^\n]+)\n +"
                                 "Manufacturer +: (?P<manufacturer>[^\n]+)\n +"
                                 "Model Number +: (?P<model>[^\n]+)\n +"
                                 "Firmware Revision +: (?P<firmware>[^\n]+)\n +"
                                 "Serial No +: (?P<serial>[^\n]+)\n +"
                                 "Protocol +: (?P<protocol>[^\n]+)\n +"
                                 "Drive Type +: (?P<drivetype>[^\n]+)\n"
                                 , tmp):
                m = cleandict(m.groupdict(), "enclosure", "slot", "sizemb", "sizesector")
                print m
            
                                

    def discover(self):
        """ use sas2ircu to populate controller, enclosures ands disks """
        self.discover_controllers()
        self.discover_enclosures()
        
    def __str__(self):
        from pprint import pformat
        result = [ "Controller" ]
        result.append("="*80)
        result.append(pformat(self.controllers))
        result.append("")
        result.append("Enclosures")
        result.append("="*80)
        result.append(pformat(self.enclosures))
        return "\n".join(result)

if __name__ == "__main__":
    if not os.path.isfile(sas2ircu):
        sys.exit("Error, cannot find sas2ircu (%s)"%sas2ircu)
    st = StorageManager()
    st.discover()
    print st
    
    
