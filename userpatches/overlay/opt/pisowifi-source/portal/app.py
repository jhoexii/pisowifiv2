import os,subprocess,json
from functools import wraps
from flask import Flask,render_template,request,redirect,url_for,session,flash,jsonify
import db,firewall

db.init_db()
app=Flask(__name__)
app.secret_key=os.environ.get("APP_SECRET","dev-secret")
BRAND=os.environ.get("BRAND_NAME","PisoWiFi")
ADMIN_USER=os.environ.get("ADMIN_USERNAME","admin")
ADMIN_PASS=os.environ.get("ADMIN_PASSWORD","change-me")
PLANS_FILE="/etc/pisowifi/plans.json"

def plans():
    with open(PLANS_FILE) as f:return json.load(f)

def client_ip():
    return request.headers.get("X-Client-IP") or request.remote_addr or ""

def client_mac(ip):
    try:
        o=subprocess.check_output(["ip","neigh","show",ip],text=True)
        for x in o.split():
            if x.count(":")==5:return x
    except Exception: pass
    return ""

def admin_required(f):
    @wraps(f)
    def w(*a,**k):
        if not session.get("admin"): return redirect(url_for("login"))
        return f(*a,**k)
    return w

@app.get("/")
def index():
    s=db.session_for_ip(client_ip())
    return render_template("index.html",brand=BRAND,plans=plans(),session=s)

@app.post("/activate")
def activate():
    code=request.form.get("code","").strip().upper()
    ip=client_ip()
    result=db.activate(code,ip,client_mac(ip))
    if not result:
        flash("Voucher is invalid or already used.","error")
        return redirect(url_for("index"))
    firewall.authorize(ip)
    firewall.apply_speed(ip,result["speed_mbps"])
    return redirect(url_for("status"))

@app.get("/status")
def status():
    s=db.session_for_ip(client_ip())
    return render_template("status.html",brand=BRAND,session=s)

@app.get("/api/status")
def api_status():
    s=db.session_for_ip(client_ip())
    if not s:return jsonify({"active":False})
    return jsonify({"active":True,"expires_at":s["expires_at"],
                    "data_limit_mb":s["data_limit_mb"],
                    "data_used_mb":s["data_used_mb"],
                    "speed_mbps":s["speed_mbps"],
                    "plan":s["plan"]})

@app.get("/admin/login")
def login(): return render_template("login.html",brand=BRAND)

@app.post("/admin/login")
def login_post():
    if request.form.get("username")==ADMIN_USER and request.form.get("password")==ADMIN_PASS:
        session["admin"]=True;return redirect(url_for("admin"))
    flash("Invalid login.","error");return redirect(url_for("login"))

@app.post("/admin/logout")
def logout():session.clear();return redirect(url_for("login"))

@app.get("/admin")
@admin_required
def admin():
    return render_template("admin.html",brand=BRAND,stats=db.stats(),
                           sessions=db.active_sessions(),plans=plans())

@app.post("/admin/voucher")
@admin_required
def admin_voucher():
    p=request.form.get("price","10")
    x=plans().get(p)
    if not x: flash("Invalid plan.","error");return redirect(url_for("admin"))
    code=db.create_voucher(int(p),x["name"],x["minutes"],x["speed_mbps"],x["data_mb"])
    return render_template("generated.html",brand=BRAND,code=code,plan=x,price=p)

@app.get("/admin/coins")
@admin_required
def coin_info():
    return jsonify(db.stats())

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORTAL_PORT","8080")))
