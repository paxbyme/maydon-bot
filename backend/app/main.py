import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB = Path(os.getenv('DATABASE_PATH', '/tmp/maydon.db'))
ADMIN_ID = os.getenv('ADMIN_TELEGRAM_ID', '')
app = FastAPI(title='MAYDON API')
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(','), allow_methods=['GET','POST'], allow_headers=['*'])

@contextmanager
def connection():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

@app.on_event('startup')
def init():
    with connection() as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS venues (id INTEGER PRIMARY KEY, name TEXT NOT NULL, sport TEXT NOT NULL, address TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, price INTEGER NOT NULL, phone TEXT, hours TEXT, owner_telegram_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending'); CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY, venue_id INTEGER NOT NULL, user_telegram_id TEXT NOT NULL, start_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', FOREIGN KEY(venue_id) REFERENCES venues(id));''')

class VenueIn(BaseModel):
    name: str = Field(min_length=2)
    sport: str
    address: str
    latitude: float
    longitude: float
    price: int = Field(ge=0)
    phone: str = ''
    hours: str = ''
    owner_telegram_id: str

class BookingIn(BaseModel):
    venue_id: int
    user_telegram_id: str
    start_at: datetime

@app.get('/health')
def health(): return {'status':'ok'}

@app.get('/venues')
def venues(sport: str | None = None):
    with connection() as db:
        rows = db.execute('SELECT * FROM venues WHERE status=?' + (' AND sport=?' if sport else ''), ('approved',sport) if sport else ('approved',)).fetchall()
        return [dict(r) for r in rows]

@app.post('/venues', status_code=201)
def request_venue(v: VenueIn):
    if v.sport not in ('football','table_tennis','billiards'): raise HTTPException(422, 'Unsupported sport')
    with connection() as db:
        cur=db.execute('INSERT INTO venues (name,sport,address,latitude,longitude,price,phone,hours,owner_telegram_id) VALUES (?,?,?,?,?,?,?,?,?)', tuple(v.model_dump().values()))
        return {'id':cur.lastrowid,'status':'pending'}

@app.get('/admin/venues')
def pending(x_telegram_user_id: str = Header(default='')):
    if not ADMIN_ID or x_telegram_user_id != ADMIN_ID: raise HTTPException(403, 'Admin only')
    with connection() as db: return [dict(r) for r in db.execute("SELECT * FROM venues WHERE status='pending'")]

@app.post('/admin/venues/{venue_id}/{decision}')
def decide(venue_id: int, decision: str, x_telegram_user_id: str = Header(default='')):
    if not ADMIN_ID or x_telegram_user_id != ADMIN_ID: raise HTTPException(403, 'Admin only')
    if decision not in ('approved','rejected'): raise HTTPException(400,'Invalid decision')
    with connection() as db:
        cur=db.execute('UPDATE venues SET status=? WHERE id=?',(decision,venue_id))
        if not cur.rowcount: raise HTTPException(404,'Venue not found')
        return {'status':decision}

@app.post('/bookings', status_code=201)
def book(b: BookingIn):
    if b.start_at.replace(tzinfo=b.start_at.tzinfo or timezone.utc) <= datetime.now(timezone.utc): raise HTTPException(422,'Booking must be in future')
    with connection() as db:
        venue=db.execute("SELECT id FROM venues WHERE id=? AND status='approved'",(b.venue_id,)).fetchone()
        if not venue: raise HTTPException(404,'Venue not found')
        cur=db.execute('INSERT INTO bookings (venue_id,user_telegram_id,start_at) VALUES (?,?,?)',(b.venue_id,b.user_telegram_id,b.start_at.isoformat()))
        return {'id':cur.lastrowid,'status':'pending'}

@app.get('/owner/bookings')
def owner_bookings(x_telegram_user_id: str = Header(default='')):
    if not x_telegram_user_id: raise HTTPException(401,'Missing owner ID')
    with connection() as db:
        return [dict(r) for r in db.execute('SELECT b.* FROM bookings b JOIN venues v ON v.id=b.venue_id WHERE v.owner_telegram_id=?',(x_telegram_user_id,))]

@app.post('/owner/bookings/{booking_id}/{decision}')
def owner_decide(booking_id:int,decision:str,x_telegram_user_id:str=Header(default='')):
    if decision not in ('confirmed','rejected'): raise HTTPException(400,'Invalid decision')
    with connection() as db:
        cur=db.execute("UPDATE bookings SET status=? WHERE id=? AND status='pending' AND venue_id IN (SELECT id FROM venues WHERE owner_telegram_id=?)",(decision,booking_id,x_telegram_user_id))
        if not cur.rowcount: raise HTTPException(404,'Pending booking not found for owner')
        return {'status':decision}
