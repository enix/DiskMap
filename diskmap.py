#!/usr/bin/env python

import subprocess, re, os, sys

def run(cmd, *args):
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
        self.controller = {}

    def discover_controller(self):
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
                self.controller[ctrl["index"]] = ctrl

    def discover_enclosure(self, *ctrls):
        """ Discover enclosure wired to controller. If no controller specified, discover them all """
        if not ctrls:
            ctrls = self.controller.keys()
        for ctrl in ctrls:
            tmp = run(sas2ircu, ctrl, "DISPLAY")
            for m in re.finditer("Enclosure# +: (?P<enclosureid>[^ ]+)\n +"
                                 "Logical ID +: (?P<logicalid>[^ ]+)\n +"
                                 "Numslots +: (?P<numslot>[0-9]+)", tmp):
                m = m.groupdict()
                print m
                self.enclosure[m["logicalid"]] = m

    def discover(self):
        """ use sas2ircu to populate controller, enclosures ands disks """
        self.discover_controller()
        self.discover_enclosure()
        
    def __str__(self):
        from pprint import pformat
        result = [ "Controller" ]
        result.append("="*80)
        result.append(pformat(self.controller))
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
    
    
