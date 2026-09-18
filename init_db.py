import sqlite3

# יצירת חיבור למסד נתונים (ייצור את הקובץ אוטומטית אם אינו קיים)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# יצירת טבלה עבור הכתבות (הריבועים)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT,
        image TEXT
    )
''')

# הוספת נתוני דוגמה התחלתיים
cursor.execute('INSERT INTO articles (category, title, content) VALUES (?, ?, ?)',
               ('טכנולוגיה', 'מחשבים קוונטיים', 'פריצת דרך בעיבוד נתונים.'))
cursor.execute('INSERT INTO articles (category, title, content) VALUES (?, ?, ?)',
               ('כלכלה', 'עליה בביקוש ל-AI', 'השוק העולמי ממשיך להשקיע.'))

conn.commit()
conn.close()
print("מסד הנתונים נוצר בהצלחה!")