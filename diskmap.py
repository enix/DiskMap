#!/usr/bin/env python

import subprocess, re, os, sys

def run(cmd, *args):
    return subprocess.Popen((cmd,) + args,
                            stdout=subprocess.PIPE).communicate()[0]
          

sas2ircu = "/usr/sbin/sas2ircu"


class Enclosure(object):
    def __init__(self):
        self.disks = {}
    def attach(self, disk):
        self.disks[disk.id] = disk


class Disk(object):
    def __init__(self):
        pass


class StorageManager(object):
    def __init__(self):
        self.enclosures = {}
        self.controller = {}

    def populate(self):
        """ use sas2ircu to populate controller, enclosures ands disks """
        # First, get Ctrl
        tmp = run(sas2ircu, "LIST")
        tmp = re.findall("(\n +[0-9]+ +.*)", tmp)
        for ctrl in tmp:
            m = re.match(" +(?P<index>[0-9]) +(?P<adaptertype>[^ ].*[^ ]) +(?P<vendorid>[^ ]+) +"
                         "(?P<deviceid>[^ ]+) +(?P<pciadress>[^ ]*:[^ ]*) +(?P<subsysvenid>[^ ]+)"
                         "+(?P<subsysdevid>[^ ]+) *", ctrl)
            if m:
                ctrl = m.groupdict()
                ctrl["index"] = int(ctrl["index"])
                self.controller[ctrl["index"]] = ctrl

    def __repr__(self):
        from pprint import pformat
        result = [ "Controller" ]
        result.append("="*80)
        result.append(pformat(self.controller))
        result.append("")
        result.append("Enclosures")
        result.append("="*80)
        result.append(pformat(self.enclosures))

if __name__ == "__main__":
    if not os.path.isfile(sas2ircu):
        sys.exit("Error, cannot find sas2ircu (%s)"%sas2ircu)
    st = StorageManager()
    st.populate()
    print st.__repr__()
    
    
