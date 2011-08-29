#!/usr/bin/env python

import subprocess, re, os, sys

def run(cmd, *args):
    return subprocess.Popen([cmd] + args, stdout=subprocess.PIPE).communicate()[0]
          

sas2ircu = "/usr/bin/sas2ircu"
if not os.path.isfile(sas2ircu):
    sys.exit("Error, cannot find sas2ircu (%s)"%sas2ircu)

class Enclosure(object):
    def __init__(self):
        self.disks = {}
    def attach(self, disk):
        self.disks[disk.id] = disk


class Disk(object):
    def __init__(self):
        pass


class StorageManager(objet):
    def __init__(self):
        self.enclosures = {}
    def populate(self):
        """ use sas2ircu to populate enclosures ands disks """
        run
