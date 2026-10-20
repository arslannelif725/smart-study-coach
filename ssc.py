import streamlit as st
import pandas as pd 
import sqlite3 
from datetime import datetime, date

# Sayfa yapılandırması
st.set_page_config(page_title='Akıllı Ders Takip Sistemi', page_icon=':bar_chart:', layout='wide')

DB_NAME = 'study_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Kullanıcılar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # 2. Günlük Plan Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            target_questions INTEGER NOT NULL,
            target_duration INTEGER NOT NULL,
            done_questions INTEGER DEFAULT 0,
            done_duration INTEGER DEFAULT 0,
            completion_rate REAL DEFAULT 0.0
        )
    ''')
    
    # 3. Deneme Analizi Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_name TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            wrong_count INTEGER NOT NULL,
            empty_count INTEGER NOT NULL,
            total_loss INTEGER NOT NULL,
            status TEXT DEFAULT 'Eksik'
        )
    ''')

    # <--- EN SON EKLENEN ÖZELLİK 1: Koç Notları Veritabanı Tablosu --->
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coach_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_text TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Veritabanını başlat
init_db()

# --- GİRİŞ / KAYIT FONKSİYONLARI ---
def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# --- VERİTABANI İŞLEM FONKSİYONLARI ---
def get_daily_plans(user_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM daily_plans WHERE user_id = ?', conn, params=(user_id,))
    conn.close()
    return df

def add_daily_plan(user_id, plan_date, subject, topic, target_q, target_t):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO daily_plans (user_id, plan_date, subject, topic, target_questions, target_duration)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, str(plan_date), subject, topic, target_q, target_t))
    conn.commit()
    conn.close()

def update_daily_progress(plan_id, done_q, done_t, completion_rate):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE daily_plans
        SET done_questions = ?, done_duration = ?, completion_rate = ?
        WHERE id = ?
    ''', (done_q, done_t, completion_rate, plan_id))
    conn.commit()
    conn.close()

def delete_daily_plan(plan_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM daily_plans WHERE id = ?', (plan_id,))
    conn.commit()
    conn.close()

def get_exam_analysis(user_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM exam_analysis WHERE user_id = ?', conn, params=(user_id,))
    conn.close()
    return df

def add_exam_analysis(user_id, exam_name, exam_date, subject, topic, wrong, empty):
    total_loss = wrong + empty
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exam_analysis (user_id, exam_name, exam_date, subject, topic, wrong_count, empty_count, total_loss, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Eksik')
    ''', (user_id, exam_name, str(exam_date), subject, topic, wrong, empty, total_loss))
    conn.commit()
    conn.close()

def update_exam_status(exam_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE exam_analysis SET status = ? WHERE id = ?', (status, exam_id))
    conn.commit()
    conn.close()

def delete_exam_analysis(exam_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM exam_analysis WHERE id = ?', (exam_id,))
    conn.commit()
    conn.close()

# <--- EN SON EKLENEN ÖZELLİK 1: Koç Notları Veritabanı Fonksiyonları --->
def get_coach_notes(user_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM coach_notes WHERE user_id = ? ORDER BY id DESC', conn, params=(user_id,))
    conn.close()
    return df

def add_coach_note(user_id, note_text, created_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO coach_notes (user_id, note_text, created_date)
        VALUES (?, ?, ?)
    ''', (user_id, note_text, str(created_date)))
    conn.commit()
    conn.close()

def delete_coach_note(note_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM coach_notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()


# --- GİRİŞ / KAYIT ARAYÜZ KONTROLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None

if not st.session_state.logged_in:
    st.title('🔐 Akıllı Ders Takip Sistemi - Giriş Ekranı')
    
    auth_tab1, auth_tab2 = st.tabs(['Giriş Yap', 'Kayıt Ol'])
    
    with auth_tab1:
        st.subheader('Hesabına Giriş Yap')
        with st.form('login_form'):
            l_user = st.text_input('Kullanıcı Adı')
            l_pass = st.text_input('Şifre', type='password')
            l_submit = st.form_submit_button('Giriş Yap')
            
            if l_submit:
                user_id = login_user(l_user, l_pass)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = l_user
                    st.success('Giriş başarılı!')
                    st.rerun()
                else:
                    st.error('Kullanıcı adı veya şifre hatalı!')
                    
    with auth_tab2:
        st.subheader('Yeni Hesap Oluştur')
        with st.form('register_form'):
            r_user = st.text_input('Yeni Kullanıcı Adı')
            r_pass = st.text_input('Yeni Şifre', type='password')
            r_submit = st.form_submit_button('Kayıt Ol')
            
            if r_submit:
                if r_user and r_pass:
                    if register_user(r_user, r_pass):
                        st.success('Kayıt oluşturuldu! Giriş yapabilirsiniz.')
                    else:
                        st.error('Bu kullanıcı adı zaten alınmış.')
                else:
                    st.warning('Lütfen tüm alanları doldurun.')
                    
    st.stop()


# --- ANA UYGULAMA ---
st.sidebar.write(f"👤 Aktif Kullanıcı: **{st.session_state.username}**")
if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()

st.title('Akıllı Ders ve Deneme Takip Sistemi')
st.write('Planını yap, günlük hedeflerini tamamla, haftalık/aylık başarılarını grafiklerle incele ve koç notlarınla motivasyonunu yüksek tut!')

# <--- EN SON EKLENEN ÖZELLİK 1: 3. Ana Sekme (Koç Notları) Eklendi --->
tab1, tab2, tab3 = st.tabs(['Günlük Plan & Analizler', 'Deneme Analizi', '📝 Koç Notları & Hedefler'])

# TAB 1: Günlük Plan ve Haftalık/Aylık/Grafik Takip
with tab1:
    st.header('1. Günlük Ders Planını Oluştur')
    
    with st.form('add_lesson_form'):
        col1, col2 = st.columns(2)
        with col1:
            plan_date = st.date_input('Plan Tarihi', value=date.today())
            subject = st.text_input('Ders Adı', placeholder='Matematik, Fizik...')
            topic = st.text_input('Konu Adı', placeholder='Fonksiyonlar, Optik...')
        with col2:
            target_questions = st.number_input('Hedef Soru Sayısı', min_value=1, value=30)
            target_duration = st.number_input('Hedef Çalışma Süresi (dk)', min_value=5, value=60)
            
        submit_plan = st.form_submit_button('Plana Ders Ekle')
        
        if submit_plan and subject and topic:
            add_daily_plan(st.session_state.user_id, plan_date, subject, topic, target_questions, target_duration)
            st.success(f"{subject} - {topic} başarıyla eklendi!")
            st.rerun()

    df_plans = get_daily_plans(st.session_state.user_id)

    if not df_plans.empty:
        df_plans['plan_date'] = pd.to_datetime(df_plans['plan_date']).dt.date
        
        st.markdown('---')
        st.subheader('2. İlerleme ve Performans Takibi')
        
        # <--- EN SON EKLENEN ÖZELLİK 2: Grafik Sekmesi (sub_tab4) İç Sekmelere Eklendi --->
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            'Günlük Planlar ve İlerleme', 
            '📅 Haftalık Analiz', 
            '📊 Aylık Analiz', 
            '📈 Başarı Grafikleri'
        ])
        
        with sub_tab1:
            total_completion_list = []
            for idx, row in df_plans.iterrows():
                with st.expander(f"Tarih: {row['plan_date']} | {row['subject']} - {row['topic']}", expanded=False):
                    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
                    
                    with c1:
                        st.write(f"**Hedef Soru:** {row['target_questions']} | **Hedef Süre:** {row['target_duration']} dk")
                    
                    with c2:
                        done_q = st.number_input(f"Çözülen Soru ({row['subject']})", min_value=0, value=int(row['done_questions']), key=f"done_q_{row['id']}")
                        done_t = st.number_input(f"Geçen Süre dk ({row['subject']})", min_value=0, value=int(row['done_duration']), key=f"done_t_{row['id']}")
                    
                    q_ratio = min((done_q / row['target_questions']), 1.0) if row['target_questions'] > 0 else 0
                    t_ratio = min((done_t / row['target_duration']), 1.0) if row['target_duration'] > 0 else 0
                    lesson_completion = round(((q_ratio + t_ratio) / 2) * 100, 1)
                    
                    if done_q != row['done_questions'] or done_t != row['done_duration']:
                        update_daily_progress(row['id'], done_q, done_t, lesson_completion)
                        st.rerun()

                    with c3:
                        st.metric('Ders Başarısı', f'%{lesson_completion}')
                        st.progress(lesson_completion / 100)

                    with c4:
                        st.write('')
                        if st.button('Sil', key=f"del_plan_{row['id']}", help='Bu dersi sil'):
                            delete_daily_plan(row['id'])
                            st.toast('Ders silindi.')
                            st.rerun()

                    total_completion_list.append(lesson_completion)

            if total_completion_list:
                avg_completion = round(sum(total_completion_list) / len(total_completion_list), 1)
                st.markdown('---')
                st.metric('GENEL ORTALAMA BAŞARI SKORU', f'%{avg_completion}')

        with sub_tab2:
            st.subheader('Son 7 Günlük Haftalık Performans')
            today = date.today()
            week_ago = today - pd.Timedelta(days=7)
            df_weekly = df_plans[df_plans['plan_date'] >= week_ago]
            
            if not df_weekly.empty:
                weekly_avg = round(df_weekly['completion_rate'].mean(), 1)
                st.metric('Haftalık Ortalama Başarı Oranı', f'%{weekly_avg}')
                
                display_weekly = df_weekly[['plan_date', 'subject', 'topic', 'target_questions', 'done_questions', 'completion_rate']].copy()
                display_weekly.columns = ['Tarih', 'Ders', 'Konu', 'Hedef Soru', 'Çözülen Soru', 'Başarı (%)']
                st.dataframe(display_weekly, use_container_width=True)
            else:
                st.info('Son 7 gün içinde kayıtlı ders planı bulunmuyor.')

        with sub_tab3:
            st.subheader('Son 30 Günlük Aylık Performans')
            month_ago = today - pd.Timedelta(days=30)
            df_monthly = df_plans[df_plans['plan_date'] >= month_ago]
            
            if not df_monthly.empty:
                monthly_avg = round(df_monthly['completion_rate'].mean(), 1)
                st.metric('Aylık Ortalama Başarı Oranı', f'%{monthly_avg}')
                
                display_monthly = df_monthly[['plan_date', 'subject', 'topic', 'target_questions', 'done_questions', 'completion_rate']].copy()
                display_monthly.columns = ['Tarih', 'Ders', 'Konu', 'Hedef Soru', 'Çözülen Soru', 'Başarı (%)']
                st.dataframe(display_monthly, use_container_width=True)
            else:
                st.info('Son 30 gün içinde kayıtlı ders planı bulunmuyor.')

        # <--- EN SON EKLENEN ÖZELLİK 2: Başarı Grafikleri Arayüz Kodu --->
        with sub_tab4:
            st.subheader('📈 Zaman İçindeki Başarı Grafiği')
            st.write('Günlük ders bazında başarı oranlarının seyri:')
            
            df_chart = df_plans[['plan_date', 'subject', 'completion_rate']].copy()
            df_grouped = df_chart.groupby(['plan_date', 'subject'])['completion_rate'].mean().unstack().fillna(0)
            
            if not df_grouped.empty:
                st.line_chart(df_grouped)
            else:
                st.info('Grafik oluşturmak için yeterli veri bulunmuyor.')

# TAB 2: Deneme Analizi
with tab2:
    st.header('Deneme Analizi ve Takip')
    
    with st.form('exam_form'):
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            exam_name = st.text_input('Deneme Yayın Adı', placeholder='Örn: 3D, Bilgi Sarmal...')
            exam_date = st.date_input('Deneme Yapıldığı Tarih', value=date.today(), key='e_date')
            exam_subject = st.text_input('Ders Adı', placeholder='Matematik, Fizik...', key='exam_subject')
        with e_col2:
            exam_topic = st.text_input('Konu', placeholder='İstatistik, Türev...', key='exam_topic')
            wrong_count = st.number_input('Yanlış Sayısı', min_value=0, value=1)
            empty_count = st.number_input('Boş Sayısı', min_value=0, value=0)
            
        submit_exam = st.form_submit_button('Deneme Analizine Ekle')
        
        if submit_exam and exam_name and exam_subject and exam_topic:
            add_exam_analysis(st.session_state.user_id, exam_name, exam_date, exam_subject, exam_topic, wrong_count, empty_count)
            st.success(f"{exam_name} deneme analizi kaydedildi!")
            st.rerun()

    df_exam = get_exam_analysis(st.session_state.user_id)

    if not df_exam.empty:
        st.markdown('---')
        st.subheader('2. Eksik Konular Listesi')
        
        for idx, row in df_exam.iterrows():
            ec1, ec2, ec3, ec4, ec5, ec6 = st.columns([2, 3, 2, 2, 2, 1])
            with ec1:
                st.write(f"**{row['exam_name']}**\n🗓️ {row['exam_date']}")
            with ec2:
                st.write(f"**{row['subject']}**\n*{row['topic']}*")
            with ec3:
                st.write(f"Yanlış: {row['wrong_count']} | Boş: {row['empty_count']}")
            with ec4:
                st.write(f"Toplam Kayıp: {row['total_loss']}")
            with ec5:
                is_checked = True if row['status'] == 'Çözüldü ✅' else False
                new_check = st.checkbox('Çözüldü', value=is_checked, key=f"check_{row['id']}")
                if new_check != is_checked:
                    new_status = 'Çözüldü ✅' if new_check else 'Eksik'
                    update_exam_status(row['id'], new_status)
                    st.rerun()
            with ec6:
                if st.button('Sil', key=f"del_exam_{row['id']}", help='Analizi Sil'):
                    delete_exam_analysis(row['id'])
                    st.toast('Kayıt silindi.')
                    st.rerun()

        display_df = df_exam[['exam_name', 'exam_date', 'subject', 'topic', 'wrong_count', 'empty_count', 'total_loss']].copy()
        display_df.columns = ['Yayın Adı', 'Deneme Tarihi', 'Ders', 'Konu', 'Yanlış', 'Boş', 'Toplam Kayıp']
        st.dataframe(display_df, use_container_width=True)

        st.markdown('---')
        st.subheader('Akıllı Öneriler')
        df_missing = df_exam[df_exam['status'] == 'Eksik']
        if not df_missing.empty:
            worst_topic = df_missing.sort_values(by='total_loss', ascending=False).iloc[0]
            st.warning(
                f"🚨 **DİKKAT KOÇ TAVSİYESİ:** **{worst_topic['exam_name']}** denemesinde ({worst_topic['exam_date']}) en çok net kaybettiğin konu "
                f"**{worst_topic['subject']}** dersinden **'{worst_topic['topic']}'** konusu (Toplam {worst_topic['total_loss']} kayıp)!"
            )
        else:
            st.success("🎉 Tebrikler! Deneme analizindeki tüm eksik konuları çözüp tamamladın!")
    else:
        st.info('Henüz Deneme Analizi eklemedin.')

# <--- EN SON EKLENEN ÖZELLİK 1: Koç Notları & Hedefler Arayüz Kodu --->
# TAB 3: Koç Notları & Hedefler
with tab3:
    st.header('📝 Koç Notları, Haftalık Hedefler ve Tavsiyeler')
    st.write('Bu alana haftalık hedeflerini, deneme sonu çıkarımlarını veya kendine hatırlatmak istediğin notları yazabilirsin.')
    
    with st.form('note_form'):
        note_text = st.text_area('Not / Hedef İçeriği', placeholder='Örn: Bu hafta mutlaka paragraf rutini oturulacak...')
        note_date = st.date_input('Tarih', value=date.today(), key='n_date')
        
        submit_note = st.form_submit_button('Notu Kaydet')
        if submit_note and note_text:
            add_coach_note(st.session_state.user_id, note_text, note_date)
            st.success('Not başarıyla kaydedildi!')
            st.rerun()

    df_notes = get_coach_notes(st.session_state.user_id)
    
    if not df_notes.empty:
        st.markdown('---')
        st.subheader('Kayıtlı Notların ve Hedeflerin')
        
        for idx, row in df_notes.iterrows():
            with st.container():
                nc1, nc2 = st.columns([5, 1])
                with nc1:
                    st.info(f"🗓️ **{row['created_date']}**\n\n{row['note_text']}")
                with nc2:
                    st.write('')
                    if st.button('Sil', key=f"del_note_{row['id']}"):
                        delete_coach_note(row['id'])
                        st.toast('Not silindi.')
                        st.rerun()
    else:
        st.info('Henüz kaydedilmiş bir koç notu veya hedef bulunmuyor.')
        


            

