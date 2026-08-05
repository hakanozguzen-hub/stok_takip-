import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Özelleştirilebilir Stok & Cari Yönetimi",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎨 BURADAN RENK VE YAZILARI DEĞİŞTİREBİLİRSİNİZ (CSS AYARLARI) ---
GÖRSEL_AYARLAR = """
<style>
    .stApp {
        background-color: #00000;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] ***, [data-testid="stSidebar"] p {
        color: #f8fafc !important;
    }
    .cari-baslik {
        color: #2563eb;
        font-size: 24px;
        font-weight: bold;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
</style>
"""
st.markdown(GÖRSEL_AYARLAR, unsafe_allow_html=True)

# --- VERİTABANI BAĞLANTISI ---
conn = sqlite3.connect("stok_takip_modern.db", check_same_thread=False)
cursor = conn.cursor()

# 1. Ana Tabloyu Oluştur (Eğer hiç yoksa)
cursor.execute("""
CREATE TABLE IF NOT EXISTS urunler (
    urun_kodu TEXT PRIMARY KEY,
    urun_adi TEXT,
    kategori TEXT,
    kritik_stok INTEGER
)""")

# 🔥 KESİN ÇÖZÜM: 'birim_fiyat' sütunu eski veritabanında yoksa otomatik ekle
try:
    cursor.execute("ALTER TABLE urunler ADD COLUMN birim_fiyat REAL DEFAULT 0.0")
    conn.commit()
except sqlite3.OperationalError:
    # Sütun zaten varsa hata verir, pas geçiyoruz
    pass

# 2. Hareket Tablosunu Oluştur
cursor.execute("""
CREATE TABLE IF NOT EXISTS stok_hareketleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urun_kodu TEXT,
    islem_turu TEXT,
    miktar INTEGER,
    tarih TEXT,
    aciklama TEXT,
    FOREIGN KEY(urun_kodu) REFERENCES urunler(urun_kodu)
)""")
conn.commit()


# --- MATEMATİKSEL HESAPLAMA FONKSİYONU ---
def stok_durumu_getir():
    cursor.execute("SELECT urun_kodu, urun_adi, kategori, kritik_stok, birim_fiyat FROM urunler")
    urunler = cursor.fetchall()
    
    stok_listesi = []
    for row in urunler:
        kod, ad, kat, kritik, fiyat = row[0], row[1], row[2], row[3], row[4]
        
        cursor.execute("SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu=? AND islem_turu='Giriş'", (kod,))
        giris_sonuc = cursor.fetchone()[0]
        giris = giris_sonuc if giris_sonuc is not None else 0
        
        cursor.execute("SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu=? AND islem_turu='Çıkış'", (kod,))
        cikis_sonuc = cursor.fetchone()[0]
        cikis = cikis_sonuc if cikis_sonuc is not None else 0
        
        kalan = giris - cikis
        durum = "⚠️ Kritik Seviye!" if kalan <= kritik else "✅ Stok Yeterli"
        toplam_deger = kalan * fiyat
        
        stok_listesi.append({
            "Ürün Kodu": kod,
            "Ürün Adı": ad,
            "Kategori": kat,
            "Birim Fiyat (TL)": fiyat,
            "Toplam Giriş": giris,
            "Toplam Çıkış": cikis,
            "Mevcut Stok": kalan,
            "Stok Değeri (TL)": toplam_deger,
            "Kritik Limit": kritik,
            "Durum": durum
        })
    
    return pd.DataFrame(stok_listesi)


# --- 📋 DİNAMİK CARİ KART PENCERESİ ---
@st.dialog("📋 ÜRÜN CARİ KARTI VE DÜZENLEME")
def pencere_cari_kart(urun_kodu):
    cursor.execute("SELECT urun_kodu, urun_adi, kategori, kritik_stok, birim_fiyat FROM urunler WHERE urun_kodu=?", (urun_kodu,))
    urun = cursor.fetchone()
    
    if not urun:
        st.error("Ürün detayları bulunamadı!")
        return

    st.markdown(f"<div class='cari-baslik'>{urun[1]} ({urun[0]})</div>", unsafe_allow_html=True)
    
    st.subheader("⚙️ Kart Bilgilerini Düzenle")
    yeni_ad = st.text_input("Ürün Adı Güncelle", value=urun[1])
    yeni_kat = st.selectbox("Kategori Değiştir", ["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"], 
                            index=["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"].index(urun[2]) if urun[2] in ["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"] else 0)
    yeni_kritik = st.number_input("Kritik Stok Sınırı", value=int(urun[3]), min_value=0)
    yeni_fiyat = st.number_input("Birim Fiyat (TL)", value=float(urun[4]), min_value=0.0, step=0.5)
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 Değişiklikleri Kaydet", use_container_width=True, type="primary"):
            cursor.execute("""
                UPDATE urunler 
                SET urun_adi=?, kategori=?, kritik_stok=?, birim_fiyat=? 
                WHERE urun_kodu=?
            """, (yeni_ad.strip(), yeni_kat, yeni_kritik, yeni_fiyat, urun_kodu))
            conn.commit()
            st.success("Cari kart güncellendi!")
            st.rerun()
            
    with col_btn2:
        if st.button("🗑️ Ürün Kartını Tamamen Sil", use_container_width=True):
            cursor.execute("DELETE FROM urunler WHERE urun_kodu=?", (urun_kodu,))
            cursor.execute("DELETE FROM stok_hareketleri WHERE urun_kodu=?", (urun_kodu,))
            conn.commit()
            st.warning("Ürün silindi!")
            st.rerun()

    st.divider()
    
    st.subheader("📜 Bu Ürünün Cari Hareketleri")
    cursor.execute("SELECT tarih, islem_turu, miktar, aciklama FROM stok_hareketleri WHERE urun_kodu=? ORDER BY id DESC", (urun_kodu,))
    gecmis = cursor.fetchall()
    
    if gecmis:
        df_gecmis = pd.DataFrame(gecmis, columns=["Tarih", "İşlem", "Miktar", "Açıklama"])
        st.dataframe(df_gecmis, use_container_width=True, hide_index=True)
    else:
        st.caption("Bu ürüne ait henüz hiçbir işlem hareketi bulunmuyor.")


# --- DİĞER AÇILIR İŞLEM PENCERELERİ ---
@st.dialog("🆕 Yeni Ürün Kartı Tanımla")
def pencere_urun_ekle():
    kod = st.text_input("Ürün Kodu")
    ad = st.text_input("Ürün Adı")
    kat = st.selectbox("Kategori", ["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"])
    kritik = st.number_input("Kritik Limit", min_value=0, value=5)
    fiyat = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=0.0)
    
    if st.button("Kaydet", use_container_width=True, type="primary"):
        if kod and ad:
            try:
                cursor.execute("INSERT INTO urunler VALUES (?, ?, ?, ?, ?)", (kod.strip(), ad.strip(), kat, kritik, fiyat))
                conn.commit()
                st.success("Ürün kartı açıldı!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Bu kod zaten mevcut!")

@st.dialog("📥 Stok Girişi")
def pencere_stok_giris():
    df = stok_durumu_getir()
    if df.empty:
        st.warning("Önce ürün eklemelisiniz.")
        return
    secilen = st.selectbox("Ürün Seçin", df["Ürün Kodu"] + " - " + df["Ürün Adı"])
    kod = secilen.split(" - ")[0]
    miktar = st.number_input("Miktar", min_value=1, value=1)
    aciklama = st.text_input("Açıklama")
    
    if st.button("Girişi Onayla", use_container_width=True, type="primary"):
        cursor.execute("INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama) VALUES (?, 'Giriş', ?, ?, ?)",
                       (kod, miktar, datetime.now().strftime("%Y-%m-%d %H:%M"), aciklama))
        conn.commit()
        st.rerun()

@st.dialog("📤 Stok Çıkışı")
def pencere_stok_cikis():
    df = stok_durumu_getir()
    if df.empty:
        st.warning("Ürün bulunamadı.")
        return
    secilen = st.selectbox("Ürün Seçin", df["Ürün Kodu"] + " - " + df["Ürün Adı"])
    kod = secilen.split(" - ")[0]
    
    mevcut = int(df[df["Ürün Kodu"] == kod]["Mevcut Stok"].values[0])
    st.info(f"Depoda kalan miktar: {mevcut}")
    
    miktar = st.number_input("Miktar", min_value=1, max_value=max(1, mevcut), value=1)
    aciklama = st.text_input("Açıklama")
    
    if mevcut <= 0:
        st.error("Stokta bu üründen kalmadığı için çıkış yapamazsınız!")
        return
        
    if st.button("Çıkışı Onayla", use_container_width=True, type="primary"):
        cursor.execute("INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama) VALUES (?, 'Çıkış', ?, ?, ?)",
                       (kod, miktar, datetime.now().strftime("%Y-%m-%d %H:%M"), aciklama))
        conn.commit()
        st.rerun()


# --- ANA PANEL ARABİRİMİ ---
with st.sidebar:
    st.title("⚙️ İşlem Menüsü")
    if st.button("🆕 YENİ ÜRÜN KARTİ", use_container_width=True): pencere_urun_ekle()
    if st.button("📥 STOK GİRİŞİ YAP", use_container_width=True): pencere_stok_giris()
    if st.button("📤 STOK ÇIKIŞI YAP", use_container_width=True): pencere_stok_cikis()

st.title("📊 MAYRA PARK Stok & Cari Kontrol Paneli")

df_ana = stok_durumu_getir()

# Üst Sayaç Kartları
col1, col2, col3 = st.columns(3)
if not df_ana.empty:
    col1.metric("Toplam Çeşit", f"{len(df_ana)} Ürün")
    col2.metric("Toplam Stok Adedi", f"{int(df_ana['Mevcut Stok'].sum())} Adet")
    col3.metric("Toplam Depo Değeri", f"{df_ana['Stok Değeri (TL)'].sum():,.2f} TL")

st.divider()

# --- 🎯 SEÇİLEBİLİR TABLO ALANI ---
st.subheader("📦 Mevcut Stok Durumu ve Kalan Listesi")
st.caption("💡 Detaylarını görmek veya düzenlemek istediğiniz ürünün solundaki kutucuğu işaretleyin. Cari Kart penceresi otomatik açılacaktır.")

if df_ana.empty:
    st.info("💡 Sistemde henüz ürün bulunmuyor. Sol menüden yeni bir ürün kartı açarak başlayabilirsiniz.")
else:
    secim_takibi = st.dataframe(
        df_ana,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Mevcut Stok": st.column_config.ProgressColumn("Mevcut Stok", format="%d", min_value=0, max_value=1000)
        }
    )
    
