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

# --- 🎨 GÖRSEL TASARIM AYARLARI (CSS) ---
GÖRSEL_AYARLAR = """
<style>
    .stApp { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, sans-serif; }
    h1, h2, h3 { color: #2c3e50 !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] ***, [data-testid="stSidebar"] p { color: #f8fafc !important; }
    .cari-baslik {
        color: #1e40af; font-size: 24px; font-weight: bold;
        border-bottom: 3px solid #3b82f6; padding-bottom: 10px; margin-bottom: 20px;
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
    kritik_stok INTEGER,
    birim_fiyat REAL DEFAULT 0.0
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


# --- 🛠️ GÜVENLİ VERI ÇEKME VE MATEMATİKSEL HESAPLAMA ---
def stok_durumu_getir():
    cursor.execute("SELECT urun_kodu, urun_adi, kategori, kritik_stok, birim_fiyat FROM urunler")
    urunler = cursor.fetchall()
    
    stok_listesi = []
    for row in urunler:
        kod = row[0]
        ad = row[1]
        kat = row[2]
        kritik = row[3]
        fiyat = row[4]
        
        # Girişleri topla
        cursor.execute("SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu=? AND islem_turu='Giriş'", (kod,))
        g_res = cursor.fetchone()
        giris = g_res[0] if g_res and g_res[0] is not None else 0
        
        # Çıkışları topla
        cursor.execute("SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu=? AND islem_turu='Çıkış'", (kod,))
        c_res = cursor.fetchone()
        cikis = c_res[0] if c_res and c_res[0] is not None else 0
        
        kalan = giris - cikis
        durum = "⚠️ Kritik" if kalan <= kritik else "✅ Yeterli"
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


# --- 📋 ÜRÜN CARİ KARTI VE DETAYLI İŞLEM GEÇMİŞİ PENCERESİ ---
@st.dialog("📋 ÜRÜN CARİ KARTI VE DETAYLI İŞLEM GEÇMİŞİ")
def pencere_cari_kart(urun_kodu):
    cursor.execute("SELECT urun_kodu, urun_adi, kategori, kritik_stok, birim_fiyat FROM urunler WHERE urun_kodu=?", (urun_kodu,))
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
    """, (urun_kodu,))
    gecmis = cursor.fetchall()
    
    if gecmis:
        df_gecmis = pd.DataFrame(gecmis, columns=["Tarih / Saat", "İşlem Türü", "Miktar (Adet)", "Firma / Müşteri (Cari)", "Açıklama"])
        st.dataframe(df_gecmis, use_container_width=True, hide_index=True)
    else:
        st.info("💡 Bu ürüne ait henüz hiçbir alım veya teslimat kaydı bulunmuyor.")
    
    st.divider()
    
    st.subheader("⚙️ Kart Bilgilerini Düzenle / Değiştir")
    yeni_ad = st.text_input("Ürün Adı Güncelle", value=urun[1])
    yeni_kat = st.selectbox("Kategori Değiştir", ["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"], 
                            index=["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"].index(urun[2]) if urun[2] in ["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"] else 0)
    yeni_kritik = st.number_input("Kritik Stok Sınırı", value=int(urun[3]), min_value=0)
    yeni_fiyat = st.number_input("Birim Fiyat (TL)", value=float(urun[4]), min_value=0.0, step=0.5)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Değişiklikleri Kaydet", use_container_width=True, type="primary"):
            cursor.execute("""
                UPDATE urunler SET urun_adi=?, kategori=?, kritik_stok=?, birim_fiyat=? WHERE urun_kodu=?
            """, (yeni_ad.strip(), yeni_kat, yeni_kritik, yeni_fiyat, urun_kodu))
            conn.commit()
            st.success("Cari kart başarıyla güncellendi!")
            st.rerun()
            
    with col_btn2:
        if st.button("🗑️ Ürün Kartını Sistemden Sil", use_container_width=True):
            cursor.execute("DELETE FROM urunler WHERE urun_kodu=?", (urun_kodu,))
            cursor.execute("DELETE FROM stok_hareketleri WHERE urun_kodu=?", (urun_kodu,))
            conn.commit()
            st.warning("Ürün ve tüm geçmiş silindi!")
            st.rerun()


# --- DİĞER İŞLEM PENCERELERİ ---
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
    aciklama = st.text_input("Açıklama (Fatura No vb.)")
    
    if st.button("Girişi Onayla", use_container_width=True, type="primary"):
        cursor.execute("""
            INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama, cari_unvan) 
            VALUES (?, 'Giriş', ?, ?, ?, ?)
        """, (kod, miktar, datetime.now().strftime("%Y-%m-%d %H:%M"), aciklama, cari_unvan))
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
    
    mevcut = int(df[df["Ürün Kodu"] == kod]["Mevcut Stok"].values[0])
    st.info(f"Depoda kalan güncel miktar: {mevcut} Adet")
    
    cari_unvan = st.text_input("Teslim Edilen Kişi / Müşteri (Kime Verildi?)")
    miktar = st.number_input("Çıkış Miktarı (Adet)", min_value=1, max_value=max(1, mevcut), value=1)
    aciklama = st.text_input("Açıklama")
    
    if mevcut <= 0:
        st.error("Stokta mal yok, çıkış yapılamaz!")
        return
        
    if st.button("Çıkışı Onayla", use_container_width=True, type="primary"):
        cursor.execute("""
            INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama, cari_unvan) 
            VALUES (?, 'Çıkış', ?, ?, ?, ?)
        """, (kod, miktar, datetime.now().strftime("%Y-%m-%d %H:%M"), aciklama, cari_unvan))
        conn.commit()
        st.rerun()


# --- ANA PANEL ARABİRİMİ ---
with st.sidebar:
    st.title("⚙️ İşlem Menüsü")
    if st.button("🆕 YENİ ÜRÜN KARTİ", use_container_width=True): pencere_urun_ekle()
    if st.button("📥 STOK GİRİŞİ YAP", use_container_width=True): pencere_stok_giris()
    if st.button("📤 STOK ÇIKIŞI YAP", use_container_width=True): pencere_stok_cikis()

st.title("📊 Gelişmiş Stok & Cari Kontrol Paneli")

# Dinamik Veriyi Çek
df_ana = stok_durumu_getir()

col1, col2, col3 = st.columns(3)
if not df_ana.empty:
    col1.metric("Toplam Çeşit", f"{len(df_ana)} Ürün")
    col2.metric("Toplam Stok Adedi", f"{int(df_ana['Mevcut Stok'].sum())} Adet")
    col3.metric("Toplam Depo Değeri", f"{df_ana['Stok Değeri (TL)'].sum():,.2f} TL")
else:
    col1.metric("Toplam Çeşit", "0 Ürün")
    col2.metric("Toplam Stok Adedi", "0 Adet")
    col3.metric("Toplam Depo Değeri", "0.00 TL")

st.divider()

st.subheader("📦 Mevcut Stok Durumu ve Kalan Listesi")

if df_ana.empty:
    st.info("💡 Sistemde henüz ürün bulunmuyor. Sol taraftaki 'YENİ ÜRÜN KARTİ' butonuna basarak ilk ürününüzü ekleyebilirsiniz.")
else:
    # 🔥 ARTIK ASLA KİLİTLENMEYEN SEÇİM VE TABLO ALANI
    col_ara, col_sec = st.columns([2, 1])
    
    with col_sec:
        # Cari kartı açmak için güvenli ve çökme ihtimali sıfır olan açılır menü
        urun_secenekleri = df_ana["Ürün Kodu"] + " - " + df_ana["Ürün Adı"]
