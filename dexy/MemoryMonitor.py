# Collect per-process memory use over time.
# Written by Lucas C. Villa Real <lucasvr@us.ibm.com>
# Released under the GNU GPL version 2.

import os

def parseStatusFile(pid, field) :
	contents = ""
	fp = open("/proc/%d/status" %pid)
	while True :
		buf = fp.readline(4096)
		if not buf :
			break
		idx = buf.find(field)
		if idx >= 0 :
			contents = buf[idx:].split()[1]
			break
	fp.close()
	return contents 

def getVmSize(pid) :
	vmSize = parseStatusFile(pid, "VmSize:")
	if len(vmSize) :
		return int(vmSize)
	return -1

def getVmSwap(pid) :
	vmSwap = parseStatusFile(pid, "VmSwap:")
	if len(vmSwap) :
		return int(vmSwap)
	return -1

def getPPid(pid) :
	ppid = parseStatusFile(pid, "PPid:")
	if len(ppid) :
		return int(ppid)
	return -1

def getProcessName(pid) :
	fp = open("/proc/%d/cmdline" %pid)
	buf = fp.readline(1024)
	fp.close()

	tokens = buf.split('\x00')
	if tokens[0].find('python') >= 0 or tokens[0].find('/bin/sh') >= 0 :
		processName = tokens[1]
	elif len(tokens[0]) > 0 :
		processName = tokens[0]
	else :
		fp = open("/proc/%d/stat" %pid)
		buf = fp.readline(1024)
		fp.close()

		idx_start = buf.find("(")
		idx_end = buf.find(")")
		if idx_start >= 0 and idx_end >= 0 :
			processName = buf[idx_start+1:idx_end]
		else :
			print "unknown --> ",
			print processName
			print "tokens  --> ",
			print tokens
			return ""

	if processName.find("/") >= 0  :
		processName = os.path.basename(processName)
	if processName.find(":") >= 0 :
		processName = processName.split(":")[0]
	if processName.find("-") == 0 :
		processName = processName[1:]

	return processName

def getTotalMemory() :
	totalMemory = 0
	fp = open("/proc/meminfo")
	for line in fp.readlines() :
		if line.find("MemTotal:") == 0 :
			totalMemory = int(line.split()[1])
			break
	fp.close()
	return totalMemory





