#!/usr/bin/env python

import subprocess, re, os, sys, readline, cmd, pickle
from pprint import pformat, pprint

cachefile = "/tmp/pouet"

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

def megabyze(i, fact=1000):
    """
    Return the size in Kilo, Mega, Giga, Tera, Peta according to the input.
    """
    i = float(i)
    for unit in "", "K", "M", "G", "T", "P":
        if i < 2000: break
        i = i / fact
    return "%.1f%s"%(i, unit)

class SesManager(cmd.Cmd):
    def __init__(self, *l, **kv):
        cmd.Cmd.__init__(self, *l, **kv)
        self._enclosures = {}
        self._controllers = {}
        self._disks = {}
        self.aliases = {}
        self.prompt = "Diskmap> "

    @property
    def disks(self):
        return dict([ (k, v) for k, v in self._disks.items() if k.startswith("/dev/rdsk/") ])

    @property
    def enclosures(self):
        return self._enclosures

    @property
    def controllers(self):
        return self._controllers

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
                self._controllers[m["id"]] = m

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
                self._enclosures[m["id"].lower()] = m
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
                self._disks[m["serial"]] = m

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
            if serial in self._disks:
                # Add device name to disks
                self._disks[serial]["device"] = device
                # Add a reverse lookup
                self._disks[device] = self._disks[serial]
            else:
                print "Warning : Got the serial %s from prtconf, but can't find it in disk detected by sas2ircu (disk removed ?)"%serial

    def set_leds(self, disks, value=True):
        if isinstance(disks, dict):
            disks = disks.values()
        progress = xrange(1,len(disks)+1, 1).__iter__()
        value = "on" if value else "off"
        for disk in disks:
            print "\rTurning leds %s : %3d/%d"%(value, progress.next(),len(disks)),
            run(sas2ircu, disk["controller"], "LOCATE", "%(enclosureindex)s:%(slot)s"%disk, value)
        print

    def preloop(self):
        try:
            self.do_load()
        except:
            print "Loading of previous save failed, trying to discover"
            self.do_discover()
            self.do_save()

    def emptyline(self):
        self.do_help("")

    def do_quit(self, line):
        "Quit"
        return True
    do_EOF = do_quit
        
    def do_discover(self, line=""):
        """Perform discovery on host to populate controller, enclosures and disks """
        self.discover_controllers()
        self.discover_enclosures()
        self.discover_mapping()
        self.do_save()
    do_refresh = do_discover

    def do_save(self, line=cachefile):
        """Save data to cache file. Use file %s if not specified"""%cachefile
        pickle.dump((self.controllers, self.enclosures, self._disks, self.aliases), file(line, "w+"))


    def do_load(self, line=cachefile):
        """Load data from cache file. Use file %s if not specified"""%cachefile
        self.controllers, self.enclosures, self._disks, self.aliases = pickle.load(file(line))

    def do_enclosures(self, line):
        """Display detected enclosures"""
        pprint(self.enclosures)

    def do_controllers(self, line):
        """Display detected controllers"""
        pprint(self.controllers)

    def do_disks(self, line):
        """Display detected disks. Use -v for verbose output"""
        list = [ ("%1d:%.2d:%.2d"%(v["controller"], v["enclosureindex"], v["slot"]), v)
                 for k,v in self.disks.items() ]
        list.sort()
        if line == "-v":
            pprint (list)
            return
        for path, disk in list:
            disk["path"] = path
            disk["device"] = disk["device"].replace("/dev/rdsk/", "")
            disk["readablesize"] = megabyze(disk["sizemb"]*1024*1024)
            print "%(path)s  %(device)23s  %(model)16s  %(readablesize)6s  %(state)s"%disk

    def ledparse(self, value, line):
        line = line.strip()
        targets = []
        if line == "all":
            targets = self.disks
        else:
            if line in self.aliases:
                line = self.aliases[line]
            if line in self.enclosures:
                targets = [ disk for disk in self.disks.values() if disk["enclosure"] == line ]
            else:
                for t in (line, "/dev/rdsk/%s"%line, line.upper(), line.lower()):
                    tmp = self._disks.get(t, None)
                    if tmp:
                        targets = [ tmp ]
                        break
                # Try to locate by path
                try:
                    if line.count(":") == 1:
                        c, e = line.split(":")
                        c, e = long(c), long(e)
                        s = None
                    else:
                        c, e, s = line.split(":", 2)
                        c, e, s = long(c), long(e), long(s)
                    targets = [ disk for disk in self.disks.values()
                            if disk["controller"] == c and disk["enclosureindex"] == e
                            and s == None or disk["slot"] == s ]
                except:
                    pass
        if targets:
            self.set_leds(targets, value)
        else:
            print "Could not find what you're talking about"

    def do_ledon(self, line):
        """ Turn on locate led on parameters FIXME : syntax parameters"""
        self.ledparse(True, line)

    def complete_ledon(self, text, line, begidx, endidx):
        candidates = [ "all", "ALL" ]
        candidates.extend(self.aliases.keys())
        candidates.extend([ disk["device"].replace("/dev/rdsk/", "") for disk in self.disks.values() ])
        candidates.extend([ disk["serial"] for disk in self.disks.values() ])
        candidates.extend([ "%(controller)s:%(enclosureindex)s:%(slot)s"%disk for disk in self.disks.values() ])
        candidates.extend([ "%(controller)s:%(index)s"%enclosure for enclosure in self.enclosures.values() ] )
        candidates.sort()
        return [ i for i in candidates if i.startswith(text) ]

    complete_ledoff = complete_ledon
    def do_ledoff(self, line):
        """ Turn off locate led on parameters FIXME : syntax parameters"""
        self.ledparse(False, line)

    def do_alias(self, line):
        """
        Used to set a name on a enclosure.
        
        Usage : alias key value
                alias -r key
        Without parameters : list current alias
        """
        if not line:
            pprint(self.aliases)
        elif line.startswith("-r"):
            junk, alias = line.split(" ",1)
            del self.aliases[alias.strip()]
        elif " " in line:
            alias,target = line.split(" ",1)
            alias = alias.strip()
            target = target.strip()
            if len(target) > 4:
                # Guess we have an uuid
                if target.lower() in self.enclosures:
                    self.aliases[alias] = target.lower()
                else:
                    print "No such enclosure %s"%target.lower()
            elif ":" in target:
                # Guess we have a path
                try:
                    c, e = target.split(":", 1)
                    c = long(c)
                    e = long(e)
                    tmp = [ v["id"].lower() for v in self.enclosures.values()
                            if v["controller"] == c and v["index"] == e ]
                    if len(tmp) != 1: raise
                    self.aliases[alias] = tmp[0]
                except Exception, e:
                    print "Tryed to find your enclosure by path but couldn't find it (%s)"%e
            self.do_save()

    def complete_alias(self, text, line, begidx, endidx):
        if line.startswith("-r "):
            return [ i for i in self.aliases.keys() if i.startswith(line) ]
        if line.count(" ") >= 2:
            return [ i for i in self.complete_ledon(text, line, begidx, endidx)
                     if i not in self.aliases ]
    
    def __str__(self):
        result = []
        for i in ("controllers", "enclosures", "disks"):
            result.append(i.capitalize())
            result.append("="*80)
            result.append(pformat(getattr(self,i)))
            result.append("")
        return "\n".join(result)



if __name__ == "__main__":
    #if not os.path.isfile(sas2ircu):
    #    sys.exit("Error, cannot find sas2ircu (%s)"%sas2ircu)
    sm = SesManager()
    if len(sys.argv) > 1:
        sm.preloop()
        sm.onecmd(" ".join(sys.argv[1:]))
    else:
        sm.cmdloop()
    
    
