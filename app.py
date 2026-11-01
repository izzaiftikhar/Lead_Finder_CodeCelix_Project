from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
import csv, io, sqlite3
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from backend.schemas import (
    HealthResponse,
    LeadsResponse,
    OptionsResponse,
    ResetDemoResponse,
    SearchRequest,
    SearchResponse,
)

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'lead_finder.db'
STATIC = ROOT / 'static'
SEED = [
('Palm Gate Realty','Dubai','Real Estate','https://palmgaterealty.example','+971 50 123 4567','Confirmed (demo)','MANUAL','NO',92,'WhatsApp contact link shown; no chatbot signal in sample notes.'),
('Crescent Keys Properties','Abu Dhabi','Real Estate','https://crescentkeys.example','+971 2 555 0182','Probable (demo)','UNKNOWN','UNKNOWN',68,'Mobile contact listed; WhatsApp link not independently verified.'),
('Harborline Medical Centre','Sharjah','Clinics','https://harborlineclinic.example','+971 6 555 0144','Confirmed (demo)','MANUAL','NO',89,'WhatsApp contact listed; sample inspection found no chatbot signal.'),
('Oasis Family Clinic','Dubai','Clinics','https://oasisfamilyclinic.example','+971 55 555 0119','Confirmed (demo)','AUTOMATED','YES',55,'Sample notes indicate a chat widget and automated WhatsApp greeting.'),
('Dune & Door Realty','Ajman','Real Estate','','+971 50 555 0190','Probable (demo)','UNKNOWN','UNKNOWN',61,'Website and automation need real-world verification.'),
('Blue Pearl Dermatology','Abu Dhabi','Clinics','https://bluepearlderm.example','+971 50 555 0121','Confirmed (demo)','MANUAL','NO',86,'Contact link and website status are illustrative only.'),
('Skyline Nest Properties','Dubai','Real Estate','https://skylinenest.example','+971 4 555 0170','Confirmed (demo)','AUTOMATED','YES',58,'Sample notes indicate a chatbot signature.'),
('Marina View Health Clinic','Ras Al Khaimah','Clinics','https://marinaviewhealth.example','+971 7 555 0166','Confirmed (demo)','MANUAL','NO',84,'Sample contact and chatbot findings are not verified.'),
('Cedar Stone Real Estate','Sharjah','Real Estate','https://cedarstone.example','+971 50 555 0133','Probable (demo)','UNKNOWN','NO',73,'WhatsApp status is probable; chatbot absence is illustrative.'),
('Nour Family Healthcare','Fujairah','Clinics','','+971 50 555 0155','Confirmed (demo)','MANUAL','UNKNOWN',77,'No website is listed in this sample record.'),
('Golden Sand Properties','Dubai','Real Estate','https://goldensands.example','+971 50 555 0101','Confirmed (demo)','MANUAL','NO',95,'Illustrative high-priority lead.'),
('Cove Medical & Wellness','Abu Dhabi','Clinics','https://covemedical.example','+971 2 555 0199','Probable (demo)','UNKNOWN','UNKNOWN',64,'Sample needs manual validation before outreach.')]

def connect():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    with connect() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS leads(
          id INTEGER PRIMARY KEY AUTOINCREMENT, business_name TEXT NOT NULL, country TEXT NOT NULL DEFAULT 'UAE',
          city TEXT NOT NULL, niche TEXT NOT NULL, website TEXT, whatsapp_number TEXT, whatsapp_status TEXT,
          automation_status TEXT, chatbot_status TEXT, lead_score INTEGER, evidence TEXT,
          source TEXT DEFAULT 'Seeded demo data', created_at TEXT)''')
        if c.execute('SELECT COUNT(*) FROM leads').fetchone()[0] == 0:
            now=datetime.now(timezone.utc).isoformat()
            for name,city,niche,site,phone,wa,auto,chat,score,evidence in SEED:
                c.execute('''INSERT INTO leads(business_name,country,city,niche,website,whatsapp_number,whatsapp_status,automation_status,chatbot_status,lead_score,evidence,source,created_at)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',(name,'UAE',city,niche,site,phone,wa,auto,chat,score,evidence,'Seeded demo data',now))

@asynccontextmanager
async def lifespan(app):
    init_db(); yield

app=FastAPI(title='CodeCelix Lead Finder Prototype',version='0.1.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=STATIC),name='static')
@app.get('/')
def home(): return FileResponse(STATIC/'index.html')
@app.get('/api/health', response_model=HealthResponse)
def health(): return {'status':'ok','mode':'demo-data','database':'SQLite','real_discovery':False}
@app.get('/api/options', response_model=OptionsResponse)
def options():
    with connect() as c:
        return {'countries':['UAE'],'cities':[r[0] for r in c.execute('SELECT DISTINCT city FROM leads ORDER BY city')], 'niches':[r[0] for r in c.execute('SELECT DISTINCT niche FROM leads ORDER BY niche')]}

def fetch_leads(country='UAE',niche='All',city='All',q='',whatsapp='All',chatbot='All',automation='All',hot_only=False,limit=200):
    sql='SELECT * FROM leads WHERE country=?'; args=[country]
    if niche!='All': sql+=' AND niche=?'; args.append(niche)
    if city!='All': sql+=' AND city=?'; args.append(city)
    if q.strip():
        sql+=' AND (LOWER(business_name) LIKE ? OR LOWER(city) LIKE ? OR LOWER(niche) LIKE ?)'; term='%'+q.strip().lower()+'%'; args += [term,term,term]
    if whatsapp!='All': sql+=' AND whatsapp_status LIKE ?'; args.append('%'+whatsapp+'%')
    if chatbot!='All': sql+=' AND chatbot_status=?'; args.append(chatbot)
    if automation!='All': sql+=' AND automation_status=?'; args.append(automation)
    if hot_only: sql+=" AND automation_status='MANUAL' AND chatbot_status='NO'"
    sql+=' ORDER BY lead_score DESC,business_name LIMIT ?'; args.append(limit)
    with connect() as c: return [dict(r) for r in c.execute(sql,args).fetchall()]

@app.get('/api/leads', response_model=LeadsResponse)
def leads(country:str='UAE',niche:str='All',city:str='All',q:str='',whatsapp:str='All',chatbot:str='All',automation:str='All',hot_only:bool=False,limit:int=Query(200,ge=1,le=200)):
    if country!='UAE': raise HTTPException(400,'This prototype currently supports UAE only.')
    return {'items':fetch_leads(country,niche,city,q,whatsapp,chatbot,automation,hot_only,limit),'demo':True}
@app.post('/api/search', response_model=SearchResponse)
def search(req:SearchRequest):
    if req.country!='UAE': raise HTTPException(400,'This prototype currently supports UAE only.')
    items=fetch_leads(req.country,req.niche,req.city,req.query,limit=req.limit)
    return {'job_id':'demo-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S'),'status':'completed','accepted':len(items),'requested':req.limit,'message':f'Demo search completed. {len(items)} sample records matched.','notice':'Illustrative sample records, not verified real businesses.','items':items}
@app.get('/api/export.csv')
def export_csv(country:str='UAE',niche:str='All',city:str='All',q:str='',whatsapp:str='All',chatbot:str='All',automation:str='All',hot_only:bool=False):
    items=fetch_leads(country,niche,city,q,whatsapp,chatbot,automation,hot_only,200)
    fields=['business_name','country','city','niche','website','whatsapp_number','whatsapp_status','automation_status','chatbot_status','lead_score','evidence','source']
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(items); out.seek(0)
    return StreamingResponse(iter([out.getvalue()]),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=codecelix-lead-finder-demo.csv'})
@app.post('/api/reset-demo', response_model=ResetDemoResponse)
def reset_demo():
    with connect() as c: c.execute('DELETE FROM leads')
    init_db(); return {'ok':True,'message':'Demo records reset.'}
