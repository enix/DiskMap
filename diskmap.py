#!/usr/bin/env python

import subprocess, re, os, sys

def run(cmd, *args):
    args = tuple([ str(i) for i in args ])
    return subprocess.Popen((cmd,) + args,
                            stdout=subprocess.PIPE).communicate()[0]
          

sas2ircu = "/usr/sbin/sas2ircu"

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
                ctrl = m.groupdict()
                ctrl["index"] = int(ctrl["index"])
                self.controllers[ctrl["index"]] = ctrl

    def discover_enclosures(self, *ctrls):
        """ Discover enclosure wired to controller. If no controller specified, discover them all """
        if not ctrls:
            ctrls = self.controllers.keys()
        for ctrl in ctrls:
            tmp = run(sas2ircu, ctrl, "DISPLAY")
            for m in re.finditer("Enclosure# +: (?P<enclosureid>[^ ]+)\n +"
                                 "Logical ID +: (?P<logicalid>[^ ]+)\n +"
                                 "Numslots +: (?P<numslot>[0-9]+)", tmp):
                m = m.groupdict()
                m["controller"] = ctrl
                self.enclosures[m["logicalid"]] = m
            for m in re.finditer("Device is a Hard disk\n +"
                                 "Enclosure # +: (?P<enclosure>[^ ]+)\n +"
#                                 "Slot # +: (?P<slot>[^ ]+)\n +"
#                                 "State +: (?P<state>[^ ]+)\n +"
#                                 "Size .in MB./.in sectors. +: (?P<sizemb>[^/]+)/(?P<sizesector>[^ ]+)\n +"
#                                 "Manufacturer +: (?P<manufacturer>[^ ]+)\n +"
#                                 "Model Number +: (?P<model>[^ ]+)\n +"
#                                 "Firmware Revision +: (?P<firmware>[^ ]+)\n +"
#                                 "Serial No +: (?P<serial>[^ ]+)\n +"
#                                 "Protocol +: (?P<protocol>[^ ]+)\n +"
#                                 "Drive Type +: (?P<drivetype>[^ ]+)\n"
                                 , tmp):
                print m.groupdict()
            
                                

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
    
    
