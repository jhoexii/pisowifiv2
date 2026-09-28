import sys,subprocess
sys.path.insert(0,"/opt/pisowifi/portal")
import db,firewall
db.init_db();db.expire_sessions()
subprocess.run(["nft","flush","set","inet","pisowifi","authorized_clients"],capture_output=True)
for s in db.active_sessions():
    firewall.authorize(s["ip"]);firewall.apply_speed(s["ip"],s["speed_mbps"])
