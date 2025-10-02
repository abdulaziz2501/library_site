import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date, timedelta
import base64
from io import BytesIO
from PIL import Image
import os

# Sahifa konfiguratsiyasi
st.set_page_config(
    page_title="📚 MyLibrary - Kutubxona Tizimi",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# CSS stillari
def load_css():
    st.markdown("""
    <style>
    /* Umumiy stil */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .book-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        transition: transform 0.2s;
    }

    .book-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }

    .stats-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1rem;
    }

    .success-box {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }

    .warning-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }

    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .review-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 3px solid #ffc107;
    }

    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)


# Ma'lumotlar bazasini boshlash
def init_database():
    conn = sqlite3.connect('kutubxona.db', check_same_thread=False)
    cursor = conn.cursor()

    # Jadvallarni yaratish
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        full_name TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        bio TEXT,
        birth_date DATE,
        nationality TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author_id INTEGER,
        description TEXT,
        isbn TEXT,
        year INTEGER,
        pages INTEGER,
        language TEXT DEFAULT 'Uzbek',
        publisher TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES authors (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book_categories (
        book_id INTEGER,
        category_id INTEGER,
        PRIMARY KEY (book_id, category_id),
        FOREIGN KEY (book_id) REFERENCES books (id),
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book_copies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        barcode TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'available',
        condition TEXT DEFAULT 'good',
        location TEXT,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS borrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        copy_id INTEGER,
        borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        returned_at TIMESTAMP,
        fine_amount REAL DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (copy_id) REFERENCES book_copies (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER,
        user_id INTEGER,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    return conn


# Demo ma'lumotlarni qo'shish
def seed_demo_data(conn):
    cursor = conn.cursor()

    # Demo foydalanuvchi
    password_hash = hashlib.md5("demo123".encode()).hexdigest()
    cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, email, full_name, phone) 
    VALUES (?, ?, ?, ?, ?)
    ''', ("demo", password_hash, "demo@example.com", "Demo Foydalanuvchi", "+998901234567"))

    # Mualliflar
    authors_data = [
        ("O'tkir", "Hoshimov", "O'zbek yozuvchisi", "1941-01-01", "O'zbekiston"),
        ("Abdulla", "Qodiriy", "O'zbek adabiyotining asoschilaridan", "1894-04-10", "O'zbekiston"),
        ("Alisher", "Navoiy", "O'zbek shoiri va mutafakkiri", "1441-02-09", "O'zbekiston"),
        ("George", "Orwell", "Ingliz yozuvchisi", "1903-06-25", "Britaniya"),
        ("Harper", "Lee", "Amerika yozuvchisi", "1926-04-28", "AQSh")
    ]

    for author in authors_data:
        cursor.execute('''
        INSERT OR IGNORE INTO authors (first_name, last_name, bio, birth_date, nationality) 
        VALUES (?, ?, ?, ?, ?)
        ''', author)

    # Kategoriyalar
    categories_data = [
        ("Badiiy adabiyot", "Roman, hikoya va she'rlar"),
        ("Ilmiy", "Ilmiy tadqiqot va ma'lumotnomalar"),
        ("Tarix", "Tarixiy kitoblar"),
        ("Fantastika", "Ilmiy fantastika va fantazi"),
        ("Biografiya", "Shaxslar haqida kitoblar"),
        ("Dasturlash", "Programming va texnologiya")
    ]

    for category in categories_data:
        cursor.execute('INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)', category)

    # Kitoblar
    books_data = [
        ("Dunyoning ishlari", 1, "O'tkir Hoshimovning mashhur romani", "978-9943-01-234-5", 1974, 320, "O'zbek",
         "Sharq"),
        ("O'tkan kunlar", 2, "O'zbek adabiyotining durdona asari", "978-9943-01-345-6", 1925, 280, "O'zbek",
         "O'zbekiston"),
        ("1984", 4, "Dystopian social science fiction novel", "978-0451524935", 1949, 328, "English", "Penguin"),
        ("To Kill a Mockingbird", 5, "Classic novel about justice", "978-0061120084", 1960, 376, "English",
         "HarperCollins"),
        ("Xamsa", 3, "Navoiyning besh dostondan iborat asari", "978-9943-01-567-8", 1485, 450, "O'zbek", "Fan")
    ]

    for book in books_data:
        cursor.execute('''
        INSERT OR IGNORE INTO books (title, author_id, description, isbn, year, pages, language, publisher) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', book)

    # Kitob nusxalari
    copies_data = [
        (1, "UZ001-001", "available", "good", "A-1-01"),
        (1, "UZ001-002", "borrowed", "good", "A-1-02"),
        (2, "UZ002-001", "available", "excellent", "A-2-01"),
        (3, "EN003-001", "available", "good", "B-1-01"),
        (3, "EN003-002", "available", "fair", "B-1-02"),
        (4, "EN004-001", "borrowed", "good", "B-2-01"),
        (5, "UZ005-001", "available", "excellent", "A-3-01")
    ]

    for copy in copies_data:
        cursor.execute('''
        INSERT OR IGNORE INTO book_copies (book_id, barcode, status, condition, location) 
        VALUES (?, ?, ?, ?, ?)
        ''', copy)

    conn.commit()


# Foydalanuvchi autentifikatsiyasi
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def authenticate_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password_hash = ?',
                   (username, hash_password(password)))
    return cursor.fetchone()


def register_user(conn, username, password, email, full_name, phone):
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO users (username, password_hash, email, full_name, phone) 
        VALUES (?, ?, ?, ?, ?)
        ''', (username, hash_password(password), email, full_name, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


# Ma'lumotlarni olish funksiyalari
def get_books_with_authors(conn, search_query="", category_filter=""):
    cursor = conn.cursor()
    query = '''
    SELECT b.*, a.first_name, a.last_name, 
           COUNT(bc.id) as total_copies,
           COUNT(CASE WHEN bc.status = 'available' THEN 1 END) as available_copies
    FROM books b
    JOIN authors a ON b.author_id = a.id
    LEFT JOIN book_copies bc ON b.id = bc.book_id
    WHERE 1=1
    '''
    params = []

    if search_query:
        query += " AND (b.title LIKE ? OR a.first_name LIKE ? OR a.last_name LIKE ?)"
        search_param = f"%{search_query}%"
        params.extend([search_param, search_param, search_param])

    if category_filter:
        query += ''' AND b.id IN (
            SELECT bc.book_id FROM book_categories bc 
            JOIN categories c ON bc.category_id = c.id 
            WHERE c.name = ?
        )'''
        params.append(category_filter)

    query += " GROUP BY b.id ORDER BY b.created_at DESC"

    cursor.execute(query, params)
    return cursor.fetchall()


def get_user_borrows(conn, user_id, active_only=True):
    cursor = conn.cursor()
    query = '''
    SELECT br.*, bc.barcode, b.title, a.first_name, a.last_name, b.id as book_id
    FROM borrows br
    JOIN book_copies bc ON br.copy_id = bc.id
    JOIN books b ON bc.book_id = b.id
    JOIN authors a ON b.author_id = a.id
    WHERE br.user_id = ?
    '''
    params = [user_id]

    if active_only:
        query += " AND br.returned_at IS NULL"

    query += " ORDER BY br.borrowed_at DESC"

    cursor.execute(query, params)
    return cursor.fetchall()


def get_book_reviews(conn, book_id):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT r.*, u.username, u.full_name
    FROM reviews r
    JOIN users u ON r.user_id = u.id
    WHERE r.book_id = ?
    ORDER BY r.created_at DESC
    ''', (book_id,))
    return cursor.fetchall()


def get_statistics(conn):
    cursor = conn.cursor()

    # Umumiy statistika
    cursor.execute('SELECT COUNT(*) FROM books')
    total_books = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM book_copies')
    total_copies = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM borrows WHERE returned_at IS NULL')
    active_borrows = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM book_copies WHERE status = "available"')
    available_copies = cursor.fetchone()[0]

    return {
        'total_books': total_books,
        'total_copies': total_copies,
        'total_users': total_users,
        'active_borrows': active_borrows,
        'available_copies': available_copies
    }


# Asosiy dastur
def main():
    load_css()
    conn = init_database()
    seed_demo_data(conn)

    # Session state initialization
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    # Sidebar navigatsiya
    with st.sidebar:
        st.markdown("### 📚 MyLibrary")

        if st.session_state.user:
            st.success(f"Xush kelibsiz, {st.session_state.user[4]}!")

            menu_options = {
                "🏠 Bosh sahifa": "home",
                "📖 Kitoblar": "books",
                "👤 Mening profilim": "profile",
                "📊 Statistika": "statistics",
                "⭐ Sharh berish": "reviews"
            }

            # Admin menu
            if st.session_state.user[1] == "admin":
                menu_options.update({
                    "➕ Kitob qo'shish": "add_book",
                    "👥 Foydalanuvchilar": "users_admin"
                })

            selected_page = st.selectbox("Menyu", list(menu_options.keys()))
            st.session_state.page = menu_options[selected_page]

            if st.button("🚪 Chiqish", use_container_width=True):
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("### Kirish yoki Ro'yxatdan o'tish")
            auth_mode = st.radio("", ["Kirish", "Ro'yxatdan o'tish"])

            if auth_mode == "Kirish":
                with st.form("login_form"):
                    username = st.text_input("Foydalanuvchi nomi")
                    password = st.text_input("Parol", type="password")
                    submitted = st.form_submit_button("Kirish", use_container_width=True)

                    if submitted:
                        user = authenticate_user(conn, username, password)
                        if user:
                            st.session_state.user = user
                            st.success("Muvaffaqiyatli kirildi!")
                            st.rerun()
                        else:
                            st.error("Noto'g'ri foydalanuvchi nomi yoki parol!")
            else:
                with st.form("register_form"):
                    new_username = st.text_input("Foydalanuvchi nomi")
                    new_password = st.text_input("Parol", type="password")
                    email = st.text_input("Email")
                    full_name = st.text_input("To'liq ism")
                    phone = st.text_input("Telefon raqam")
                    submitted = st.form_submit_button("Ro'yxatdan o'tish", use_container_width=True)

                    if submitted:
                        if register_user(conn, new_username, new_password, email, full_name, phone):
                            st.success("Muvaffaqiyatli ro'yxatdan o'tdingiz! Endi kirishingiz mumkin.")
                        else:
                            st.error("Bu foydalanuvchi nomi allaqachon mavjud!")

        # Demo ma'lumot
        st.markdown("---")
        st.info("**Demo hisobni sinab ko'ring:**\nUsername: demo\nParol: demo123")

    # Asosiy kontent
    if st.session_state.page == 'home':
        show_home_page(conn)
    elif st.session_state.page == 'books':
        show_books_page(conn)
    elif st.session_state.page == 'profile':
        show_profile_page(conn)
    elif st.session_state.page == 'statistics':
        show_statistics_page(conn)
    elif st.session_state.page == 'reviews':
        show_reviews_page(conn)
    elif st.session_state.page == 'add_book':
        show_add_book_page(conn)


def show_home_page(conn):
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 MyLibrary - Kutubxona Tizimi</h1>
        <p>O'zbekistondagi eng yirik elektron kutubxona tizimiga xush kelibsiz!</p>
    </div>
    """, unsafe_allow_html=True)

    # Statistika kartlari
    stats = get_statistics(conn)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #667eea; margin: 0;">{stats['total_books']}</h2>
            <p style="margin: 0;">Jami kitoblar</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #f093fb; margin: 0;">{stats['available_copies']}</h2>
            <p style="margin: 0;">Mavjud nusxalar</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #84fab0; margin: 0;">{stats['total_users']}</h2>
            <p style="margin: 0;">Foydalanuvchilar</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #ffecd2; margin: 0;">{stats['active_borrows']}</h2>
            <p style="margin: 0;">Olingan kitoblar</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Yangi kitoblar
    st.markdown("### 📖 So'nggi qo'shilgan kitoblar")
    books = get_books_with_authors(conn)[:6]  # Faqat 6 ta kitob

    cols = st.columns(3)
    for i, book in enumerate(books):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="book-card">
                <h4>{book[1]}</h4>
                <p><strong>Muallif:</strong> {book[8]} {book[9]}</p>
                <p><strong>Yil:</strong> {book[5] or 'Nomalum'}</p>
                <p> < strong > Mavjud:</strong> {book[11]} ta nusxa</p>
                <p style="font-size: 0.9em; color: #666;">{book[2][:100]}...</p>
            </div>
            """, unsafe_allow_html=True)


def show_books_page(conn):
    st.markdown("# 📖 Kitoblar katalogi")

    # Qidiruv va filtrlar
    col1, col2 = st.columns([2, 1])

    with col1:
        search_query = st.text_input("🔍 Kitob yoki muallif nomi bo'yicha qidirish", key="search")

    with col2:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM categories ORDER BY name')
        categories = [row[0] for row in cursor.fetchall()]
        category_filter = st.selectbox("📂 Kategoriya", ["Barchasi"] + categories)
        if category_filter == "Barchasi":
            category_filter = ""

    # Kitoblar ro'yxati
    books = get_books_with_authors(conn, search_query, category_filter)

    if not books:
        st.info("Hech qanday kitob topilmadi.")
        return

    # Sahifalash
    books_per_page = 9
    total_pages = (len(books) - 1) // books_per_page + 1

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    # Sahifa navigatsiyasi
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        current_page = st.selectbox("Sahifa", range(1, total_pages + 1),
                                    index=st.session_state.current_page - 1)
        st.session_state.current_page = current_page

    # Sahifa uchun kitoblarni olish
    start_idx = (current_page - 1) * books_per_page
    end_idx = start_idx + books_per_page
    page_books = books[start_idx:end_idx]

    # Kitoblarni ko'rsatish
    cols = st.columns(3)
    for i, book in enumerate(page_books):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div class="book-card">
                    <h4>{book[1]}</h4>
                    <p><strong>Muallif:</strong> {book[8]} {book[9]}</p>
                    <p><strong>Yil:</strong> {book[5] or 'Nomalum'}</p>
                < p > < strong > Sahifalar:</strong> {book[6] or 'Nomalum'}</p>
                < p > < strong > Til:</strong> {book[7]}</p>
                    <p><strong>Mavjud:</strong> {book[11]} / {book[10]} ta nusxa</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"📖 Batafsil", key=f"detail_{book[0]}"):
                    show_book_detail(conn, book[0])

                if st.session_state.user and book[11] > 0:
                    if st.button(f"📚 Kitobni olish", key=f"borrow_{book[0]}"):
                        borrow_book(conn, book[0], st.session_state.user[0])


def show_book_detail(conn, book_id):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT b.*, a.first_name, a.last_name 
    FROM books b 
    JOIN authors a ON b.author_id = a.id 
    WHERE b.id = ?
    ''', (book_id,))
    book = cursor.fetchone()

    if not book:
        st.error("Kitob topilmadi!")
        return

    st.markdown("---")
    st.markdown(f"## 📖 {book[1]}")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"**Muallif:** {book[8]} {book[9]}")
        st.markdown(f"**Yil:** {book[5] or 'Noma\'lum'}")
        st.markdown(f"**Sahifalar:** {book[6] or 'Noma\'lum'}")
        st.markdown(f"**Til:** {book[7]}")
        st.markdown(f"**Nashriyot:** {book[9] or 'Noma\'lum'}")
        st.markdown(f"**ISBN:** {book[4] or 'Noma\'lum'}")

    with col2:
        # Kitob nusxalari
        cursor.execute('SELECT * FROM book_copies WHERE book_id = ?', (book_id,))
        copies = cursor.fetchall()

        st.markdown("### 📋 Mavjud nusxalar:")
        for copy in copies:
            status_color = "🟢" if copy[3] == "available" else "🔴"
            st.markdown(f"{status_color} {copy[2]} - {copy[4]} ({copy[5]})")

    if book[2]:
        st.markdown("### 📄 Tavsif:")
        st.markdown(book[2])

    # Sharhlar
    st.markdown("### ⭐ Sharhlar:")
    reviews = get_book_reviews(conn, book_id)

    if reviews:
        for review in reviews:
            stars = "⭐" * review[2]
            st.markdown(f"""
            <div class="review-card">
                <strong>{review[6] or review[5]}</strong> {stars}<br>
                <small>{review[4]}</small><br>
                {review[3]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Hali sharhlar yo'q.")


def borrow_book(conn, book_id, user_id):
    cursor = conn.cursor()

    # Mavjud nusxani topish
    cursor.execute('SELECT * FROM book_copies WHERE book_id = ? AND status = "available" LIMIT 1', (book_id,))
    copy = cursor.fetchone()

    if not copy:
        st.error("Hozirda bu kitobning mavjud nusxasi yo'q!")
        return

    # Kitobni olish
    due_date = (datetime.now() + timedelta(days=14)).date()

    cursor.execute('''
    INSERT INTO borrows (user_id, copy_id, due_date) 
    VALUES (?, ?, ?)
    ''', (user_id, copy[0], due_date))

    cursor.execute('UPDATE book_copies SET status = "borrowed" WHERE id = ?', (copy[0],))

    conn.commit()

    st.success(f"Kitob muvaffaqiyatli olindi! Qaytarish muddati: {due_date}")
    st.rerun()


def show_profile_page(conn):
    if not st.session_state.user:
        st.error("Profilni ko'rish uchun tizimga kiring!")
        return

    user = st.session_state.user
    st.markdown(f"# 👤 {user[4]}ning profili")

    # Foydalanuvchi ma'lumotlari
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Foydalanuvchi nomi:** {user[1]}")
        st.markdown(f"**Email:** {user[3]}")
        st.markdown(f"**Telefon:** {user[5]}")

    with col2:
        st.markdown(f"**Ro'yxatdan o'tgan:** {user[6][:10]}")

    st.markdown("---")

    # Faol qarzlar
    st.markdown("### 📚 Olingan kitoblar")
    active_borrows = get_user_borrows(conn, user[0], active_only=True)

    if active_borrows:
        for borrow in active_borrows:
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"**{borrow[5]}**")
                st.markdown(f"Muallif: {borrow[6]} {borrow[7]}")

            with col2:
                st.markdown(f"Olingan: {borrow[3][:10]}")
                st.markdown(f"Qaytarish: {borrow[4]}")

                # Muddati o'tganligini tekshirish
                if borrow[4]:
                    due_date = datetime.strptime(borrow[4], '%Y-%m-%d').date()
                    if date.today() > due_date:
                        days_overdue = (date.today() - due_date).days
                        st.error(f"⚠️ {days_overdue} kun muddati o'tgan!")

            with col3:
                if st.button(f"Qaytarish", key=f"return_{borrow[0]}"):
                    return_book(conn, borrow[0])
    else:
        st.info("Hozirda olingan kitoblar yo'q")

    st.markdown("---")

    # Tarix
    st.markdown("### 📜 Kitob olish tarixi")
    all_borrows = get_user_borrows(conn, user[0], active_only=False)

    if all_borrows:
        history_data = []
        for borrow in all_borrows:
            status = "✅ Qaytarilgan" if borrow[5] else "📖 Hozir o'qilmoqda"
            history_data.append({
                "Kitob": borrow[5],
                "Muallif": f"{borrow[6]} {borrow[7]}",
                "Olingan": borrow[3][:10] if borrow[3] else "N/A",
                "Qaytarilgan": borrow[5][:10] if borrow[5] else "-",
                "Status": status
            })

        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Tarix mavjud emas")


def return_book(conn, borrow_id):
    cursor = conn.cursor()

    # Qarz ma'lumotlarini olish
    cursor.execute('SELECT * FROM borrows WHERE id = ?', (borrow_id,))
    borrow = cursor.fetchone()

    if not borrow:
        st.error("Qarz topilmadi!")
        return

    # Jarima hisobla
    fine = 0
    if borrow[4]:
        due_date = datetime.strptime(borrow[4], '%Y-%m-%d').date()
        if date.today() > due_date:
            days_overdue = (date.today() - due_date).days
            fine = days_overdue * 1000  # 1000 so'm kuniga

    # Kitobni qaytarish
    cursor.execute('''
    UPDATE borrows SET returned_at = CURRENT_TIMESTAMP, fine_amount = ? 
    WHERE id = ?
    ''', (fine, borrow_id))

    cursor.execute('UPDATE book_copies SET status = "available" WHERE id = ?', (borrow[2],))

    conn.commit()

    if fine > 0:
        st.warning(f"Kitob qaytarildi. Jarima: {fine:,} so'm")
    else:
        st.success("Kitob muvaffaqiyatli qaytarildi!")

    st.rerun()


def show_statistics_page(conn):
    st.markdown("# 📊 Kutubxona statistikasi")

    stats = get_statistics(conn)
    cursor = conn.cursor()

    # Umumiy statistika
    st.markdown("### 📈 Umumiy ko'rsatkichlar")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Jami kitoblar", stats['total_books'])
        st.metric("Jami nusxalar", stats['total_copies'])

    with col2:
        st.metric("Foydalanuvchilar", stats['total_users'])
        st.metric("Faol qarzlar", stats['active_borrows'])

    with col3:
        st.metric("Mavjud nusxalar", stats['available_copies'])
        availability_rate = (stats['available_copies'] / stats['total_copies'] * 100) if stats[
                                                                                             'total_copies'] > 0 else 0
        st.metric("Mavjudlik darajasi", f"{availability_rate:.1f}%")

    st.markdown("---")

    # Eng mashhur kitoblar
    st.markdown("### 🏆 Eng ko'p o'qilgan kitoblar")

    cursor.execute('''
    SELECT b.title, a.first_name || ' ' || a.last_name as author, COUNT(br.id) as borrow_count
    FROM books b
    JOIN authors a ON b.author_id = a.id
    LEFT JOIN book_copies bc ON b.id = bc.book_id
    LEFT JOIN borrows br ON bc.id = br.copy_id
    GROUP BY b.id
    HAVING borrow_count > 0
    ORDER BY borrow_count DESC
    LIMIT 10
    ''')

    popular_books = cursor.fetchall()

    if popular_books:
        df_popular = pd.DataFrame(popular_books, columns=['Kitob', 'Muallif', 'O\'qishlar soni'])
        st.dataframe(df_popular, use_container_width=True)
    else:
        st.info("Ma'lumot mavjud emas")

    st.markdown("---")

    # Kategoriyalar statistikasi
    st.markdown("### 📚 Kategoriyalar bo'yicha statistika")

    cursor.execute('''
    SELECT c.name, COUNT(DISTINCT bc.book_id) as book_count
    FROM categories c
    LEFT JOIN book_categories bc ON c.id = bc.category_id
    GROUP BY c.id
    ORDER BY book_count DESC
    ''')

    category_stats = cursor.fetchall()

    if category_stats:
        df_categories = pd.DataFrame(category_stats, columns=['Kategoriya', 'Kitoblar soni'])
        st.bar_chart(df_categories.set_index('Kategoriya'))

    st.markdown("---")

    # Tillar statistikasi
    st.markdown("### 🌍 Tillar bo'yicha taqsimot")

    cursor.execute('''
    SELECT language, COUNT(*) as count
    FROM books
    GROUP BY language
    ORDER BY count DESC
    ''')

    language_stats = cursor.fetchall()

    if language_stats:
        df_languages = pd.DataFrame(language_stats, columns=['Til', 'Soni'])

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(df_languages, use_container_width=True)
        with col2:
            st.bar_chart(df_languages.set_index('Til'))


def show_reviews_page(conn):
    if not st.session_state.user:
        st.error("Sharh qoldirish uchun tizimga kiring!")
        return

    st.markdown("# ⭐ Kitoblarga sharh qoldirish")

    cursor = conn.cursor()

    # Foydalanuvchi o'qigan kitoblarni olish
    cursor.execute('''
    SELECT DISTINCT b.id, b.title, a.first_name || ' ' || a.last_name as author
    FROM borrows br
    JOIN book_copies bc ON br.copy_id = bc.id
    JOIN books b ON bc.book_id = b.id
    JOIN authors a ON b.author_id = a.id
    WHERE br.user_id = ? AND br.returned_at IS NOT NULL
    ''', (st.session_state.user[0],))

    read_books = cursor.fetchall()

    if not read_books:
        st.info("Sharh qoldirish uchun avval kitoblarni o'qib qaytarishingiz kerak.")
        return

    # Sharh qoldirish formasi
    with st.form("review_form"):
        st.markdown("### 📝 Yangi sharh qo'shish")

        book_options = {f"{book[1]} - {book[2]}": book[0] for book in read_books}
        selected_book = st.selectbox("Kitobni tanlang", list(book_options.keys()))

        rating = st.slider("Baho", 1, 5, 3)
        st.markdown("⭐" * rating)

        review_text = st.text_area("Sharhingiz", height=100)

        submitted = st.form_submit_button("Sharh qo'shish", use_container_width=True)

        if submitted and review_text:
            book_id = book_options[selected_book]

            # Avvalgi sharhni tekshirish
            cursor.execute('''
            SELECT * FROM reviews 
            WHERE book_id = ? AND user_id = ?
            ''', (book_id, st.session_state.user[0]))

            existing_review = cursor.fetchone()

            if existing_review:
                # Sharhni yangilash
                cursor.execute('''
                UPDATE reviews 
                SET rating = ?, text = ?, created_at = CURRENT_TIMESTAMP
                WHERE book_id = ? AND user_id = ?
                ''', (rating, review_text, book_id, st.session_state.user[0]))
                st.success("Sharhingiz yangilandi!")
            else:
                # Yangi sharh qo'shish
                cursor.execute('''
                INSERT INTO reviews (book_id, user_id, rating, text)
                VALUES (?, ?, ?, ?)
                ''', (book_id, st.session_state.user[0], rating, review_text))
                st.success("Sharhingiz qo'shildi!")

            conn.commit()
            st.rerun()

    st.markdown("---")

    # Foydalanuvchi sharhlari
    st.markdown("### 📚 Mening sharhlarim")

    cursor.execute('''
    SELECT r.*, b.title, a.first_name || ' ' || a.last_name as author
    FROM reviews r
    JOIN books b ON r.book_id = b.id
    JOIN authors a ON b.author_id = a.id
    WHERE r.user_id = ?
    ORDER BY r.created_at DESC
    ''', (st.session_state.user[0],))

    user_reviews = cursor.fetchall()

    if user_reviews:
        for review in user_reviews:
            st.markdown(f"""
            <div class="review-card">
                <h4>{review[6]} - {review[7]}</h4>
                <p>{"⭐" * review[3]}</p>
                <p>{review[4]}</p>
                <small>Qo'shilgan: {review[5][:10]}</small>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"🗑️ O'chirish", key=f"delete_review_{review[0]}"):
                cursor.execute('DELETE FROM reviews WHERE id = ?', (review[0],))
                conn.commit()
                st.rerun()
    else:
        st.info("Hali sharhlar yo'q")


def show_add_book_page(conn):
    st.markdown("# ➕ Yangi kitob qo'shish")

    cursor = conn.cursor()

    with st.form("add_book_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Kitob nomi *", placeholder="Masalan: O'tkan kunlar")

            # Mualliflar ro'yxati
            cursor.execute('SELECT id, first_name, last_name FROM authors ORDER BY last_name')
            authors = cursor.fetchall()
            author_options = {f"{a[1]} {a[2]}": a[0] for a in authors}
            author_options["Yangi muallif qo'shish"] = -1

            selected_author = st.selectbox("Muallif *", list(author_options.keys()))

            if selected_author == "Yangi muallif qo'shish":
                st.markdown("#### Yangi muallif ma'lumotlari:")
                author_first = st.text_input("Muallif ismi *")
                author_last = st.text_input("Muallif familiyasi *")
                author_bio = st.text_area("Biografiya", height=100)
                author_birth = st.date_input("Tug'ilgan sanasi", value=None)
                author_nationality = st.text_input("Millati")

            isbn = st.text_input("ISBN", placeholder="978-9943-01-234-5")
            year = st.number_input("Nashr yili", min_value=1000, max_value=2025, value=2024)
            pages = st.number_input("Sahifalar soni", min_value=1, value=100)

        with col2:
            language = st.selectbox("Til", ["O'zbek", "English", "Русский", "Boshqa"])
            publisher = st.text_input("Nashriyot", placeholder="Masalan: Sharq")

            # Kategoriyalar
            cursor.execute('SELECT id, name FROM categories ORDER BY name')
            categories = cursor.fetchall()
            category_options = {c[1]: c[0] for c in categories}
            selected_categories = st.multiselect("Kategoriyalar", list(category_options.keys()))

            description = st.text_area("Kitob haqida", height=150)

            # Nusxalar
            st.markdown("#### Kitob nusxalari:")
            num_copies = st.number_input("Nusxalar soni", min_value=1, max_value=10, value=1)
            location_prefix = st.text_input("Joylashuv prefiksi", placeholder="A-1", value="A-1")

        submitted = st.form_submit_button("Kitobni qo'shish", use_container_width=True)

        if submitted:
            if not title:
                st.error("Kitob nomi kiritilishi shart!")
                return

            # Muallif qo'shish yoki olish
            if selected_author == "Yangi muallif qo'shish":
                if not author_first or not author_last:
                    st.error("Muallif ismi va familiyasi kiritilishi shart!")
                    return

                cursor.execute('''
                INSERT INTO authors (first_name, last_name, bio, birth_date, nationality)
                VALUES (?, ?, ?, ?, ?)
                ''', (author_first, author_last, author_bio,
                      author_birth.strftime('%Y-%m-%d') if author_birth else None,
                      author_nationality))
                author_id = cursor.lastrowid
            else:
                author_id = author_options[selected_author]

            # Kitob qo'shish
            cursor.execute('''
            INSERT INTO books (title, author_id, description, isbn, year, pages, language, publisher)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, author_id, description, isbn, year, pages, language, publisher))

            book_id = cursor.lastrowid

            # Kategoriyalarni bog'lash
            for cat_name in selected_categories:
                cat_id = category_options[cat_name]
                cursor.execute('''
                INSERT INTO book_categories (book_id, category_id)
                VALUES (?, ?)
                ''', (book_id, cat_id))

            # Nusxalarni qo'shish
            for i in range(num_copies):
                barcode = f"{language[:2].upper()}{book_id:03d}-{i + 1:03d}"
                location = f"{location_prefix}-{i + 1:02d}"

                cursor.execute('''
                INSERT INTO book_copies (book_id, barcode, status, condition, location)
                VALUES (?, ?, 'available', 'excellent', ?)
                ''', (book_id, barcode, location))

            conn.commit()

            st.success(f"✅ '{title}' kitobi va {num_copies} ta nusxasi muvaffaqiyatli qo'shildi!")
            st.balloons()


if __name__ == "__main__":
    main()