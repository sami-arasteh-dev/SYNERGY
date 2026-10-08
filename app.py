
import os, json, sqlite3, secrets
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from openai import OpenAI

BASE = Path(__file__).resolve().parent
DB = BASE / "synergy.db"
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id=1),
        api_base TEXT DEFAULT 'https://api.gapgpt.app/v1',
        api_key TEXT DEFAULT '',
        model TEXT DEFAULT 'gpt-4o',
        temperature REAL DEFAULT 0.2,
        max_tokens INTEGER DEFAULT 6000,
        extra_headers TEXT DEFAULT '{}',
        updated_at TEXT
    );
    INSERT OR IGNORE INTO settings(id,updated_at) VALUES(1,datetime('now'));

    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'partner',
        description TEXT DEFAULT '',
        data TEXT DEFAULT '{}',
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        payload TEXT NOT NULL,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS saved_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_id INTEGER,
        card_json TEXT NOT NULL,
        created_at TEXT
    );
    """)
    c.commit(); c.close()

init_db()

def clean_json_text(s):
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.split("\n",1)[1] if "\n" in s else s
        if s.endswith("```"): s = s[:-3]
    a, b = s.find("{"), s.rfind("}")
    return s[a:b+1] if a >= 0 and b > a else s

def get_settings():
    r = db().execute("SELECT * FROM settings WHERE id=1").fetchone()
    return dict(r)

def call_model(system_prompt, user_prompt):
    s = get_settings()
    if not s["api_key"]:
        raise RuntimeError("API Key در تب «تنظیمات مدل» وارد نشده است.")
    client = OpenAI(
        base_url=s["api_base"] or None,
        api_key=s["api_key"],
        default_headers=json.loads(s["extra_headers"] or "{}")
    )
    kwargs = dict(
        model=s["model"],
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        temperature=float(s["temperature"] or 0.2),
        max_tokens=int(s["max_tokens"] or 6000)
    )
    r = client.chat.completions.create(**kwargs)
    return r.choices[0].message.content

SYSTEM_PROMPT = """
You are the intelligence engine of a B2B customer and sales synergy platform.
The platform has one AXIS organization and an unlimited number of OTHER organizations.
Organizations may be partners, suppliers, customers, prospects, or unrelated businesses.
Build a directed, weighted, explainable commercial synergy network centered on the AXIS.

Use the supplied organization data, optional manually entered business context, and any
relevant current public internet/news knowledge available to the model. Never invent
facts as if verified. Mark assumptions and external/current information explicitly.

Think in terms of:
- referral flows
- cross-selling
- reciprocal offers
- timed campaigns
- customer overlap
- complementary products/services
- geographic or audience fit
- seasonality
- capacity and operational feasibility
- commercial value
- risk
- confidence
- evidence

Edges must be directed and weighted. Weight is 0..100 and represents the strategic
strength of the proposed relationship, not a guaranteed financial result.

Return ONLY valid JSON in this exact conceptual structure:
{
 "summary": "...",
 "network_strategy": "...",
 "assumptions": ["..."],
 "external_signals": [{"signal":"...","source":"...","impact":"..."}],
 "nodes":[{"id":"...","label":"...","role":"axis|partner|customer|prospect|supplier|other","score":0}],
 "edges":[
   {"source":"...","target":"...","weight":0,"relationship":"...","reason":"...",
    "conditions":["..."],"offer":"...","timing":"...","confidence":0}
 ],
 "recommendations":[
   {"title":"...","priority":"high|medium|low","from":"...","to":"...",
    "offer":"...","customer_flow":"...",
    "commercial_logic":"...","implementation":"...",
    "expected_benefit":"...","risk":"...","confidence":0}
 ],
 "campaigns":[
   {"name":"...","sequence":[{"step":1,"action":"...","timing":"..."}]}
 ]
}
Do not claim actual discounts, customer identities, sales figures, news, or partnerships
unless present in the supplied data or clearly labeled as a proposal/assumption.
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/settings")
def settings_get():
    s = get_settings()
    s["api_key"] = ("*" * max(0, len(s["api_key"])-8) + s["api_key"][-8:]) if s["api_key"] else ""
    return jsonify(s)

@app.post("/api/settings")
def settings_save():
    data = request.get_json(force=True)
    c = db()
    old = c.execute("SELECT api_key FROM settings WHERE id=1").fetchone()["api_key"]
    key = data.get("api_key","")
    if key.startswith("*") and old:
        key = old
    headers = data.get("extra_headers","{}")
    if isinstance(headers, dict): headers = json.dumps(headers)
    c.execute("""UPDATE settings SET api_base=?,api_key=?,model=?,temperature=?,
                 max_tokens=?,extra_headers=?,updated_at=? WHERE id=1""",
              (data.get("api_base","https://api.gapgpt.app/v1"),
               key,data.get("model","gpt-4o"),float(data.get("temperature",0.2)),
               int(data.get("max_tokens",6000)),headers,datetime.now().isoformat()))
    c.commit(); c.close()
    return jsonify({"ok":True})

@app.get("/api/organizations")
def orgs():
    rows = db().execute("SELECT * FROM organizations ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/organizations")
def org_add():
    d=request.get_json(force=True)
    c=db()
    cur=c.execute("""INSERT INTO organizations(name,role,description,data,created_at)
                     VALUES(?,?,?,?,?)""",
                  (d["name"],d.get("role","partner"),d.get("description",""),
                   json.dumps(d.get("data",{}),ensure_ascii=False),datetime.now().isoformat()))
    c.commit()
    oid=cur.lastrowid
    c.close()
    return jsonify({"id":oid})

@app.put("/api/organizations/<int:oid>")
def org_update(oid):
    d=request.get_json(force=True); c=db()
    c.execute("""UPDATE organizations SET name=?,role=?,description=?,data=? WHERE id=?""",
              (d["name"],d.get("role","partner"),d.get("description",""),
               json.dumps(d.get("data",{}),ensure_ascii=False),oid))
    c.commit(); c.close()
    return jsonify({"ok":True})

@app.delete("/api/organizations/<int:oid>")
def org_delete(oid):
    c=db(); c.execute("DELETE FROM organizations WHERE id=?",(oid,)); c.commit(); c.close()
    return jsonify({"ok":True})

@app.post("/api/import")
def import_file():
    f=request.files.get("file")
    if not f: return jsonify({"error":"فایلی انتخاب نشده"}),400
    name=secure_filename(f.filename)
    path=UPLOADS/name; f.save(path)
    ext=path.suffix.lower()
    try:
        records=[]
        if ext==".json":
            records=json.loads(path.read_text(encoding="utf-8"))
            if isinstance(records,dict): records=[records]
        elif ext in (".csv",".txt"):
            import csv
            with open(path,encoding="utf-8-sig") as x:
                records=list(csv.DictReader(x))
        elif ext in (".xlsx",".xls"):
            import pandas as pd
            xl=pd.ExcelFile(path)
            for sheet in xl.sheet_names:
                df=pd.read_excel(path,sheet_name=sheet).fillna("")
                records.append({"sheet":sheet,"rows":df.to_dict(orient="records")})
        else:
            return jsonify({"error":"فرمت مجاز: CSV, JSON, XLSX, XLS"}),400
        return jsonify({"filename":name,"records":records})
    except Exception as e:
        return jsonify({"error":str(e)}),400

@app.post("/api/analyze")
def analyze():
    d=request.get_json(force=True)
    orgs_data=d.get("organizations",[])
    axis=d.get("axis")
    if not axis:
        return jsonify({"error":"مجموعه محور را انتخاب کنید."}),400
    context=d.get("context","")
    prompt=f"""
AXIS ORGANIZATION:
{json.dumps(axis,ensure_ascii=False,indent=2)}

OTHER ORGANIZATIONS:
{json.dumps(orgs_data,ensure_ascii=False,indent=2)}

USER-ENTERED BUSINESS CONTEXT:
{context}

TASK:
Create the most useful feasible commercial synergy network. Explore multiple directions
between organizations when justified. Do not assume every organization must connect.
Suggest reciprocal/referral/customer-flow mechanics, offer bands, timing, conditions and
campaign sequences. If numerical offers are proposed, label them as proposed ranges or
examples, not facts. Current internet/news information may be used if actually available
to the model; cite source names/URLs in external_signals when used.
"""
    try:
        raw=call_model(SYSTEM_PROMPT,prompt)
        result=json.loads(clean_json_text(raw))
    except Exception as e:
        return jsonify({"error":f"خطا در تحلیل مدل: {e}"}),500
    c=db()
    cur=c.execute("INSERT INTO analyses(title,payload,created_at) VALUES(?,?,?)",
                  (d.get("title","تحلیل شبکه هم‌افزایی"),json.dumps(result,ensure_ascii=False),
                   datetime.now().isoformat()))
    c.commit(); aid=cur.lastrowid; c.close()
    result["_analysis_id"]=aid
    return jsonify(result)

@app.get("/api/analyses")
def analyses():
    rows=db().execute("SELECT id,title,created_at,payload FROM analyses ORDER BY id DESC").fetchall()
    out=[]
    for r in rows:
        x=dict(r); x["payload"]=json.loads(x["payload"]); out.append(x)
    return jsonify(out)

@app.get("/api/analyses/<int:aid>")
def analysis(aid):
    r=db().execute("SELECT * FROM analyses WHERE id=?",(aid,)).fetchone()
    if not r:return jsonify({"error":"یافت نشد"}),404
    x=dict(r); x["payload"]=json.loads(x["payload"]); return jsonify(x)

@app.post("/api/cards")
def save_card():
    d=request.get_json(force=True)
    c=db()
    cur=c.execute("INSERT INTO saved_cards(analysis_id,card_json,created_at) VALUES(?,?,?)",
                  (d.get("analysis_id"),json.dumps(d["card"],ensure_ascii=False),datetime.now().isoformat()))
    c.commit(); cid=cur.lastrowid; c.close()
    return jsonify({"id":cid})

@app.get("/api/cards")
def cards():
    rows=db().execute("SELECT * FROM saved_cards ORDER BY id DESC").fetchall()
    return jsonify([{**dict(r),"card_json":json.loads(r["card_json"])} for r in rows])

@app.get("/api/export/<int:aid>")
def export_analysis(aid):
    r=db().execute("SELECT * FROM analyses WHERE id=?",(aid,)).fetchone()
    if not r:return jsonify({"error":"یافت نشد"}),404
    out=BASE/f"analysis_{aid}.json"
    out.write_text(json.dumps(json.loads(r["payload"]),ensure_ascii=False,indent=2),encoding="utf-8")
    return send_file(out,as_attachment=True,download_name=out.name,mimetype="application/json")

@app.get("/api/health")
def health():
    return jsonify({"ok":True,"time":datetime.now().isoformat()})

if __name__=="__main__":
    app.run(host="127.0.0.1",port=8500,debug=False)
