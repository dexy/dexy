import subprocess
import re


f = open("server.conf.template", "r")
config = f.read()

proc = subprocess.Popen("ifconfig", stdout=subprocess.PIPE)
ifconfig, stderr = proc.communicate()

r = re.compile("inet addr\:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)")
m = re.search(r, ifconfig)

ip = m.groups(1)[0]
print ip

o = open("server.conf", "w")
o.write(config.replace("localhost", ip))
o.close()


