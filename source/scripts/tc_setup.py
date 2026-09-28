#!/usr/bin/env python3
import os,subprocess,sys
wan=os.environ.get("WAN_INTERFACE","eth0")
wifi=os.environ.get("WIFI_INTERFACE","wlan0")

def sh(a): return subprocess.run(a,text=True,capture_output=True)

# This is a simple per-client ingress/egress shaping helper.
# Replace with IFB-based shaping if you need strict bidirectional guarantees.
def main():
    if len(sys.argv)<2:return
    op=sys.argv[1]
    if op=="init":
        sh(["tc","qdisc","replace","dev",wan,"root","handle","1:","htb","default","999"])
        sh(["tc","class","replace","dev",wan,"parent","1:","classid","1:999","htb","rate","1000mbit"])
    elif op=="add" and len(sys.argv)>=4:
        ip=sys.argv[2];mbps=float(sys.argv[3])
        cid=str(abs(hash(ip))%60000+100)
        rate=f"{mbps}mbit"
        sh(["tc","class","replace","dev",wan,"parent","1:","classid",f"1:{cid}","htb","rate",rate,"ceil",rate])
        sh(["tc","filter","replace","dev",wan,"protocol","ip","parent","1:","prio","10","u32","match","ip","dst",ip+"/32","flowid",f"1:{cid}"])
    elif op=="del" and len(sys.argv)>=3:
        # Filters/classes expire naturally on restart; explicit cleanup can be added per deployment.
        pass

if __name__=="__main__":main()
