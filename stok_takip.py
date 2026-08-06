import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Detaylı Cari & Stok Yönetimi",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎨 GÖRSEL TASARIM VE RENK AYARLARI (CSS) ---
GÖRSEL_AYARLAR = """
<style>
    /* 📌 UYGULAMANIN GENEL ARKA PLAN RENGİ */
    .stApp {
        background-color: #f8fafc !important; /* Temiz modern açık gri-beyaz */
    }

    /* 📌 ORTADAKİ TÜM YAZILARIN RENGİ (Görünmeme sorununu çözer) */
    .stApp [data-testid="stHeader"], .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span, .stApp label {
        color: #0f172a !important; /* Yazıları tamamen okunur koyu lacivert yapar */
    }

    /* 📌 SOL PANELİN (SIDEBAR) ARKA PLAN RENGİ */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important; /* Şık koyu lacivert/karbon */
    }
    
    /* Sol paneldeki başlık ve yazıların renkleri (Beyaz kalmalı) */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    /* 📌 ANA İŞLEM BUTONLARININ RENGİ (Mavi Butonlar) */
    div[data-testid="stBaseButton-primary"] button {
        background-color: #0284c7 !important; /* Canlı kurumsal mavi */
        color: #ffffff !important; /* Yazı rengi beyaz */
        border-radius: 6px !important;
        border: none !important;
    }

    /* 📌 STANDART BUTONLARIN RENGİ */
    div[data-testid="stBaseButton-secondary"] button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* 📌 CARİ PENCERE BAŞLIĞI */
    .cari-baslik {
        color: #0284c7; font-size: 24px; font-weight: bold;
        border-bottom: 3px solid #0284c7; padding-bottom: 10px; margin-bottom: 20px;
    }
    
    /* 📐 PENCEREYİ DIŞA DOĞRU GENİŞLETEN CSS */
    div[data-testid="stDialog"] > div {
        max-width: 1400px !important;
        width: 85vw !important;
    }
</style>
"""
st.markdown(GÖRSEL_AYARLAR, unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
conn = sqlite3.connect("stok_takip_modern.db", check_same_thread=False)
cursor = conn.cursor()

# Tabloları Oluştur
cursor.execute("""
CREATE TABLE IF NOT EXISTS urunler (
    urun_kodu TEXT PRIMARY KEY,
    urun_adi TEXT,
    kategori TEXT,
    kritik_stok INTEGER DEFAULT 5
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stok_hareketleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urun_kodu TEXT,
    islem_turu TEXT,
    miktar INTEGER,
    tarih TEXT,
    aciklama TEXT,
    cari_unvan TEXT DEFAULT '-'
)""")
conn.commit()


# --- 🛠️ VERI ÇEKME YÖNTEMİ ---
def stok_durumu_getir():
    sorgu = """
    SELECT 
        u.urun_kodu AS [Ürün Kodu],
        u.urun_adi AS [Ürün Adı],
        u.kategori AS [Kategori],
        IFNULL((SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu = u.urun_kodu AND islem_turu = 'Giriş'), 0) AS [Toplam Giriş],
        IFNULL((SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu = u.urun_kodu AND islem_turu = 'Çıkış'), 0) AS [Toplam Çıkış],
        u.kritik_stok AS [Kritik Limit]
    FROM urunler u
    """
    df = pd.read_sql_query(sorgu, conn)
    
    if not df.empty:
        df["Mevcut Stok"] = df["Toplam Giriş"] - df["Toplam Çıkış"]
        df["Durum"] = df.apply(lambda r: "⚠️ Kritik" if r["Mevcut Stok"] <= r["Kritik Limit"] else "✅ Yeterli", axis=1)
    else:
        df = pd.DataFrame(columns=["Ürün Kodu", "Ürün Adı", "Kategori", "Toplam Giriş", "Toplam Çıkış", "Mevcut Stok", "Kritik Limit", "Durum"])
        
    return df


# --- 📋 ÜRÜN CARİ KARTI VE DETAYLI İŞLEM GEÇMİŞİ PENCERESİ ---
@st.dialog("📋 ÜRÜN CARİ KARTI VE DETAYLI İŞLEM GEÇMİŞİ")
def pencere_cari_kart(urun_kodu):
    cursor.execute("SELECT urun_kodu, urun_adi, kategori, kritik_stok FROM urunler WHERE urun_kodu=?", (str(urun_kodu),))
    urun = cursor.fetchone()
    
    if not urun:
        st.error("Ürün detayları bulunamadı!")
        return

    st.markdown(f"<div class='cari-baslik'>{urun[1]} ({urun[0]}) Cari Kartı</div>", unsafe_allow_html=True)
    
    st.subheader("📜 Detaylı Cari Hareket Geçmişi (Ekstre)")
    cursor.execute("""
        SELECT tarih, islem_turu, miktar, cari_unvan, aciklama 
        FROM stok_hareketleri 
        WHERE urun_kodu=? 
        ORDER BY id DESC
    """, (str(urun_kodu),))
    gecmis = cursor.fetchall()
    
    if gecmis:
        df_gecmis = pd.DataFrame(gecmis, columns=["Tarih / Saat", "İşlem Türü", "Miktar (Adet)", "Firma / Müşteri (Cari)", "Açıklama"])
        st.dataframe(df_gecmis, use_container_width=True, hide_index=True)
    else:
        st.info("💡 Bu ürüne ait henüz hiçbir alım veya teslimat kaydı bulunmuyor.")
    
    st.divider()
    
    st.subheader("⚙️ Kart Bilgilerini Düzenle / Değiştir")
    yeni_ad = st.text_input("Ürün Adı Güncelle", value=urun[1])
    yeni_kat = st.selectbox("Kategori Değiştir", ["Genel", "Temizlik", "Gıda", "Tekstil", "Hırdavat", "Diğer"], 
                            index=["Genel", "Temizlik", "Gıda", "Tekstil", "Hırdavat", "Diğer"].index(urun[2]) if urun[2] in ["Genel", "Temizlik", "Gıda", "Tekstil", "Hırdavat", "Diğer"] else 0)
    yeni_kritik = st.number_input("Kritik Stok Sınırı", value=int(urun[3] if urun[3] is not None else 5), min_value=0)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Değişiklikleri Kaydet", use_container_width=True, type="primary"):
            cursor.execute("""
                UPDATE urunler SET urun_adi=?, kategori=?, kritik_stok=? WHERE urun_kodu=?
            """, (yeni_ad.strip(), yeni_kat, yeni_kritik, str(urun_kodu)))
            conn.commit()
            st.success("Cari kart başarıyla güncellendi!")
            st.rerun()
            
    with col_btn2:
        if st.button("🗑️ Ürün Kartını Sistemden Sil", use_container_width=True):
            cursor.execute("DELETE FROM urunler WHERE urun_kodu=?", (str(urun_kodu),))
            cursor.execute("DELETE FROM stok_hareketleri WHERE urun_kodu=?", (str(urun_kodu),))
            conn.commit()
            st.warning("Ürün ve tüm geçmiş silindi!")
            st.rerun()


# --- İŞLEM PENCERELERİ ---
@st.dialog("🆕 Yeni Ürün Kartı Tanımla")
def pencere_urun_ekle():
    kod = st.text_input("Ürün Kodu")
    ad = st.text_input("Ürün Adı")
    kat = st.selectbox("Kategori", ["Genel", "Temizlik", "Gıda", "Tekstil", "Hırdavat", "Diğer"])
    kritik = st.number_input("Kritik Limit", min_value=0, value=5)
    
    if st.button("Kaydet", use_container_width=True, type="primary"):
        if kod and ad:
            try:
                cursor.execute("INSERT INTO urunler (urun_kodu, urun_adi, kategori, kritik_stok) VALUES (?, ?, ?, ?)", 
                               (kod.strip(), ad.strip(), kat, kritik))
                conn.commit()
                st.success("Ürün kartı açıldı!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Bu kod zaten mevcut!")

@st.dialog("📥 Stok Girişi (Mal Alımı)")
def pencere_stok_giris():
    df = stok_durumu_getir()
    if df.empty:
        st.warning("Önce ürün eklemelisiniz.")
        return
    secilen = st.selectbox("Giriş Yapılacak Ürün", df["Ürün Kodu"] + " - " + df["Ürün Adı"])
    kod = secilen.split(" - ")[0]
    
    cari_unvan = st.text_input("Alınan Firma / Tedarikçi (Kimden Alındı?)")
    miktar = st.number_input("Giriş Miktarı (Adet)", min_value=1, value=1)
    
    # 📆 MANUEL TARİH GİRİŞ ALANI
    secilen_tarih = st.date_input("Alım Tarihi Seçin", value=datetime.now().date())
    aciklama = st.text_input("Açıklama (Fatura No vb.)")
    
    if st.button("Girişi Onayla", use_container_width=True, type="primary"):
        tarih_str = secilen_tarih.strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama, cari_unvan) 
            VALUES (?, 'Giriş', ?, ?, ?, ?)
        """, (str(kod), int(miktar), tarih_str, aciklama, cari_unvan))
        conn.commit()
        st.rerun()

@st.dialog("📤 Stok Çıkışı (Teslimat / Satış)")
def pencere_stok_cikis():
    df = stok_durumu_getir()
    if df.empty:
        st.warning("Ürün bulunamadı.")
        return
    secilen = st.selectbox("Çıkış Yapılacak Ürün", df["Ürün Kodu"] + " - " + df["Ürün Adı"])
    kod = secilen.split(" - ")[0]
    
    mevcut_row = df[df["Ürün Kodu"] == str(kod)]
    mevcut = int(mevcut_row["Mevcut Stok"].iloc[0]) if not mevcut_row.empty else 0
    st.info(f"Depoda kalan güncel miktar: {mevcut} Adet")
    
    cari_unvan = st.text_input("Teslim Edilen Kişi / Müşteri (Kime Verildi?)")
    miktar = st.number_input("Çıkış Miktarı (Adet)", min_value=1, max_value=max(1, mevcut), value=1)
    
    # 📆 MANUEL TARİH GİRİŞ ALANI
    secilen_tarih = st.date_input("Teslim Tarihi Seçin", value=datetime.now().date())
    aciklama = st.text_input("Açıklama")
    
    if mevcut <= 0:
        st.error("Stokta mal yok, çıkış yapılamaz!")
        return
        
    if st.button("Çıkışı Onayla", use_container_width=True, type="primary"):
        tarih_str = secilen_tarih.strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama, cari_unvan) 
            VALUES (?, 'Çıkış', ?, ?, ?, ?)
        """, (str(kod), int(miktar), tarih_str, aciklama, cari_unvan))
        conn.commit()
        st.rerun()


# --- 🎛️ ANA PANEL VE SIDEBAR MENÜSÜ ---
st.title("📦 MAYRA PARK Cari & Stok Yönetim Paneli")

# Filtreleri hazırlamak için başlangıç veri setini çekiyoruz
df_stok = stok_durumu_getir()

# --- 🔍 FİLTRELEME SEÇENEKLERİ (SIDEBAR ÜST KISIM) ---
with st.sidebar:
    st.header("⚡ Hızlı İşlemler")
    if st.button("🆕 Yeni Ürün Tanımla", use_container_width=True):
