# DiskMap

OpenSolaris/OpenIndiana utility to manage drive and map wmn device name (c1txxx) to real drive using lsi sas controller — Read more

This script will hopefully make your life easier if you use ZFS on OpenSolaris/OpenIndiana with LSI controllers and some kind of backplane.

It can:

* list connected drives, and see the mapping between wmn device name (c1txxx) and their physical location (controller, enclosure, slot);
* turn the error led of a drive on and off (for easy identification of the drive in large enclosures with many disks);
* be used as a pipe to enhance the output of programs like `iostat` to annotate disk information with the location of each disk.

It's a work in progress. It works for me, but I don't have the time to polish or clean it up; so if you want to add your favourite feature or fix some nasty bug, feel free to contribute.

# Requirements

You have to get the sas2ircu tool. Install it in /usr/sbin, or edit the path in the file).
An outdated revision is available [here](http://www.supermicro.com/support/faqs/data_lib/FAQ_9633_SAS2IRCU_Phase_5.0-5.00.00.00.zip).

There is some work in progress for smartmontools support.


# Usage & Available Commands

Everything happens through a CLI:

	# ./diskmap.py 
	Diskmap - berilia>

You can also run individual commands directly when invoking the program:

	# ./diskmap.py ledoff all


## `discover`

You need to run discover whenever the layout has changed (disk have been added/removed).
It will populate a cache, which will in turn be used by other commands.

Example:

	Diskmap - berilia> discover
	Warning : Got the serial 5629293 from prtconf, but can't find it in disk detected by sas2ircu (disk removed/not on backplane ?)
	Warning : Got the serial 5629293 from prtconf, but can't find it in disk detected by sas2ircu (disk removed/not on backplane ?)
	Warning : Got the disk /dev/rdsk/c3t0d0 from zpool status, but can't find it in disk detected by sas2ircu (disk removed ?)
	Warning : Got the disk /dev/rdsk/c3t1d0 from zpool status, but can't find it in disk detected by sas2ircu (disk removed ?)

## `disks`

List all the disks, along with their associated slot, model, capacity, state, pool, and usage.

The format for the slot is `<ctrl>:<enclosureid>:<drivenumber>`.

Example:

	Diskmap - berilia> disks
	0:02:00    c1t500151795944D1F0d0  INTEL SSDSA2M080   80.0G  Ready (RDY) rpool: mirror-0 / data: cache
	0:02:01    c1t50014EE6013FA92Ad0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-12
	0:02:02    c1t50014EE058037AA6d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-16
	0:02:03    c1t5001517959419710d0  INTEL SSDSA2M080   80.0G  Ready (RDY) rpool: mirror-0 / data: cache
	0:02:04    c1t50014EE6AB8F0F8Cd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-11
	0:02:05    c1t50014EE002AE45C0d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-16
	0:02:06    c1t500151795941982Bd0  INTEL SSDSA2M080   80.0G  Ready (RDY) rpool: mirror-0 / data: cache
	0:02:07    c1t50014EE6AB8F2BC5d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-10
	0:02:08    c1t50014EE0AD591F51d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-15
	0:02:09    c1t50014EE600E466F2d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-14
	0:02:10    c1t50014EE058037F90d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-15
	0:02:11    c1t50014EE0AD00308Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-3
	1:02:00    c1t50014EE00295E662d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-11
	1:02:01    c1t50014EE00295E07Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-7
	1:02:02    c1t50014EE0AD40CB43d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-2
	1:02:03    c1t50014EE0AD40BE62d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-1
	1:02:04    c1t50014EE600FE429Ed0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-13
	1:02:05    c1t50014EE6ABA7418Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-10
	1:02:06    c1t50014EE00295E6B4d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-7
	1:02:07    c1t50014EE0AD40C469d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-2
	1:02:08    c1t50014EE0AD40C373d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-1
	1:02:09    c1t50014EE057EB1AA1d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-6
	1:02:10    c1t50014EE65639A59Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-12
	1:02:11    c1t50014EE6AB8EEE8Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-4
	1:02:12    c1t50014EE600FE548Cd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: spares
	1:02:13    c1t50014EE0AD40CDAEd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-3
	1:02:14    c1t50014EE057EAEB0Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-6
	1:02:15    c1t50014EE0AD3BF57Dd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-0
	1:02:16    c1t50014EE600E4A577d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-13
	1:02:17    c1t50014EE6ABEA298Fd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-9
	1:02:18    c1t50014EE0AD3C068Cd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-0
	1:02:19    c1t50014EE057E63E46d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-4
	1:02:20    c1t50014EE057E64BBAd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-5
	1:02:21    c1t50014EE057E6558Dd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-5
	1:02:22    c1t50014EE6ABDA37BEd0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-9
	1:02:23    c1t50014EE0AD592031d0  WDC WD2002FAEX-0    2.0T  Ready (RDY) data: mirror-14
	Drives : 36   Total Capacity : 66.3T

## `ledon` & `ledoff`

You can turn on and off the error LEDs of individual drives.

Examples:

	Diskmap - berilia> ledon c1t50014EE6ABEA298Fd0
	Turning leds on :   1/1
	Diskmap - berilia> ledon 1:02:16
	Turning leds on :   1/1
	Diskmap - berilia> ledoff all
	Turning leds on :   36/36

Various input format are supported; use completion to see them all.

## `enclosures`

List detected enclosures on your system. The main purpose is to give you the enclosures ID and define aliases.

Example:

	Diskmap - berilia> enclosures
	{'50030480:0070d090': {'controller': 1L,
			       'id': '50030480:0070d090',
			       'index': 1L,
			       'numslot': 8L},
	 '50030480:0070d320': {'controller': 0L,
			       'id': '50030480:0070d320',
			       'index': 1L,
			       'numslot': 8L},
	 '50030480:0075e67f': {'controller': 0L,
			       'id': '50030480:0075e67f',
			       'index': 2L,
			       'numslot': 13L},
	 '50030480:009f8c7f': {'controller': 1L,
			       'id': '50030480:009f8c7f',
			       'index': 2L,
			       'numslot': 25L}}

## `alias`

Give an alias to an enclosure. You need the enclosure ID as shown by `enclosures`.

Examples:

	Diskmap - berilia> alias 50030480:0075e67f BCK
	Diskmap - berilia> alias 50030480:009f8c7f FNT
	Diskmap - berilia> alias
	{'50030480:0075e67f': 'BCK', '50030480:009f8c7f': 'FNT'}

## `enumerate`

Helper to generate zpool create command line.

Examples:

	Diskmap - berilia> enumerate mirror BCK FNT
	Debug with drive path : mirror 0:03:00 0:02:00 mirror 0:03:01 0:02:01 mirror 0:03:02 0:02:02 mirror 0:03:03 0:02:03 mirror 0:03:04 0:02:04 mirror 0:03:05 0:02:05 mirror 0:03:06 0:02:06 mirror 0:03:07 0:02:07 mirror 0:03:08 0:02:08 mirror 0:03:09 0:02:09 mirror 0:03:10 0:02:10 mirror 0:03:11 0:02:11 mirror 0:03:12
	C/C this in your zpool create cmd line : mirror c1t50014EE00295E662d0 c1t500151795944D1F0d0 mirror c1t50014EE00295E07Fd0 c1t50014EE6013FA92Ad0 mirror c1t50014EE0AD40CB43d0 c1t50014EE058037AA6d0 mirror c1t50014EE0AD40BE62d0 c1t5001517959419710d0 mirror c1t50014EE600FE429Ed0 c1t50014EE6AB8F0F8Cd0 mirror c1t50014EE6ABA7418Fd0 c1t50014EE002AE45C0d0 mirror c1t50014EE00295E6B4d0 c1t500151795941982Bd0 mirror c1t50014EE0AD40C469d0 c1t50014EE6AB8F2BC5d0 mirror c1t50014EE0AD40C373d0 c1t50014EE0AD591F51d0 mirror c1t50014EE057EB1AA1d0 c1t50014EE600E466F2d0 mirror c1t50014EE6ABA30519d0 c1t50014EE058037F90d0 mirror c1t50014EE6AB8EEE8Fd0 c1t50014EE0AD00308Fd0

	Diskmap - headone>  enumerate raidz2 0:3 0:4 0:3 0:4 0:3 0:4
	Debug with drive path : raidz2 0:03:03 0:04:00 0:03:04 0:04:01 0:03:05 0:04:02 raidz2 0:03:06 0:04:03 0:03:09 0:04:04 0:03:10 0:04:05 raidz2 0:03:11 0:04:06 0:03:12 0:04:07 0:03:13 0:04:08 raidz2 0:03:14 0:04:09 0:03:15 0:04:10 0:03:16 0:04:11 raidz2 0:03:17 0:04:12 0:03:18 0:04:13 0:03:19 0:04:14 raidz2 0:03:20 0:04:15
	C/C on your zpool create cmd line : raidz2 c8t50014EE5AAAC5B08d0 c8t50014EE555577A3Cd0 c8t50014EE55556F208d0 c8t50014EE500016C20d0 c8t50014EE555571580d0 c8t50014EE5AAAC37D8d0 raidz2 c8t5000A7203007963Ad0 c8t50014EE500018F04d0 c8t50014EE555576B44d0 c8t50014EE5AAACF084d0 c8t50014EE55556C0A0d0 c8t5000A72030079632d0 raidz2 c8t50014EE555564DD8d0 c8t50014EE5AAAC3270d0 c8t50014EE50001B748d0 c8t50014EE500026A8Cd0 c8t50014EE5AAAB3470d0 c8t50014EE5000227F8d0 raidz2 c8t50014EE5AAACF6A0d0 c8t50014EE5AAAC5574d0 c8t50014EE55557BEA0d0 c8t50014EE555568130d0 c8t50014EE5AAAC185Cd0 c8t50014EE5AAAC24ACd0 raidz2 c8t50014EE5AAABC21Cd0 c8t50014EE55555FDA4d0 c8t50014EE555577928d0 c8t50014EE5AAAC6010d0 c8t50014EE5AAAC8788d0 c8t50014EE555575130d0




# STDIN mangling

The program can also be used in a pipe, to enhance the standard output of another program to add device locations to the output of the program.

Example (assuming the aliases defined above):

	# iostat  -x -e  -n 1 | ./diskmap.py 
				    extended device statistics       ---- errors --- 
	    r/s    w/s   kr/s   kw/s wait actv wsvc_t asvc_t  %w  %b s/w h/w trn tot device
	    0.0    0.0    0.0    1.0  0.0  0.0    2.2    0.2   0   0   0   0   0   0 c3t0d0
	    0.0    0.0    0.0    1.0  0.0  0.0    2.2    0.2   0   0   0   0   0   0 c3t1d0
	    6.1    1.1   78.5   89.2  0.0  0.0    0.0    2.4   0   0   2   2   5   9 c1t5001517959419710d0/BCK03
	    6.2    1.1   79.4   89.2  0.0  0.0    0.0    2.3   0   0   2   2   7  11 c1t500151795944D1F0d0/BCK00
	    6.1    1.1   78.6   89.3  0.0  0.0    0.0    2.4   0   0   2   3  13  18 c1t500151795941982Bd0/BCK06
	    2.9   10.2   57.0  174.7  0.0  0.0    0.0    1.7   0   1   2   0   0   2 c1t50014EE0AD00308Fd0/BCK11
	    2.8    9.6   56.2  172.8  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE057EB1AA1d0/FNT09
	    2.8    9.8   56.1  174.5  0.0  0.0    0.0    2.9   0   1   2   0   0   2 c1t50014EE0AD40BE62d0/FNT03
	    0.6    3.0   12.4   34.2  0.0  0.0    0.0    2.2   0   0   2   0   0   2 c1t50014EE00295E662d0/FNT00
	    2.8    9.8   56.3  174.5  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE0AD40C373d0/FNT08
	    2.8    9.9   56.3  174.4  0.0  0.0    0.0    2.9   0   1   2   0   0   2 c1t50014EE0AD40CB43d0/FNT02
	    2.8    9.7   56.4  174.5  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE00295E6B4d0/FNT06
	    3.0    9.9   68.1  175.5  0.0  0.0    0.0    3.3   0   1   2   0   0   2 c1t50014EE057E63E46d0/FNT19
	    2.8    9.9   56.4  174.4  0.0  0.0    0.0    2.9   0   1   2   0   0   2 c1t50014EE0AD40C469d0/FNT07
	    2.8    9.3   55.4  169.4  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE057E64BBAd0/FNT20
	    2.8   10.0   56.5  175.6  0.0  0.0    0.0    2.9   0   1   2   0   0   2 c1t50014EE0AD3C068Cd0/FNT18
	    2.8    9.3   55.6  169.4  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE057E6558Dd0/FNT21
	    2.9   10.0   56.7  175.6  0.0  0.0    0.0    2.9   0   1   2   0   0   2 c1t50014EE0AD3BF57Dd0/FNT15
	    2.8    9.9   56.6  174.7  0.0  0.0    0.0    2.9   0   1   2   0   0   2 c1t50014EE0AD40CDAEd0/FNT13
	    2.9    9.5   56.7  172.8  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE057EAEB0Fd0/FNT14
	    2.8    9.7   56.5  174.5  0.0  0.0    0.0    3.0   0   1   2   0   0   2 c1t50014EE00295E07Fd0/FNT01
	    1.6    7.8   36.7   94.5  0.0  0.0    0.0    1.7   0   0   2   0   0   2 c1t50014EE600E466F2d0/BCK09
	    1.6    7.7   36.5   93.9  0.0  0.0    0.0    1.6   0   0   2   0   0   2 c1t50014EE058037F90d0/BCK10
	    1.6    7.4   37.1   91.8  0.0  0.0    0.0    1.6   0   0   2   0   0   2 c1t50014EE6013FA92Ad0/BCK01
	    1.5    7.4   35.9   91.8  0.0  0.0    0.0    1.6   0   0   2   0   0   2 c1t50014EE058037AA6d0/BCK02
	    1.5    8.5   35.0  100.8  0.0  0.0    0.0    2.3   0   0   2   0   0   2 c1t50014EE6ABA7418Fd0/FNT05
	    1.5    7.4   36.0   91.8  0.0  0.0    0.0    1.6   0   0   2   0   0   2 c1t50014EE002AE45C0d0/BCK05
	    1.5    7.8   34.0   94.4  0.0  0.0    0.0    2.4   0   0   2   0   0   2 c1t50014EE600FE429Ed0/FNT04
	    1.5    7.9   36.0   93.1  0.0  0.0    0.0    1.7   0   0   2   0   0   2 c1t50014EE6AB8F0F8Cd0/BCK04
	    1.5    7.4   34.2   91.8  0.0  0.0    0.0    2.6   0   0   2   9  32  43 c1t50014EE65639A59Fd0/FNT10
	    1.7    9.0   36.2  107.5  0.0  0.0    0.0    2.4   0   0   2   0   0   2 c1t50014EE6ABEA298Fd0/FNT17
	    1.6    7.7   36.6   93.9  0.0  0.0    0.0    1.6   0   0   2   0   0   2 c1t50014EE0AD591F51d0/BCK08
	    1.6    8.4   37.3  100.8  0.0  0.0    0.0    1.6   0   0   2   0   0   2 c1t50014EE6AB8F2BC5d0/BCK07
	    1.5    7.8   33.8   94.4  0.0  0.0    0.0    2.5   0   0   2   0   0   2 c1t50014EE600E4A577d0/FNT16
	    1.5    7.8   33.7   94.5  0.0  0.0    0.0    2.4   0   0   2   0   0   2 c1t50014EE0AD592031d0/FNT23
	    1.7    9.0   36.4  107.5  0.0  0.0    0.0    2.4   0   1   2   0   0   2 c1t50014EE6ABDA37BEd0/FNT22
	    2.2    9.3   47.3  122.1  0.0  0.0    0.0    3.2   0   1   2   0   0   2 c1t50014EE6AB8EEE8Fd0/FNT11
	    0.0    0.0    0.0    0.0  0.0  0.0    0.0    0.1   0   0   0   0   0   0 c1t50014EE600FE548Cd0/FNT12

See how BCK and FNT (as well as drive number in the enclosure) has been added to the output.

