#!/usr/bin/env python
#-*- coding: utf-8 -*- 
#
#
# Copyright (C) 2011 Sébastien Wacquiez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
                                                


VERSION="0.12a"

import subprocess, re, os, sys, readline, cmd, pickle, glob
from pprint import pformat, pprint
pj = os.path.join

from socket import gethostname
hostname = gethostname()

cachefile = "/tmp/pouet"

sas2ircu = "/usr/sbin/sas2ircu"
prtconf = "/usr/sbin/prtconf"
zpool = "/usr/sbin/zpool"
smartctl = "/usr/local/sbin/smartctl"
mdb = "/usr/bin/mdb"

def run(cmd, args, tosend=""):
    if not isinstance(args, list):
        args = [ args ]
    if not os.path.exists(cmd):
        raise Exception("Executable %s not found, please provide absolute path"%cmd)
    args = tuple([ str(i) for i in args ])
    if tosend:
        process = subprocess.Popen((cmd,) + args,
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE)
        return process.communicate(tosend)[0]
    else:
        return subprocess.Popen((cmd,) + args,
                                stdout=subprocess.PIPE).communicate()[0]
    

def revert(mydict):
    return dict([ (v,k) for k,v in mydict.items()])

def cleandict(mydict, *toint):
    result = {}
    for k in mydict.keys():
        if k in toint:
            result[k] = long(mydict[k])
        elif isinstance(mydict[k], str):
            result[k] = mydict[k].strip()
        else:
            result[k] = mydict[k]
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
        self.prompt = "Diskmap - %s> "%hostname

    @property
    def disks(self):
        return dict([ (k, v) for k, v in self._disks.items() if k.startswith("/dev/rdsk/") ])

    @property
    def enclosures(self):
        return self._enclosures

    @property
    def controllers(self):
        return self._controllers

    def discover_controllers(self, fromstring=None):
        """ Discover controller present in the computer """
        if not fromstring:
            fromstring = run(sas2ircu, "LIST")
        tmp = re.findall("(\n +[0-9]+ +.*)", fromstring)
        for ctrl in tmp:
            ctrl = ctrl.strip()
            m = re.match("(?P<id>[0-9]) +(?P<adaptertype>[^ ].*[^ ]) +(?P<vendorid>[^ ]+) +"
                         "(?P<deviceid>[^ ]+) +(?P<pciadress>[^ ]*:[^ ]*) +(?P<subsysvenid>[^ ]+) +"
                         "(?P<subsysdevid>[^ ]+) *", ctrl)
            if m:
                m = cleandict(m.groupdict(), "id")
                self._controllers[m["id"]] = m

    def discover_enclosures(self, ctrls = None):
        """ Discover enclosure wired to controller. Ctrls = { 0: 'sas2ircu output', 1: 'sas2ircu output', ...}"""
        if not ctrls:
            tmp = {}
            for ctrl in self.controllers.keys():
                tmp[ctrl] = run(sas2ircu, [ctrl, "DISPLAY"])
            ctrls = tmp
        for ctrl, output in ctrls.items():
            enclosures = {}
            # Discover enclosures
            for m in re.finditer("Enclosure# +: (?P<index>[^ ]+)\n +"
                                 "Logical ID +: (?P<id>[^ ]+)\n +"
                                 "Numslots +: (?P<numslot>[0-9]+)", output):
                m = cleandict(m.groupdict(), "index", "numslot")
                m["id"] = m["id"].lower()
                
                # Compute path, save ctrl
                m["path"] = [ "%s:%s"%(ctrl,m["index"] ) ]
                m["controller"] = ctrl

                # And if we already have this enclosure, just add it to the existing one, else save it
                if m["id"] in self._enclosures:
                    self._enclosures[m["id"]]["path"].extend(m["path"])
                    enclosures[m["index"]] = self._enclosures[m["id"]]
                else:
                    self._enclosures[m["id"]] = m
                    enclosures[m["index"]] = m
                
            # Discover Drives on each enclosure
            for m in re.finditer("Device is a Hard disk\n +"
                                 "Enclosure # +: (?P<enclosureindex>[^\n]*)\n +"
                                 "Slot # +: (?P<slot>[^\n]*)\n +"
                                 "(SAS Address +: (?P<sasaddress>[^\n]*)\n +)?"
                                 "State +: (?P<state>[^\n]*)\n +"
                                 "Size .in MB./.in sectors. +: (?P<sizemb>[^/]*)/(?P<sizesector>[^\n]*)\n +"
                                 "Manufacturer +: (?P<manufacturer>[^\n]*)\n +"
                                 "Model Number +: (?P<model>[^\n]*)\n +"
                                 "Firmware Revision +: (?P<firmware>[^\n]*)\n +"
                                 "Serial No +: (?P<serial>[^\n]*)\n +"
                                 "(GUID +: (?P<guid>[^\n]*)\n +)?"
                                 "Protocol +: (?P<protocol>[^\n]*)\n +"
                                 "Drive Type +: (?P<drivetype>[^\n]*)\n"
                                 , output):
                m = cleandict(m.groupdict(), "enclosureindex", "slot", "sizemb", "sizesector")
                m["enclosure"] = enclosures[m["enclosureindex"]]["id"]
                # Uppercase the serial number (I really don't know if it's a good idea ...)
                m["serial"] = m["serial"].upper()
                # Set the controller and full path. A device can be multiple attached
                m["controller"] = [ ctrl ]
                m["path"] = [ "%1d:%.2d:%.2d"%(ctrl, m["enclosureindex"], m["slot"]) ]
                # If we already have this disk, just add the path to the existing object
                if m["serial"] in self._disks:
                    self._disks[m["serial"]]["path"].extend(m["path"])
                    self._disks[m["serial"]]["controller"].extend(m["controller"])
                else: # else save it
                    self._disks[m["serial"]] = m

    def discover_mapping(self, fromstring=None):
        """
        Use prtconf to get real device name using disk serial.
        We should be able to use guid instead, but for some reason it's not reported
        in standard way on the server I've access to.

        """
        if not fromstring:
            fromstring = run(prtconf, "-v")
        # Do some ugly magic to get what we want
        # First, get one line per drive
        tmp = fromstring.replace("\n", "").replace("disk, instance", "\n")
        # Then match with regex
        tmp = re.findall("name='inquiry-serial-no' type=string items=1 dev=none +value='([^']+)'"
                         ".*?"
                         #"name='client-guid' type=string items=1 *value='([^']+)'"
                         #".*?"
                         "dev_link=(/dev/rdsk/c[^ ]*d0)s0", tmp)
        for serial, device in tmp:
            # We use a upped serial.
            serial = serial.strip().upper()
            # Sometimes serial returned by prtconf and by sas2ircu are different.
            if serial not in self._disks:
                # First, try to mangle them (observed on WD disk)
                if serial.replace("-", "") in self._disks:
                    serial = serial.replace("-", "")
                # Then try to use just 8 first char (observed on Seagate Drive)
                elif serial[:8] in self._disks:
                    serial = serial[:8]
                # Then try to use just 8 last char (observed on some other WD disk)
                elif serial[-8:] in self._disks:
                    serial = serial[-8:]
            if serial in self._disks:
                # Add device name to disks
                if "device" in self._disks[serial]:
                    print "Warning ! We have 2 device for disk %s : %s and %s"%(serial, self._disks[serial]["device"], device)
                    print "Check your mutlipath settings (stmsboot -e and scsi-vhci-failover-override in /kernel/drv/scsi_vhci.conf"
                self._disks[serial]["device"] = device
                # Add a reverse lookup
                self._disks[device] = self._disks[serial]
            else:
                print "Warning : Got the serial %s from prtconf, but can't find it in disk detected by sas2ircu (disk removed/not on backplane ?)"%serial

    def discover_zpool(self, fromstring=None):
        """ Try to locate disk in current zpool configuration"""
        if not fromstring:
            fromstring = run(zpool, "status")
        pools = fromstring.split("pool:")
        for pool in pools:
            if not pool.strip(): continue
            for m in re.finditer(" (?P<pool>[^\n]+)\n *" # We've splitted on pool:, so our first word is the pool name
                                 "state: (?P<state>[^ ]+)\n *"
                                 "(status: (?P<status>(.|\n)+)\n *)??"
                                 "scan: (?P<scan>(.|\n)*)\n *"
                                 "config: ?(?P<config>(.|\n)*)\n *"
                                 "errors: (?P<errors>[^\n]*)"
                                 ,pool):
                m = m.groupdict()
                parent = "stripped"
                for disk in re.finditer("(?P<indent>[ \t]+)(?P<name>[^ \t\n]+)( +(?P<state>[^ \t\n]+) +)?("
                                        "(?P<read>[^ \t\n]+) +(?P<write>[^ \t\n]+) +"
                                        "(?P<cksum>[^\n]+))?(?P<notes>[^\n]+)?\n", m["config"]):
                    disk = disk.groupdict()
                    if not disk["name"] or disk["name"] in ("NAME", m["pool"]):
                        continue
                    if disk["name"][-4:-2] == "d0":
                        disk["name"] = disk["name"][:-2]
                    if (disk["name"].startswith("mirror") or
                        disk["name"].startswith("log") or
                        disk["name"].startswith("raid") or
                        disk["name"].startswith("spare") or
                        disk["name"].startswith("cache")):
                        parent = disk["name"].strip()
                        continue
                    if "/dev/rdsk" not in disk["name"]:
                        disk["name"] = "/dev/rdsk/%s"%disk["name"]
                    if disk["name"] not in self._disks:
                        print "Warning : Got the disk %s from zpool status, but can't find it in disk detected by sas2ircu (disk removed ?)"%disk["name"]
                        continue
                    self._disks[disk["name"]]["zpool"] = self._disks[disk["name"]].get("zpool", {})
                    self._disks[disk["name"]]["zpool"][m["pool"]] = parent
        
    def set_leds(self, disks, value=True):
        if isinstance(disks, dict):
            disks = disks.values()
        progress = xrange(1,len(disks)+1, 1).__iter__()
        value = "on" if value else "off"
        for disk in disks:
            print "\rTurning leds %s : %3d/%d"%(value, progress.next(),len(disks)),
            run(sas2ircu, [disk["controller"][0], "LOCATE", "%(enclosureindex)s:%(slot)s"%disk, value])
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
        
    def do_discover(self, configdir=""):
        """Perform discovery on host to populate controller, enclosures and disks

        Take an optionnal parameter which can be a directory containing files dumped
        with confidump.
        """
        self._enclosures = {}
        self._controllers = {}
        self._disks = {}
        if configdir and os.path.isdir(configdir):
            # We wan't to load data from an other box for testing purposes
            # So we don't want to catch any exception
            files = os.listdir(configdir)
            for f in ("prtconf-v.txt", "sas2ircu-0-display.txt", "sas2ircu-list.txt", "zpool-status.txt"):
                if f not in files:
                    print "Invalid confdir, lacking of %s"%f
                    return
            self.discover_controllers(file(pj(configdir, "sas2ircu-list.txt")).read())
            files = glob.glob(pj(configdir, "sas2ircu-*-display.txt"))
            tmp = {}
            for name in files:
                ctrlid = long(os.path.basename(name).split("-")[1])
                tmp[ctrlid] = file(name).read()
            self.discover_enclosures(tmp)
            self.discover_mapping(file(pj(configdir, "prtconf-v.txt")).read())
            self.discover_zpool(file(pj(configdir, "zpool-status.txt")).read())
        else:
            for a in ( "discover_controllers", "discover_enclosures",
                   "discover_mapping", "discover_zpool" ):
                try:
                    getattr(self, a)()
                except Exception, e:
                    print "Got an error during %s discovery : %s"%(a,e)
                    print "Please run %s configdump and send the report to dev"%sys.argv[0]
                    break
        self.do_save()
    do_refresh = do_discover

    def do_save(self, line=cachefile):
        """Save data to cache file. Use file %s if not specified"""%cachefile
        if not line: line = cachefile # Cmd pass a empty string
        pickle.dump((self.controllers, self.enclosures, self._disks, self.aliases), file(line, "w+"))


    def do_load(self, line=cachefile):
        """Load data from cache file. Use file %s if not specified"""%cachefile
        self._controllers, self._enclosures, self._disks, self.aliases = pickle.load(file(line))

    def do_enclosures(self, line):
        """Display detected enclosures"""
        pprint(self.enclosures)

    def do_controllers(self, line):
        """Display detected controllers"""
        pprint(self.controllers)

    def do_disks(self, line):
        """Display detected disks. Use -v for verbose output"""
        list = [ (",".join(v["path"]), v)
                 for k,v in self.disks.items() ]
        list.sort()
        if line == "-v":
            pprint (list)
            return
        totalsize = 0
        for path, disk in list:
            disk["cpath"] = path
            disk["device"] = disk["device"].replace("/dev/rdsk/", "")
            disk["readablesize"] = megabyze(disk["sizemb"]*1024*1024)
            disk["pzpool"] = " / ".join([ "%s: %s"%(k,v) for k,v in disk.get("zpool", {}).items() ])
            disk["alias"] = self.aliases.get(disk["enclosure"], disk["enclosure"]) + "/%02d"%disk["slot"]
            totalsize += disk["sizemb"]*1024*1024
            print "{cpath}  {alias:<16} {device:<21}  {model:<16}  {readablesize:<6} {pzpool}".format(**disk)
        print "Drives : %s   Total Capacity : %s"%(len(self.disks), megabyze(totalsize))

    def smartctl(self, disks, action="status"):
        """ Execute smartctl on listed drive. If no drive selected, run it on all available drive. """
        params = [ "-s", "on", "-d", "sat" ]
        if action == "status":
            params += [ "-a" ]
        elif action == "test":
            params += [ "-t", "short" ]
        result = []
        progress = xrange(1,len(disks)+1, 1).__iter__()
        for disk in disks:
            print "\rExecuting smartcl on %s : %3d/%d"%(disk["device"].replace("/dev/rdsk/",""),
                                                     progress.next(),len(disks)),
            smartparams = params + [ disk["device"]+"p0" ]
            result.append(run(smartctl, smartparams))
        print "Done"
        return result

    def do_smartcl_getstatus(self, line):
        # FIXME : line parsing
        if line:
            raise NotImplemetedError
        else:
            disks = self.disks.values()
        for (disk, smartoutput) in zip(disks, self.smartctl(disks)):
            try:
                self._disks[disk["device"]]["smartoutput"] = smartoutput
                smartoutput = re.sub("\n[ \t]+", " ", smartoutput)
                if "test failed" in smartoutput:
                    print "  Disk %s fail his last test"%disk["device"].replace("/dev/rdsk/", "")
                zob= re.findall("(Self-test execution status.*)", smartoutput)
            except KeyError:
                pass

    def do_smartcl_runtest(self, line):
        # FIXME : line parsing
        if line:
            raise NotImplemetedError
        else:
            disks = self.disks.values()
        self.smartctl(disks, action="test")

    def get_enclosure(self, line):
        """ Try to find an enclosure """
        aliases = revert(self.aliases)
        if line in aliases:
            line = aliases[line]
        if line in self.enclosures:
            return line
        if line.lower() in self.enclosures:
            return line.lower()
        try:
            c, e = line.split(":", 1)
            c, e = long(c), long(e)
            tmp = [ v["id"].lower() for v in self.enclosures.values()
                    if v["controller"] == c and v["index"] == e ]
            if len(tmp) != 1: raise
            return tmp[0]
        except Exception, e:
            #print e
            return None

    def get_disk(self, line):
        for t in (line, "/dev/rdsk/%s"%line, line.upper(), line.lower()):
            tmp = self._disks.get(t, None)
            if tmp:
                return [ tmp ]
    
        # Try to locate by path
        try:
            # Check if first element of path is an enclosure
            tmp = line.split(":",2)
            if len(tmp) == 2:
                e = self.get_enclosure(tmp[0])
                if e:
                    return [ disk for disk in self.disks.values()
                             if disk["enclosure"] == e and disk["slot"] == long(tmp[1]) ]
            else:
                c, e, s = tmp
                c, e, s = long(c), long(e), long(s)
                return [ disk for disk in self.disks.values()
                         if c in disk["controller"] and disk["enclosureindex"] == e
                         and disk["slot"] == s ]
        except Exception, e:
            print e
            return None

    def complete_enumerate(self, text, line, begidx, endidx):
        if line.count(" ") > 1:
            # FIXME Only use enclosure with drive attached ...
            result = []
            result.extend(self.enclosures.keys())
            result.extend([ "%(controller)s:%(index)s"%e for e in self.enclosures.values() ])
            result.extend(self.aliases.values())
        else:
            result = [ "mirror", "raidz1", "raidz2", "raidz3" ]
        return [ i for i in result if i.startswith(text) ]

    def do_enumerate(self, line):
        """
        Enumerate disks sequentially to help zpool creation.

        Eg :
        2 way mirror on 1 enclosures :
        enumerate mirror backplane1 backplane1
        mirror disk1_backplane1 disk2_backplane1 mirror disk3_backplane1 disk4_backplane1 [...]
        
        2 way mirror on 2 enclosures :
        enumerate mirror [backplane1] [backplane2]
        output :
        mirror disk1_backplane1 disks1_backplane2 mirror disk2_backplane1 disk2_backplane2 [...]

        enumerate raidz2 b1 b2 b1 b2 :
        raidz2 d1_b1 d1_b2 d2_b1 d2_b2 raidz2 d3_b1 d3_b2 d4_b1 d4_b2 [...]
        """
        line = line.strip()
        if not line: return
        line = line.split()
        text = line.pop(0)
        # Get enclosure id for each parameters
        enclosures = [ self.get_enclosure(i) for i in line ]
        # Then build a list of drives for each enclosure
        disks = {}
        for enclosure in enclosures:
            disks[enclosure] = [ disk for disk in self.disks.values() if disk["enclosure"] == enclosure ]
            # And sort it per drive index
            disks[enclosure].sort(key=lambda a: a["slot"])
        # Now, iterate on each enclosures we get a print the drive device name
        debug = []
        result = []
        while True:
            # Use a temporary list so we don't print partial calculation
            tmp = [ text ]
            debug.append(text)
            try:
                for enclosure in enclosures:
                    # Get next disk
                    disk = disks[enclosure].pop(0)
                    # Add what we need
                    tmp.append(disk["device"].replace("/dev/rdsk/",""))
                    debug.append(disk["path"][0])
            except IndexError:
                    break
            result.extend(tmp)
        print "Debug with drive path : " + " ".join(debug)
        print "C/C this in your zpool create cmd line : " + " ".join(result)
        

    def do_drawletter(self, line):
        """ Print a char on a 4x6 enclosure """
        line = line.strip()
        if not line: return
        letters = { "N": [ 0, 1, 2, 3, 4, 5, 9, 10, 13, 14, 18, 19, 20, 21, 22, 23 ],
                   "X": [ 0, 1, 4, 5, 8, 9, 14, 15, 18 , 19, 22, 23 ],
                   # FIXME Ajouter les chiffres
                   }
        letter, enclosure = line.split(" ",1)
        e = self.get_enclosure(enclosure)
        if not e:
            print "Invalid enclosure %s"%e
        self.do_ledoff(e)
        self.set_leds([ disk for disk in self.disks.values()
                        if disk["slot"] in letters[letter] and disk["enclosure"] == e ], True)

    def do_configdump(self, path):
        if not path:
            path = pj(".", "configudump-%s"%hostname)
        if not os.path.exists(path):
            os.makedirs(path)
        tmp = run(sas2ircu, "LIST")
        self.discover_controllers(tmp)
        file(pj(path, "sas2ircu-list.txt"), "w").write(tmp)
        for ctrl in self.controllers:
            file(pj(path, "sas2ircu-%s-display.txt"%ctrl), "w").write(
                run(sas2ircu, [ctrl, "DISPLAY"]))
        file(pj(path, "prtconf-v.txt"), "w").write(
            run(prtconf, "-v"))
        file(pj(path, "zpool-status.txt"), "w").write(
            run(zpool, "status"))
        print "Dumped all value to path %s"%path

    def ledparse(self, value, line):
        line = line.strip()
        targets = []
        if line == "all":
            targets = self.disks
        else:
            # Try to see if it's an enclosure
            target = self.get_enclosure(line)
            if target:
                targets = [ disk for disk in self.disks.values() if disk["enclosure"] == target ]
            else:
                # Try to see if it's a disk
                targets = self.get_disk(line)
        if targets:
            self.set_leds(targets, value)
        else:
            print "Could not find what you're talking about"

    def do_ledon(self, line):
        """ Turn on locate led on parameters FIXME : syntax parameters"""
        self.ledparse(True, line)

    def complete_ledon(self, text, line, begidx, endidx):
        candidates = [ "all", "ALL" ]
        candidates.extend(self.aliases.values())
        candidates.extend([ disk["device"].replace("/dev/rdsk/", "") for disk in self.disks.values() ])
        candidates.extend([ disk["serial"] for disk in self.disks.values() ])
        candidates.extend([ "%s:%s:%s"%(ctrl, disk["enclosureindex"], disk["slot"])
                            for disk in self.disks.values() for ctrl in disk["controller"] ])
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
        
        Usage : alias enclosure name
                alias -r name
                alias -r enclosure
        Without parameters : list current alias
        """
        if not line:
            pprint(self.aliases)
        elif line.startswith("-r"):
            junk, alias = line.split(" ",1)
            alias = alias.strip()
            if alias in self.aliases:
                del self.aliases[alias]
            else:
                # We have to do a reverse lookup to find it !
                tmp = revert(self.aliases)
                if alias in tmp:
                    del self.aliases[tmp[alias]]
            self.do_save()
        elif " " in line:
            target, alias = line.split(" ",1)
            alias = alias.strip()
            enclosure = self.get_enclosure(target.strip())
            if not enclosure:
                print "No such enclosure %s"%target.lower()
            else:
                self.aliases[enclosure] = alias
                self.do_save()

    def complete_alias(self, text, line, begidx, endidx):
        if line.startswith("alias -r "):
            return ([ i for i in self.aliases.keys() if i.startswith(text) ] +
                    [ i for i in self.aliases.values() if i.startswith(text) ])
        if line.count(" ") == 1:
            result = []
            result.extend(self.enclosures.keys())
            result.extend([ "%(controller)s:%(index)s"%e for e in self.enclosures.values() ])
            return [ i for i in result if i.startswith(text) ]
                        
    def do_mangle(self, junk=""):
        """ This function is automatically called when piping something to diskmap.

        It'll suffix all drive name with the enclosure name they are in (defined with an
        alias) and the drive slot.

        Try : iostat -x -e -n 1 | diskmap.py
        """
        if sys.stdin.isatty():
            print "This command is not intented to be executed in interactive mode"
            return
        replacelist = []
        for enclosure, alias in self.aliases.items():
            for disk in self.disks.values():
                if disk["enclosure"] == enclosure:
                    tmp = disk["device"].replace("/dev/rdsk/", "")
                    replacelist.append((tmp, "%s/%s%02d"%(tmp, alias, disk["slot"])))
        line = sys.stdin.readline()
        while line:
            for r, e in replacelist:
                line = line.replace(r, e)
            sys.stdout.write(line)
            sys.stdout.flush()
            line = sys.stdin.readline()

    def do_sd_timeout(self, timeout=""):
        """
        Get / Set sd timeout value

        When no parameter is present, display the current sd_io_time, and check that running
        drive use the same timing.
        
        This script will only change value for the running drive. If you wan't to apply change
        permanently, put 'set sd:sd_io_time=5' in /etc/system

        Be aware that the script will change the default value of sd_io_time, and also change
        the current value for all drive in your system.

        See : http://blogs.everycity.co.uk/alasdair/2011/05/adjusting-drive-timeouts-with-mdb-on-solaris-or-openindiana/
        """
        if timeout:
            try:
                timeout = int(timeout)
            except:
                print "Invalid timeout specified"
                return
        # Displaying current timeout
        tmp = run(mdb, "-k", tosend="sd_io_time::print\n")
        globaltimeout = int(tmp.strip(), 16)
        print "Current Global sd_io_time : %s"%globaltimeout
        drivestimeout = run(mdb, "-k", tosend="::walk sd_state | ::grep '.!=0' | "
                            "::print -a struct sd_lun un_cmd_timeout\n")
        values = [ int(i, 16) for i in re.findall("= (0x[0-9a-f]+)", drivestimeout) if i ]
        print "Got %s values from sd disk driver, %s are not equal to system default"%(
            len(values), len(values)-values.count(globaltimeout))
        if timeout: # We want to set new timeout for drives
            # Set global timeout
            print "Setting global timeout ...",
            run(mdb, "-kw", tosend="sd_io_time/W 0x%x\n"%timeout)
            # Set timeout for every drive
            for driveid in re.findall("(.+) un_cmd_timeout", drivestimeout):
                print "\rSetting timeout for drive id %s ..."%driveid,
                run(mdb, "-kw", tosend="%s/W 0x%x\n"%(driveid, timeout))
            print "Done"
            print "Don't forget add to your /etc/system 'set sd:sd_io_time=%s' so change persist accross reboot"%timeout
    
    def __str__(self):
        result = []
        for i in ("controllers", "enclosures", "disks"):
            result.append(i.capitalize())
            result.append("="*80)
            result.append(pformat(getattr(self,i)))
            result.append("")
        return "\n".join(result)


import unittest
class TestConfigs(unittest.TestCase):
    pass



if __name__ == "__main__":
    #if not os.path.isfile(sas2ircu):
    #    sys.exit("Error, cannot find sas2ircu (%s)"%sas2ircu)
    sm = SesManager()
    if len(sys.argv) > 1:
        sm.preloop()
        sm.onecmd(" ".join(sys.argv[1:]))
        sm.postloop()
    elif sys.stdin.isatty():
        sm.cmdloop()
    else:
        sm.preloop()
        sm.onecmd("mangle")
        sm.postloop()
    
    
