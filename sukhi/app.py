import os, sqlite3, secrets
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE=os.path.dirname(os.path.abspath(__file__)); DB=os.path.join(BASE,'jewellery.db'); UPLOADS=os.path.join(BASE,'static','uploads')
os.makedirs(UPLOADS,exist_ok=True)
app=Flask(__name__); app.secret_key=os.environ.get('SECRET_KEY',secrets.token_hex(32)); app.config['MAX_CONTENT_LENGTH']=8*1024*1024
ALLOWED={'png','jpg','jpeg','webp'}

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS metal_rates(id INTEGER PRIMARY KEY AUTOINCREMENT,rate_date TEXT UNIQUE NOT NULL,gold_24k REAL NOT NULL,silver REAL NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,metal TEXT NOT NULL,category TEXT NOT NULL,carat REAL,weight REAL NOT NULL DEFAULT 0,making_charges REAL NOT NULL DEFAULT 0,stone_charges REAL NOT NULL DEFAULT 0,other_charges REAL NOT NULL DEFAULT 0,cost_price REAL NOT NULL DEFAULT 0,mrp REAL NOT NULL DEFAULT 0,selling_price REAL NOT NULL DEFAULT 0,description TEXT DEFAULT '',image_filename TEXT DEFAULT '',active INTEGER NOT NULL DEFAULT 1,best_seller INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer_name TEXT NOT NULL,email TEXT,phone TEXT,amount REAL NOT NULL,status TEXT NOT NULL DEFAULT 'Pending',payment_id TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS site_settings(id INTEGER PRIMARY KEY CHECK(id=1),brand_name TEXT NOT NULL DEFAULT 'Sukhi Jewellers',announcement TEXT DEFAULT '',instagram TEXT DEFAULT '',facebook TEXT DEFAULT '',youtube TEXT DEFAULT '',pinterest TEXT DEFAULT '',snapchat TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS hero_slides(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT DEFAULT '',subtitle TEXT DEFAULT '',image_filename TEXT DEFAULT '',link_url TEXT DEFAULT '',active INTEGER NOT NULL DEFAULT 1,sort_order INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS nav_items(id INTEGER PRIMARY KEY AUTOINCREMENT,label TEXT NOT NULL,parent_id INTEGER,url TEXT DEFAULT '',sort_order INTEGER NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS home_sections(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,section_type TEXT NOT NULL DEFAULT 'products',sort_order INTEGER NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS section_products(id INTEGER PRIMARY KEY AUTOINCREMENT,section_id INTEGER NOT NULL,product_id INTEGER NOT NULL,short_name TEXT DEFAULT '',display_price REAL,sort_order INTEGER NOT NULL DEFAULT 0);
    ''')
    cols=[r['name'] for r in c.execute('PRAGMA table_info(products)').fetchall()]
    if 'best_seller' not in cols: c.execute('ALTER TABLE products ADD COLUMN best_seller INTEGER NOT NULL DEFAULT 0')
    if not c.execute('SELECT 1 FROM admins LIMIT 1').fetchone():
        c.execute('INSERT INTO admins(username,password_hash) VALUES(?,?)',(os.environ.get('ADMIN_USER','admin'),generate_password_hash(os.environ.get('ADMIN_PASSWORD','ChangeMe123!'))))
    today=datetime.now().strftime('%Y-%m-%d')
    if not c.execute('SELECT 1 FROM metal_rates WHERE rate_date=?',(today,)).fetchone(): c.execute('INSERT INTO metal_rates(rate_date,gold_24k,silver,created_at) VALUES(?,?,?,?)',(today,7500,95,datetime.now().isoformat()))
    if not c.execute('SELECT 1 FROM site_settings WHERE id=1').fetchone(): c.execute("INSERT INTO site_settings(id,brand_name,announcement) VALUES(1,'Sukhi Jewellers','Welcome to Sukhi Jewellers — discover our latest arrivals!')")
    if not c.execute('SELECT 1 FROM nav_items LIMIT 1').fetchone():
        for i,(label,url) in enumerate([('Home','/'),('Shop By Category','#'),('New Arrivals','/new-arrivals'),('Best Seller','/best-sellers'),('Info','#'),('Our Policy','#')]): c.execute('INSERT INTO nav_items(label,url,sort_order) VALUES(?,?,?)',(label,url,i))
        shop=c.execute("SELECT id FROM nav_items WHERE label='Shop By Category'").fetchone()['id']; info=c.execute("SELECT id FROM nav_items WHERE label='Info'").fetchone()['id']; pol=c.execute("SELECT id FROM nav_items WHERE label='Our Policy'").fetchone()['id']
        cats=['Anklet','Bracelet','Rings','Toe Rings','Earrings','Necklaces and Pendants','Mangalsutra','Chain','Nose Pins','Evil Eye','Kids/Baby','Pens','Rakhi','Personalized Jewellery','Phone Cases']
        infos=['Jobs','Blogs','About Us','Contact Us','Bulk Inquiry','Brand Story','Collab With Us','Track Your Order','Customer Reviews']
        policies=['Shipping Policy','Return & Exchange','Privacy Policy','Terms & Conditions','Jewellery Care']
        for parent,items in [(shop,cats),(info,infos),(pol,policies)]:
            for i,x in enumerate(items):
                slug=x.lower().replace(' ','-').replace('/','-').replace('&','and')
                prefix='/category/' if parent==shop else ('/info/' if parent==info else '/policy/')
                c.execute('INSERT INTO nav_items(label,parent_id,url,sort_order) VALUES(?,?,?,?)',(x,parent,prefix+slug,i))
    if not c.execute('SELECT 1 FROM hero_slides LIMIT 1').fetchone(): c.execute("INSERT INTO hero_slides(title,subtitle,sort_order) VALUES('Timeless jewellery, made for you','Discover our latest collection',0)")
    if not c.execute('SELECT 1 FROM home_sections LIMIT 1').fetchone():
        c.execute("INSERT INTO home_sections(title,section_type,sort_order) VALUES('Manifested by You. Crafted by Us.','products',1)"); c.execute("INSERT INTO home_sections(title,section_type,sort_order) VALUES('Shop by Price','price',2)")
    if not c.execute('SELECT 1 FROM products LIMIT 1').fetchone():
        rows=[('22K Floral Gold Ring','Gold','Rings',22,5.8,3500,0,0,45000,59999,52999,'Floral 22K gold ring.',0),('22K Classic Gold Chain','Gold','Chain',22,18.2,9500,0,0,125000,159999,149999,'Classic gold chain.',1),('Silver Heritage Ring','Silver','Rings',None,7.4,800,0,0,2200,3999,3299,'Sterling silver style ring.',0),('Diamond Solitaire Pendant','Diamond','Necklaces and Pendants',18,3.2,6000,10000,0,52000,74999,64999,'Diamond pendant in gold.',1)]
        for x in rows: c.execute('''INSERT INTO products(name,metal,category,carat,weight,making_charges,stone_charges,other_charges,cost_price,mrp,selling_price,description,best_seller,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',x+(datetime.now().isoformat(),))
    c.commit(); c.close()

def latest_rate():
    c=db(); r=c.execute('SELECT * FROM metal_rates ORDER BY rate_date DESC LIMIT 1').fetchone(); c.close(); return r

def carat_rate(gold24,carat): return gold24*float(carat)/24 if carat else 0

def price_data(p,rate):
    metal=carat_rate(rate['gold_24k'],p['carat'])*p['weight'] if p['metal']=='Gold' and p['carat'] else 0
    d=max(0,p['mrp']-p['selling_price']); pct=d/p['mrp']*100 if p['mrp'] else 0
    return metal,d,pct

def admin_required(fn):
    @wraps(fn)
    def w(*a,**kw): return fn(*a,**kw) if session.get('admin_id') else redirect(url_for('login',next=request.path))
    return w

def site_data():
    c=db(); settings=c.execute('SELECT * FROM site_settings WHERE id=1').fetchone(); parents=c.execute('SELECT * FROM nav_items WHERE parent_id IS NULL AND active=1 ORDER BY sort_order,id').fetchall(); nav=[]
    for p in parents: nav.append((p,c.execute('SELECT * FROM nav_items WHERE parent_id=? AND active=1 ORDER BY sort_order,id',(p['id'],)).fetchall()))
    slides=c.execute('SELECT * FROM hero_slides WHERE active=1 ORDER BY sort_order,id').fetchall(); sections=c.execute('SELECT * FROM home_sections WHERE active=1 ORDER BY sort_order,id').fetchall(); c.close(); return settings,nav,slides,sections

@app.context_processor
def globals_():
    settings,nav,slides,sections=site_data(); return {'latest_rate':latest_rate(),'logged_in':bool(session.get('admin_id')),'site_settings':settings,'nav_menu':nav,'hero_slides':slides,'home_sections':sections}

@app.route('/')
def home():
    c=db(); products=c.execute('SELECT * FROM products WHERE active=1 ORDER BY id DESC').fetchall(); c.close(); return render_template('home.html',products=products,rate=latest_rate(),price_data=price_data)
@app.route('/product/<int:pid>')
def product(pid):
    c=db(); p=c.execute('SELECT * FROM products WHERE id=? AND active=1',(pid,)).fetchone(); c.close(); return render_template('product.html',p=p,rate=latest_rate(),price_data=price_data) if p else ('Product not found',404)
@app.route('/new-arrivals')
def new_arrivals():
    c=db(); ps=c.execute('SELECT * FROM products WHERE active=1 ORDER BY created_at DESC').fetchall(); c.close(); return render_template('listing.html',title='New Arrivals',subtitle='Freshly added jewellery',products=ps,rate=latest_rate(),price_data=price_data)
@app.route('/best-sellers')
def best_sellers():
    c=db(); ps=c.execute('SELECT * FROM products WHERE active=1 AND best_seller=1 ORDER BY id DESC').fetchall(); c.close(); return render_template('listing.html',title='Best Sellers',subtitle='Jewellery loved by our customers',products=ps,rate=latest_rate(),price_data=price_data)
@app.route('/category/<path:category>')
def category(category):
    q=category.replace('-',' '); c=db(); ps=c.execute('SELECT * FROM products WHERE active=1 AND lower(category)=lower(?) ORDER BY id DESC',(q,)).fetchall(); c.close(); return render_template('listing.html',title=q.title(),subtitle='Explore the collection',products=ps,rate=latest_rate(),price_data=price_data)
@app.route('/price/<int:max_price>')
def price_page(max_price):
    c=db(); ps=c.execute('SELECT * FROM products WHERE active=1 AND selling_price<=? ORDER BY selling_price',(max_price,)).fetchall(); c.close(); return render_template('listing.html',title=f'Jewellery Under ₹{max_price:,}',subtitle='Curated picks within your budget',products=ps,rate=latest_rate(),price_data=price_data)
@app.route('/info/<path:slug>')
def info_page(slug): return render_template('content_page.html',title=slug.replace('-',' ').title())
@app.route('/policy/<path:slug>')
def policy_page(slug): return render_template('content_page.html',title=slug.replace('-',' ').title())
@app.route('/admin/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        c=db(); a=c.execute('SELECT * FROM admins WHERE username=?',(request.form['username'],)).fetchone(); c.close()
        if a and check_password_hash(a['password_hash'],request.form['password']): session['admin_id']=a['id']; session['admin_user']=a['username']; return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid username or password.','error')
    return render_template('login.html')
@app.route('/admin/logout')
def logout(): session.clear(); return redirect(url_for('home'))
@app.route('/admin')
@admin_required
def dashboard():
    c=db(); ps=c.execute('SELECT * FROM products ORDER BY id DESC').fetchall(); orders=c.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 10').fetchall(); c.close(); return render_template('dashboard.html',products=ps,orders=orders,rate=latest_rate(),price_data=price_data)
@app.route('/admin/rates',methods=['POST'])
@admin_required
def save_rate():
    date=request.form.get('rate_date') or datetime.now().strftime('%Y-%m-%d'); c=db(); c.execute('INSERT INTO metal_rates(rate_date,gold_24k,silver,created_at) VALUES(?,?,?,?) ON CONFLICT(rate_date) DO UPDATE SET gold_24k=excluded.gold_24k,silver=excluded.silver',(date,float(request.form['gold_24k']),float(request.form.get('silver') or 0),datetime.now().isoformat())); c.commit(); c.close(); flash('Metal rates saved.','success'); return redirect(url_for('dashboard'))
@app.route('/admin/product/new',methods=['GET','POST'])
@admin_required
def new_product():
    if request.method=='POST':
        f=request.files.get('image'); fn=''
        if f and f.filename:
            ext=f.filename.rsplit('.',1)[-1].lower();
            if ext not in ALLOWED: flash('Unsupported image type.','error'); return redirect(request.url)
            fn=secure_filename(f'{secrets.token_hex(8)}.{ext}'); f.save(os.path.join(UPLOADS,fn))
        c=db(); c.execute('''INSERT INTO products(name,metal,category,carat,weight,making_charges,stone_charges,other_charges,cost_price,mrp,selling_price,description,image_filename,best_seller,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(request.form['name'],request.form['metal'],request.form['category'],float(request.form['carat']) if request.form.get('carat') else None,float(request.form.get('weight') or 0),float(request.form.get('making_charges') or 0),float(request.form.get('stone_charges') or 0),float(request.form.get('other_charges') or 0),float(request.form.get('cost_price') or 0),float(request.form.get('mrp') or 0),float(request.form.get('selling_price') or 0),request.form.get('description',''),fn,1 if request.form.get('best_seller') else 0,datetime.now().isoformat())); c.commit(); c.close(); flash('Product added.','success'); return redirect(url_for('dashboard'))
    return render_template('product_form.html')
@app.route('/admin/product/<int:pid>/delete',methods=['POST'])
@admin_required
def delete_product(pid): c=db(); c.execute('UPDATE products SET active=0 WHERE id=?',(pid,)); c.commit(); c.close(); flash('Product archived.','success'); return redirect(url_for('dashboard'))
@app.route('/admin/site',methods=['GET','POST'])
@admin_required
def admin_site():
    c=db()
    if request.method=='POST':
        c.execute('UPDATE site_settings SET brand_name=?,announcement=?,instagram=?,facebook=?,youtube=?,pinterest=?,snapchat=? WHERE id=1',(request.form.get('brand_name','Sukhi Jewellers'),request.form.get('announcement',''),request.form.get('instagram',''),request.form.get('facebook',''),request.form.get('youtube',''),request.form.get('pinterest',''),request.form.get('snapchat','')))
        f=request.files.get('hero_image')
        if f and f.filename:
            ext=f.filename.rsplit('.',1)[-1].lower()
            if ext in ALLOWED:
                fn=secure_filename(f'hero_{secrets.token_hex(8)}.{ext}'); f.save(os.path.join(UPLOADS,fn)); c.execute('INSERT INTO hero_slides(title,subtitle,image_filename,sort_order) VALUES(?,?,?,?)',(request.form.get('hero_title',''),request.form.get('hero_subtitle',''),fn,0))
        c.commit(); c.close(); flash('Website settings saved.','success'); return redirect(url_for('admin_site'))
    settings=c.execute('SELECT * FROM site_settings WHERE id=1').fetchone(); slides=c.execute('SELECT * FROM hero_slides ORDER BY sort_order,id').fetchall(); c.close(); return render_template('admin_site.html',settings=settings,slides=slides)
@app.route('/admin/site/hero/<int:sid>/delete', methods=['POST'])
@admin_required
def delete_hero(sid):
    c = db()
    slide = c.execute('SELECT image_filename FROM hero_slides WHERE id=?', (sid,)).fetchone()
    if not slide:
        c.close()
        flash('Homepage image not found.', 'error')
        return redirect(url_for('admin_site'))

    filename = slide['image_filename']
    c.execute('DELETE FROM hero_slides WHERE id=?', (sid,))
    c.commit()
    c.close()

    # Delete the uploaded image file if it exists.
    if filename:
        filepath = os.path.join(UPLOADS, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
        except OSError:
            pass

    flash('Homepage image deleted.', 'success')
    return redirect(url_for('admin_site'))


@app.route('/admin/nav',methods=['GET','POST'])
@admin_required
def admin_nav():
    c=db()
    if request.method=='POST': c.execute('INSERT INTO nav_items(label,parent_id,url,sort_order) VALUES(?,?,?,?)',(request.form['label'],request.form.get('parent_id') or None,request.form.get('url',''),int(request.form.get('sort_order') or 10))); c.commit(); c.close(); flash('Navigation item added.','success'); return redirect(url_for('admin_nav'))
    parents=c.execute('SELECT * FROM nav_items WHERE parent_id IS NULL ORDER BY sort_order,id').fetchall(); items=c.execute('SELECT n.*,p.label parent_label FROM nav_items n LEFT JOIN nav_items p ON p.id=n.parent_id ORDER BY COALESCE(n.parent_id,n.id),n.sort_order,n.id').fetchall(); c.close(); return render_template('admin_nav.html',parents=parents,items=items)
@app.route('/api/rates')
def api_rates():
    r=latest_rate(); return jsonify(date=r['rate_date'],gold24k=r['gold_24k'],gold22k=carat_rate(r['gold_24k'],22),gold18k=carat_rate(r['gold_24k'],18),gold14k=carat_rate(r['gold_24k'],14),silver=r['silver'])
@app.route('/checkout',methods=['POST'])
def checkout():
    data=request.get_json(silent=True) or {}; amount=float(data.get('amount') or 0)
    if amount<=0:return jsonify(ok=False,error='Invalid amount'),400
    c=db(); cur=c.execute('INSERT INTO orders(customer_name,email,phone,amount,status,created_at) VALUES(?,?,?,?,?,?)',(data.get('name','Customer'),data.get('email',''),data.get('phone',''),amount,'Payment Pending',datetime.now().isoformat())); c.commit(); oid=cur.lastrowid; c.close(); return jsonify(ok=True,order_id=oid,message='Order created. Connect Razorpay server-side here.')
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
