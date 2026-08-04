import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# ==============================================================================
# 🎛️ GENEL KONTROL PANELİ (HER ŞEYE BURADAN MÜDAHALE EDEBİLİRSİNİZ)
# ==============================================================================

# --- 🎨 RENK AYARLARI ---
PENCERE_ARKA_PLAN_RENK = "#314666"  # Ekranın genel arka plan rengi
KART_ARKA_PLAN_RENK     = "#315366"  # Form alanlarının ve kutuların içi
ANA_BAZ_RENK            = "#2c3e50"  # Üst başlık şeridi ve detay butonlarının rengi
GIRIS_BUTON_RENK        = "#27ae60"  # Stok Giriş buton rengi
CIKIS_BUTON_RENK        = "#e74c3c"  # Stok Çıkış buton rengi
SILME_BUTON_RENK        = "#c0392b"  # Ürün Silme butonu rengi
ANA_YAZI_RENK           = "#ffffff"  # Formların ve düz metinlerin ana yazı rengi

# --- 📝 METİN VE YAZI AYARLARI ---
PROGRAM_ANA_BASLIGI     = "📦 MAYRA PARK Gelişmiş Stok Takip Sistemi"
GIRIS_PANEL_UST_YAZI    = "🟩 STOK GİRİŞİ (ALIM PANELİ)"
CIKIS_PANEL_UST_YAZI   = "🟥 STOK ÇIKIŞI (TESLİMAT PANELİ)"
TABLO_UST_YAZI          = "📊 Güncel Stok Durum Raporu"
YONETIM_UST_YAZI        = "🔍 Gelişmiş Filtreleme ve Hareket Geçmişi Raporu"

# --- 🔘 BUTON ÜZERİNDEKİ YAZILAR ---
GIRIS_KAYDET_BUTON_METNI= "📥 STOK EKLE / SİSTEME GİRİŞ YAP"
CIKIS_KAYDET_BUTON_METNI= "📤 STOKTAN DÜŞ / TESLİMAT YAP"
URUN_SIL_BUTON_METNI    = "🗑️ BU ÜRÜNÜ SİSTEMDEN KALICI OLARAK SİL"

# --- 📐 BOYUT VE FONT AYARLARI ---
ANA_YAZI_FONTU          = "Arial"    # Kullanılacak yazı tipi ailesi
YAZI_BOYUTU_PIXER       = "15px"     # Form ve tablo içi yazıların boyutu

# ==============================================================================
# 💾 SQLITE VERİTABANI MOTORU
# ==============================================================================
DB_YOLU = "mayra_stok_sistemi_yeni.db"

def veritabani_kur():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urunler (
            stok_kodu TEXT PRIMARY KEY,
            aciklama TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS girisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stok_kodu TEXT,
            tarih TEXT,
            firma TEXT,
            adet INTEGER,
            FOREIGN KEY(stok_kodu) REFERENCES urunler(stok_kodu) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cikisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stok_kodu TEXT,
            tarih TEXT,
            kime TEXT,
            adet INTEGER,
            FOREIGN KEY(stok_kodu) REFERENCES urunler(stok_kodu) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

veritabani_kur()

# ==============================================================================
# 🎨 Gelişmiş Tasarım Motoru (CSS Kontrolü Aktif Edildi)
# ==============================================================================
st.set_page_config(page_title="Stok Takip Sistemi", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {PENCERE_ARKA_PLAN_RENK} !important; color: {ANA_YAZI_RENK} !important; font-family: '{ANA_YAZI_FONTU}' !important; font-size: {YAZI_BOYUTU_PIXER} !important; }}
    .stExpander {{ background-color: {KART_ARKA_PLAN_RENK} !important; border: 2px solid #e0e0e0; border-radius: 8px; }}
    div.stButton > button {{ width: 100%; font-weight: bold !important; color: white !important; border-radius: 6px !important; border: none !important; padding: 10px !important; }}
    
    /* Buton Key Renk Atamaları */
    button[key="btn_g_ekle"] {{ background-color: {GIRIS_BUTON_RENK} !important; }}
    button[key="btn_c_dus"] {{ background-color: {CIKIS_BUTON_RENK} !important; }}
    button[key="btn_silme_motoru"] {{ background-color: {SILME_BUTON_RENK} !important; }}
    
    /* Başlık ve Yazı Karakteri Eşitlemesi */
    h1, h2, h3, h4, h5, h6, p, label, .stSubheader {{ font-family: '{ANA_YAZI_FONTU}' !important; color: white !important; }}
    div[data-testid="stSidebar"] {{ background-color: {ANA_BAZ_RENK} !important; }}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🛡️ VERİ KORUMA PANELİ (SOL YAN MENÜ)
# ==============================================================================
with st.sidebar:
    st.markdown("## 🛡️ Mayra Park Veri Koruma")
    st.write("GitHub güncellemesi yapmadan önce yedek alın, güncelleme bitince yedeği yükleyin.")
    
    conn = sqlite3.connect(DB_YOLU)
    u_df = pd.read_sql_query("SELECT * FROM urunler", conn)
    g_df = pd.read_sql_query("SELECT * FROM girisler", conn)
    c_df = pd.read_sql_query("SELECT * FROM cikisler", conn)
    conn.close()
        
    output = io.BytesIO()
    u_df.to_excel(output, index=False)
    
    st.download_button(
        label="📥 Güncelleme Öncesi Verileri Yedekle",
        data=output.getvalue(),
        file_name=f"mayrapark_stok_yedek_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_yedek_indir"
    )

    st.markdown("---")
    
    yuklenen_dosya = st.file_uploader("📤 Güncelleme Sonrası Yedeği Yükle (.xlsx)", type=["xlsx"], key="yedek_sec")
    if yuklenen_dosya is not None:
        if st.button("⚙️ Eski Verileri Sisteme Geri Yükle", key="btn_yedek_yukle"):
            excel_u = pd.read_excel(yuklenen_dosya)
            conn = sqlite3.connect(DB_YOLU)
            excel_u.to_sql('urunler', conn, if_exists='replace', index=False)
            conn.commit()
            conn.close()
            st.success("🎉 Verileriniz başarıyla kurtarıldı!")
            st.rerun()

# Ana Başlık
st.title(PROGRAM_ANA_BASLIGI)

sol_panel, sag_panel = st.columns(2)

# ==============================================================================
# 🟩 SOL PANEL - GİRİŞ VE ÇIKIŞ İŞLEMLERİ
# ==============================================================================
with sol_panel:
    with st.expander(GIRIS_PANEL_UST_YAZI, expanded=True):
        g_kod = st.text_input("Stok Kodu (Giriş):", key="g1").strip().upper()
        g_aciklama = st.text_input("Stok Açıklaması / Ürün Adı:", key="g_acik").strip()
        g_tarih = st.text_input("Alınma Tarihi:", value=datetime.now().strftime("%d.%m.%Y"), key="g2")
        g_firma = st.text_input("Hangi Firmadan Alındı:", key="g3")
        g_adet = st.number_input("Alım Adeti:", min_value=1, step=1, key="g4")
        
        if st.button(GIRIS_KAYDET_BUTON_METNI, key="btn_g_ekle"):
            if g_kod and g_aciklama and g_firma:
                conn = sqlite3.connect(DB_YOLU)
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO urunler (stok_kodu, aciklama) VALUES (?, ?)", (g_kod, g_aciklama))
                cursor.execute("INSERT INTO girisler (stok_kodu, tarih, firma, adet) VALUES (?, ?, ?, ?)", (g_kod, g_tarih, g_firma, g_adet))
                conn.commit()
                conn.close()
                st.success(f"**{g_kod}** veritabanına işlendi.")
                st.rerun()
            else:
                st.error("Hata: Stok Kodu, Açıklama ve Firma alanları boş bırakılamaz.")

    with st.expander(CIKIS_PANEL_UST_YAZI, expanded=True):
        c_kod = st.text_input("Stok Kodu (Çıkış):", key="c1").strip().upper()
        c_tarih = st.text_input("Teslim Tarihi:", value=datetime.now().strftime("%d.%m.%Y"), key="c2")
        c_kime = st.text_input("Kime / Alıcı Kişi:", key="c3")
        c_adet = st.number_input("Teslim Edilecek Adet:", min_value=1, step=1, key="c4")
        
        if st.button(CIKIS_KAYDET_BUTON_METNI, key="btn_c_dus"):
            if c_kod and c_kime:
                conn = sqlite3.connect(DB_YOLU)
                cursor = conn.cursor()
                
                cursor.execute("SELECT SUM(adet) FROM girisler WHERE stok_kodu=?", (c_kod,))
                res_g = cursor.fetchone()
                toplam_giris = res_g if res_g and res_g is not None else 0
                
                cursor.execute("SELECT SUM(adet) FROM cikisler WHERE stok_kodu=?", (c_kod,))
                res_c = cursor.fetchone()
                toplam_cikis = res_c if res_c and res_c is not None else 0
                
                kalan = toplam_giris - toplam_cikis
                
                if toplam_giris == 0:
                    st.error("Hata: Bu stok kodu sistemde tanımlı değil.")
                elif c_adet > kalan:
                    st.error(f"Hata: Yetersiz stok! Mevcut kalan miktar: {kalan}")
                else:
                    cursor.execute("INSERT INTO cikisler (stok_kodu, tarih, kime, adet) VALUES (?, ?, ?, ?)", (c_kod, c_tarih, c_kime, c_adet))
                    conn.commit()
                    st.success(f"**{c_kod}** stok çıkış kaydı yapıldı.")
                    conn.close()
                    st.rerun()
                conn.close()
            else:
                st.error("Hata: Lütfen çıkış için gerekli tüm alanları doldurun.")

# ==============================================================================
# 📊 SAĞ PANEL - TÜM RAPORLAMA VE YÖNETİM MOTORU
# ==============================================================================
with sag_panel:
    st.subheader(YONETIM_UST_YAZI)
    
    arama_sorgusu = st.text_input("🔍 Bulmak istediğiniz Stok Kodunu veya Ürün Adını yazın:", "").strip().lower()
    
    conn = sqlite3.connect(DB_YOLU)
    urunler_df = pd.read_sql_query("SELECT * FROM urunler", conn)
    girisler_df = pd.read_sql_query("SELECT * FROM girisler", conn)
    cikisler_df = pd.read_sql_query("SELECT * FROM cikisler", conn)
    
    stok_durumu = []
    
    for idx, row in urunler_df.iterrows():
        skod = str(row['stok_kodu'])
        aciklama = str(row['aciklama'])
        
        g_toplam = girisler_df[girisler_df['stok_kodu'] == skod]['adet'].sum()
