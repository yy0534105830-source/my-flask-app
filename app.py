import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'secret_key_for_session_management'
app.config['UPLOAD_FOLDER'] = 'static'

# חיבור למסד הנתונים
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# אתחול מסד הנתונים ויצירת הטבלאות הנדרשות
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # יצירת טבלת הגדרות האתר
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # יצירת טבלת משבצות התוכן והכתבות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slots (
            slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            content TEXT,
            image TEXT,
            width_val TEXT,
            height_val TEXT
        )
    ''')

    # יצירת טבלת מבזקים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT
        )
    ''')

    # יצירת טבלת פניות / הודעות מיצירת קשר
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # הגדרות ברירת מחדל לאתר
    default_settings = {
        'site_title': 'חדשות ועדכונים',
        'main_title': 'ברוכים הבאים לפורטל החדשות',
        'main_summary': 'כאן תמצאו את העדכונים החמים והמבזקים השוטפים בזמן אמת.',
        'bg_color': '#0f172a',
        'primary_color': '#3b82f6',
        'card_bg': '#1e293b'
    }

    for key, value in default_settings.items():
        cursor.execute('''
            INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)
        ''', (key, value))

    # יצירת משבצות ברירת מחדל אם הטבלה ריקה
    cursor.execute('SELECT COUNT(*) FROM slots')
    if cursor.fetchone()[0] == 0:
        default_slots = [
            ('כתבה ראשית 1', 'חדשות', 'תוכן הכתבה הראשונה מופיע כאן...', '', '300px', '350px'),
            ('כתבה ראשית 2', 'טכנולוגיה', 'תוכן הכתבה השנייה מופיע כאן...', '', '300px', '350px'),
            ('כתבה ראשית 3', 'כלכלה', 'תוכן הכתבה השלישית מופיע כאן...', '', '300px', '350px')
        ]
        cursor.executemany('''
            INSERT INTO slots (title, category, content, image, width_val, height_val)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', default_slots)

    # יצירת מבזק ברירת מחדל אם הטבלה ריקה
    cursor.execute('SELECT COUNT(*) FROM ticker')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO ticker (text) VALUES (?)', ('מבזק ראשון: ברוכים הבאים לאתר!',))

    conn.commit()
    conn.close()

# טעינת הגדרות האתר למילון
def get_site_settings():
    conn = get_db_connection()
    settings_rows = conn.execute('SELECT * FROM site_settings').fetchall()
    conn.close()
    return {row['key']: row['value'] for row in settings_rows}

# דף הבית
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if name and message:
            conn = get_db_connection()
            conn.execute('INSERT INTO messages (name, email, message) VALUES (?, ?, ?)',
                         (name, email, message))
            conn.commit()
            conn.close()

        return redirect(url_for('index'))

    settings = get_site_settings()
    conn = get_db_connection()
    slots = conn.execute('SELECT * FROM slots').fetchall()
    ticker = conn.execute('SELECT * FROM ticker').fetchall()
    conn.close()

    return render_template('index.html', settings=settings, slots=slots, ticker=ticker)

# דף התחברות לניהול
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == '1234password':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "שם משתמש או סיסמה שגויים", 401

    return '''
        <html lang="he" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>התחברות לניהול</title>
            <style>
                body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                form { background: #1e293b; padding: 30px; border-radius: 8px; display: flex; flex-direction: column; gap: 15px; width: 300px; }
                input { padding: 10px; border-radius: 4px; border: 1px solid #334155; background: #0f172a; color: white; }
                button { padding: 10px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            </style>
        </head>
        <body>
            <form method="POST">
                <h2>התחברות למערכת</h2>
                <input type="text" name="username" placeholder="שם משתמש" required>
                <input type="password" name="password" placeholder="סיסמה" required>
                <button type="submit">התחבר</button>
            </form>
        </body>
        </html>
    '''

# התנתקות
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# לוח בקרה וניהול
@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    settings = get_site_settings()
    conn = get_db_connection()
    slots = conn.execute('SELECT * FROM slots').fetchall()
    ticker = conn.execute('SELECT * FROM ticker').fetchall()
    messages = conn.execute('SELECT * FROM messages ORDER BY id DESC').fetchall()
    conn.close()

    return render_template('admin.html', settings=settings, slots=slots, ticker=ticker, messages=messages)

# עדכון הגדרות עיצוב וצבעים
@app.route('/admin/update_settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    for key in ['site_title', 'main_title', 'main_summary', 'bg_color', 'primary_color', 'card_bg']:
        value = request.form.get(key)
        if value is not None:
            conn.execute('UPDATE site_settings SET value = ? WHERE key = ?', (value, key))
    
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# הוספת משבצת חדשה
@app.route('/admin/add_slot', methods=['POST'])
def add_slot():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    title = request.form.get('title', 'משבצת חדשה')
    category = request.form.get('category', 'כללי')
    content = request.form.get('content', '')
    width_val = request.form.get('width_val', '300px')
    height_val = request.form.get('height_val', '350px')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO slots (title, category, content, image, width_val, height_val)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, category, content, '', width_val, height_val))
    
    slot_id = cursor.lastrowid

    file = request.files.get('image')
    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cursor.execute('UPDATE slots SET image = ? WHERE slot_id = ?', (filename, slot_id))

    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# עדכון משבצת
@app.route('/admin/edit_slot/<int:slot_id>', methods=['POST'])
def edit_slot(slot_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    width_val = request.form.get('width_val')
    height_val = request.form.get('height_val')

    conn = get_db_connection()
    conn.execute('''
        UPDATE slots 
        SET title = ?, category = ?, content = ?, width_val = ?, height_val = ?
        WHERE slot_id = ?
    ''', (title, category, content, width_val, height_val, slot_id))

    file = request.files.get('image')
    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn.execute('UPDATE slots SET image = ? WHERE slot_id = ?', (filename, slot_id))

    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# מחיקת משבצת
@app.route('/admin/delete_slot/<int:slot_id>')
def delete_slot(slot_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM slots WHERE slot_id = ?', (slot_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# הוספת מבזק
@app.route('/admin/add_ticker', methods=['POST'])
def add_ticker():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    text = request.form.get('ticker_text')
    if text:
        conn = get_db_connection()
        conn.execute('INSERT INTO ticker (text) VALUES (?)', (text,))
        conn.commit()
        conn.close()

    return redirect(url_for('admin_dashboard'))

# מחיקת מבזק
@app.route('/admin/delete_ticker/<int:ticker_id>')
def delete_ticker(ticker_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM ticker WHERE id = ?', (ticker_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# מחיקת פנייה
@app.route('/admin/delete_message/<int:msg_id>')
def delete_message(msg_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM messages WHERE id = ?', (msg_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# הצגת כתבה מלאה
@app.route('/article/<int:slot_id>')
def show_article(slot_id):
    settings = get_site_settings()
    conn = get_db_connection()
    slot = conn.execute('SELECT * FROM slots WHERE slot_id = ?', (slot_id,)).fetchone()
    conn.close()

    if not slot:
        return "הכתבה לא נמצאה", 404

    return render_template('index.html', settings=settings, slots=[slot], ticker=[])

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    
    init_db()
    app.run(debug=True)