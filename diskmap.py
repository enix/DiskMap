#!/usr/bin/env python

import subprocess, re, os, sys, readline, cmd


sas2ircu = "/usr/sbin/sas2ircu"
prtconf = "/usr/sbin/prtconf"

def run(cmd, *args):
    args = tuple([ str(i) for i in args ])
    return subprocess.Popen((cmd,) + args,
                            stdout=subprocess.PIPE).communicate()[0]

def cleandict(mydict, *toint):
    result = {}
    for k in mydict.keys():
        result[k] = long(mydict[k]) if k in toint else mydict[k].strip()
    return result


class SesManager(cmd.Cmd):
    def __init__(self, *l, **kv):
        super(SesManager, self).__init__(*l, **kv)
        self.enclosures = {}
        self.controllers = {}
        self.disks = {}

    def discover_controllers(self):
        """ Discover controller present in the computer """
        tmp = run(sas2ircu, "LIST")
        tmp = re.findall("(\n +[0-9]+ +.*)", tmp)
        for ctrl in tmp:
            ctrl = ctrl.strip()
            m = re.match("(?P<id>[0-9]) +(?P<adaptertype>[^ ].*[^ ]) +(?P<vendorid>[^ ]+) +"
                         "(?P<deviceid>[^ ]+) +(?P<pciadress>[^ ]*:[^ ]*) +(?P<subsysvenid>[^ ]+) +"
                         "(?P<subsysdevid>[^ ]+) *", ctrl)
            if m:
                m = cleandict(m.groupdict(), "id")
                self.controllers[m["id"]] = m

    def discover_enclosures(self, *ctrls):
        """ Discover enclosure wired to controller. If no controller specified, discover them all """
        if not ctrls:
            ctrls = self.controllers.keys()
        for ctrl in ctrls:
            tmp = run(sas2ircu, ctrl, "DISPLAY")
            #tmp = file("/tmp/pouet.txt").read() # Test with Wraith__ setup
            enclosures = {}
            # Discover enclosures
            for m in re.finditer("Enclosure# +: (?P<index>[^ ]+)\n +"
                                 "Logical ID +: (?P<id>[^ ]+)\n +"
                                 "Numslots +: (?P<numslot>[0-9]+)", tmp):
                m = cleandict(m.groupdict(), "index", "numslot")
                m["controller"] = ctrl
                self.enclosures[m["id"]] = m
                enclosures[m["index"]] = m
            # Discover Drives
            for m in re.finditer("Device is a Hard disk\n +"
                                 "Enclosure # +: (?P<enclosureindex>[^\n]+)\n +"
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
                m = cleandict(m.groupdict(), "enclosureindex", "slot", "sizemb", "sizesector")
                m["enclosure"] = enclosures[m["enclosureindex"]]["id"]
                m["controller"] = ctrl
                self.disks[m["serial"]] = m

    def discover_mapping(self):
        """ use prtconf to get real device name using disk serial """
        tmp = run(prtconf, "-v")
        # Do some ugly magic to get what we want
        # First, get one line per drive
        tmp = tmp.replace("\n", "").replace("disk, instance", "\n")
        # Then match with regex
        tmp = re.findall("name='inquiry-serial-no' type=string items=1 dev=none +value='([^']+)'"
                         ".*?"
                         "name='client-guid' type=string items=1 *value='([^']+)'", tmp)
        # Capitalize everything.
        tmp = [ (a.upper(), b.upper()) for a, b in tmp ]
        tmp = dict(tmp)
        # Sometimes serial returned by prtconf and by sas2ircu are different. Mangle them
        for serial, device in tmp.items()[:]:
            serial = serial.strip()
            serial = serial.replace("WD-", "WD")
            device = "/dev/rdsk/c1t%sd0"%device
            if serial in self.disks:
                # Add device name to disks
                self.disks[serial]["device"] = device
                # Add a reverse lookup
                self.disks[device] = self.disks[serial]
            else:
                print "Warning : Got this serial (%s), but can't find it in disk detected by sas2ircu"%serial

    def discover(self):
        """ use sas2ircu to populate controller, enclosures ands disks """
        self.discover_controllers()
        self.discover_enclosures()
        self.discover_mapping()
        
    def __str__(self):
        from pprint import pformat
        result = []
        for i in ("controllers", "enclosures", "disks"):
            result.append(i.capitalize())
            result.append("="*80)
            result.append(pformat(getattr(self,i)))
            result.append("")
        return "\n".join(result)



if __name__ == "__main__":
    if not os.path.isfile(sas2ircu):
        sys.exit("Error, cannot find sas2ircu (%s)"%sas2ircu)
    sm = SesManager()
    sm.discover()
    print sm
    
    
