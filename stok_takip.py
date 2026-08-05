import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Profesyonel Stok Takip Sistemi",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- VERİTABANI BAĞLANTISI ---
# Streamlit Cloud üzerinde sorunsuz çalışması için yerel SQLite bağlantısı
conn = sqlite3.connect("stok_takip_modern.db", check_same_thread=False)
cursor = conn.cursor()

# Tabloları Oluştur
cursor.execute("""
CREATE TABLE IF NOT EXISTS urunler (
    urun_kodu TEXT PRIMARY KEY,
    urun_adi TEXT,
    kategori TEXT,
    kritik_stok INTEGER
)""")

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
    """Tüm ürünlerin giriş, çıkış ve kalan miktarlarını hesaplar."""
    cursor.execute("SELECT urun_kodu, urun_adi, kategori, kritik_stok FROM urunler")
    urunler = cursor.fetchall()
    
    stok_listesi = []
    for kod, ad, kat, kritik in urunler:
        # Girişleri Topla
        cursor.execute("SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu=? AND islem_turu='Giriş'", (kod,))
        giris_sonuc = cursor.fetchone()[0]
        giris = giris_sonuc if giris_sonuc is not None else 0
        
        # Çıkışları Topla
        cursor.execute("SELECT SUM(miktar) FROM stok_hareketleri WHERE urun_kodu=? AND islem_turu='Çıkış'", (kod,))
        cikis_sonuc = cursor.fetchone()[0]
        cikis = cikis_sonuc if cikis_sonuc is not None else 0
        
        kalan = giris - cikis
        durum = "⚠️ Kritik Seviye!" if kalan <= kritik else "✅ Stok Yeterli"
        
        stok_listesi.append({
            "Ürün Kodu": kod,
            "Ürün Adı": ad,
            "Kategori": kat,
            "Toplam Giriş": giris,
            "Toplam Çıkış": cikis,
            "Mevcut Stok": kalan,
            "Kritik Limit": kritik,
            "Durum": durum
        })
    
    return pd.DataFrame(stok_listesi)


# --- MASAÜSTÜ TARZI AÇILIR PENCERELER (DIALOGS) ---

@st.dialog("🆕 Yeni Ürün Kartı Tanımla")
def pencere_urun_ekle():
    st.write("Sisteme ilk kez girecek ürünlerin kimlik kartını oluşturun.")
    kod = st.text_input("Ürün Kodu (Örn: STK-001)", key="ekle_kod")
    ad = st.text_input("Ürün Adı", key="ekle_ad")
    kat = st.selectbox("Kategori", ["Genel", "Elektronik", "Gıda", "Tekstil", "Hırdavat", "Diğer"])
    kritik = st.number_input("Kritik Stok Limiti (Bu miktarın altına düşünce uyarı verir)", min_value=0, value=5)
    
    if st.button("Ürün Kartını Kaydet", use_container_width=True, type="primary"):
        if kod and ad:
            try:
                cursor.execute("INSERT INTO urunler VALUES (?, ?, ?, ?)", (kod.strip(), ad.strip(), kat, kritik))
                conn.commit()
                st.success(f"'{ad}' başarıyla tanımlandı!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Bu ürün kodu sistemde zaten kayıtlı!")
        else:
            st.warning("Lütfen boş alan bırakmayınız.")

@st.dialog("📥 Stok Girişi (Depoya Mal Kabul)")
def pencere_stok_giris():
    df_urunler = stok_durumu_getir()
    if df_urunler.empty:
        st.warning("Önce ürün kartı oluşturmalısınız!")
        return
        
    secenekler = df_urunler["Ürün Kodu"] + " - " + df_urunler["Ürün Adı"]
    secilen = st.selectbox("Giriş Yapılacak Ürün", secenekler)
    kod = secilen.split(" - ")[0]
    
    miktar = st.number_input("Giriş Miktarı", min_value=1, value=1)
    aciklama = st.text_input("Açıklama / Fatura No / Tedarikçi")
    
    if st.button("Stok Girişini Onayla", use_container_width=True, type="primary"):
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama) VALUES (?, 'Giriş', ?, ?, ?)",
                       (kod, miktar, tarih, aciklama))
        conn.commit()
        st.success("Stok girişi başarıyla kaydedildi!")
        st.rerun()

@st.dialog("📤 Stok Çıkışı (Satış / Depodan Çıkış)")
def pencere_stok_cikis():
    df_stok = stok_durumu_getir()
    if df_stok.empty:
        st.warning("Sistemde ürün bulunmuyor!")
        return
        
    secenekler = df_stok["Ürün Kodu"] + " - " + df_stok["Ürün Adı"]
    secilen = st.selectbox("Çıkış Yapılacak Ürün", secenekler)
    kod = secilen.split(" - ")[0]
    
    # Mevcut stoğu bul ki eksiye düşmesin
    mevcut = df_stok[df_stok["Ürün Kodu"] == kod]["Mevcut Stok"].values[0]
    st.info(f"Bu üründen depoda şu an **{mevcut}** adet var.")
    
    miktar = st.number_input("Çıkış Miktarı", min_value=1, max_value=int(mevcut) if mevcut > 0 else 1, value=1)
    aciklama = st.text_input("Açıklama / Müşteri Adı / Sevkiyat No")
    
    if mevcut <= 0:
        st.error("Depoda bu üründen kalmadığı için çıkış yapamazsınız!")
        return

    if st.button("Stok Çıkışını Onayla", use_container_width=True, type="primary"):
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("INSERT INTO stok_hareketleri (urun_kodu, islem_turu, miktar, tarih, aciklama) VALUES (?, 'Çıkış', ?, ?, ?)",
                       (kod, miktar, tarih, aciklama))
        conn.commit()
        st.success("Stok çıkışı başarıyla kaydedildi!")
        st.rerun()


# --- ANA PANEL TASARIMI ---

# Yan Menü (Sidebar) Kontrolleri
with st.sidebar:
    st.image("https://flaticon.com", width=100)
    st.title("Kontrol Paneli")
    st.write("Aşağıdaki butonları kullanarak açılır pencereler üzerinden işlemlerinizi yapabilirsiniz.")
    st.divider()
    
    if st.button("🆕 YENİ ÜRÜN KARTİ", use_container_width=True):
        pencere_urun_ekle()
        
    if st.button("📥 STOK GİRİŞİ YAP", use_container_width=True):
        pencere_stok_giris()
        
    if st.button("📤 STOK ÇIKIŞI YAP", use_container_width=True):
        pencere_stok_cikis()
    
    st.divider()
    st.caption("Gelişmiş Masaüstü Görünümlü Stok Takip v2.0")

# Ana Sayfa İçeriği
st.title("📊 İşyeri Stok Yönetim Paneli")
st.write("Mevcut depolarınızdaki ürün durumları, kalanlar ve kritik seviyeler anlık olarak aşağıdadır.")

# Özet Kartları (KPI Metrics)
df_ana = stok_durumu_getir()

col1, col2, col3, col4 = st.columns(4)
if not df_ana.empty:
    toplam_kart = len(df_ana)
    toplam_stok_adet = df_ana["Mevcut Stok"].sum()
    kritik_adet = len(df_ana[df_ana["Mevcut Stok"] <= df_ana["Kritik Limit"]])
    
    col1.metric("Toplam Ürün Çeşidi", f"{toplam_kart} Çeşit")
    col2.metric("Depodaki Toplam Mal", f"{toplam_stok_adet} Adet", delta="Aktif")
    col3.metric("Kritik Stok Uyarıları", f"{kritik_adet} Ürün", delta="-Dikkat" if kritik_adet > 0 else "0", delta_color="inverse")
    col4.metric("Veritabanı Durumu", "Bağlı", delta="Güvenli")
else:
    col1.metric("Toplam Ürün Çeşidi", "0")
    col2.metric("Depodaki Toplam Mal", "0")
    col3.metric("Kritik Stok Uyarıları", "0")
    col4.metric("Veritabanı Durumu", "Bağlı")

st.divider()

# --- ANA TABLO GÖRÜNÜMÜ ---
st.subheader("📦 Mevcut Stok Durumu ve Kalan Listesi")

if df_ana.empty:
    st.info("💡 Henüz hiç ürün eklenmemiş. Sol menüden 'Yeni Ürün Kartı' oluşturarak başlayın.")
else:
    # Filtreleme Seçeneği
    arama = st.text_input("🔍 Ürün Adı veya Koduna Göre Hızlı Ara...", "")
    if arama:
        df_ana = df_ana[df_ana["Ürün Adı"].str.contains(arama, case=False) | df_ana["Ürün Kodu"].str.contains(arama, case=False)]
    
    # Renkli ve modern tablo gösterimi
    st.dataframe(
        df_ana,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Mevcut Stok": st.column_config.ProgressColumn(
                "Mevcut Stok",
                help="Depoda kalan net miktar",
                format="%d",
                min_value=0,
                max_value=int(df_ana["Toplam Giriş"].max() if df_ana["Toplam Giriş"].max() > 0 else 100),
            ),
            "Durum": st.column_config.TextColumn(
                "Durum",
                help="Kritik seviye kontrolü",
            )
        }
    )

# --- SON HAREKETLER (LOG KAYITLARI) ---
st.divider()
st.subheader("📜 Son Stok Hareketleri Geçmişi")

cursor.execute("""
SELECT h.tarih, h.urun_kodu, u.urun_adi, h.islem_turu, h.miktar, h.aciklama 
FROM stok_hareketleri h
JOIN urunler u ON h.urun_kodu = u.urun_kodu
ORDER BY h.id DESC LIMIT 10
""")
hareketler = cursor.fetchall()

if hareketler:
    df_hareket = pd.DataFrame(hareketler, columns=["Tarih", "Ürün Kodu", "Ürün Adı", "İşlem Türü", "Miktar", "Açıklama"])
    st.table(df_hareket)
else:
    st.caption("Henüz bir stok giriş veya çıkış hareketi gerçekleşmedi.")
