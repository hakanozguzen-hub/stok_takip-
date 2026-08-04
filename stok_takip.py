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
ANA_YAZI_RENK           = "#333333"  # Formların ve düz metinlerin ana yazı rengi

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
DB_YOLU = "stok_takip.db"

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
# ARKA PLAN TASARIM MOTORU (CSS)
# ==============================================================================
st.set_page_config(page_title="Stok Takip Sistemi", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: {PENCERE_ARKA_PLAN_RENK} !important; color: {ANA_YAZI_RENK} !important; font-family: '{ANA_YAZI_FONTU}' !important; font-size: {YAZI_BOYUTU_PIXER} !important; }}
    .ozel-ust-baslik {{ background-color: {ANA_BAZ_RENK}; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 25px; border-bottom: 4px solid #1a252f; }}
    .ozel-ust-baslik h1 {{ color: white !important; font-family: '{ANA_YAZI_FONTU}' !important; font-weight: bold; margin: 0; }}
    .stExpander {{ background-color: {KART_ARKA_PLAN_RENK} !important; border: 2px solid #e0e0e0; border-radius: 8px; }}
    div.stButton > button {{ width: 100%; font-weight: bold !important; color: white !important; border-radius: 6px !important; border: none !important; padding: 10px !important; }}
    .stTextInput input, .stNumberInput input {{ color: {ANA_YAZI_RENK} !important; }}
    </style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="ozel-ust-baslik"><h1>{PROGRAM_ANA_BASLIGI}</h1></div>', unsafe_allow_html=True)

# ==============================================================================
# 🟩 STOK GİRİŞ VE ÇIKIŞ İŞLEMLERİ (ALT ALTA GÜVENLİ YERLEŞİM)
# ==============================================================================
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
            res_g = cursor.fetchone()[0]
            toplam_giris = res_g if res_g is not None else 0
            
            cursor.execute("SELECT SUM(adet) FROM cikisler WHERE stok_kodu=?", (c_kod,))
            res_c = cursor.fetchone()[0]
            toplam_cikis = res_c if res_c is not None else 0
            
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
# 📊 GELİŞMİŞ FİLTRELEME, HAREKET GEÇMİŞİ VE SİLME MOTORU
# ==============================================================================
st.markdown("---")
st.subheader(YONETIM_UST_YAZI)

arama_sorgusu = st.text_input("🔍 Bulmak istediğiniz Stok Kodunu veya Stok İsmini (Açıklamasını) yazın:", "").strip().lower()

conn = sqlite3.connect(DB_YOLU)
urunler_df = pd.read_sql_query("SELECT * FROM urunler", conn)
girisler_df = pd.read_sql_query("SELECT * FROM girisler", conn)
cikisler_df = pd.read_sql_query("SELECT * FROM cikisler", conn)

stok_durumu = []

for idx, row in urunler_df.iterrows():
    skod = str(row['stok_kodu'])
    aciklama = str(row['aciklama'])
    
    g_toplam = girisler_df[girisler_df['stok_kodu'] == skod]['adet'].sum()
    c_toplam = cikisler_df[cikisler_df['stok_kodu'] == skod]['adet'].sum()
    
    g_toplam = int(g_toplam) if pd.notna(g_toplam) else 0
    c_toplam = int(c_toplam) if pd.notna(c_toplam) else 0
    kalan_stok = g_toplam - c_toplam
    
    if arama_sorgusu in skod.lower() or arama_sorgusu in aciklama.lower():
        stok_durumu.append({
            "Stok Kodu": skod,
            "Açıklama": aciklama,
            "Toplam Giriş": g_toplam,
            "Toplam Çıkış": c_toplam,
            "Mevcut Stok": kalan_stok
        })

st.markdown(f"### {TABLO_UST_YAZI}")

if len(stok_durumu) > 0:
    df_ozet = pd.DataFrame(stok_durumu)
    st.dataframe(df_ozet, use_container_width=True)
    
    # Excel Çıktı Motoru
    output_rapor = io.BytesIO()
    with pd.ExcelWriter(output_rapor, engine='xlsxwriter') as writer:
        df_ozet.to_excel(writer, sheet_name='Stok_Durumu', index=False)
    st.download_button(
        label="📊 Güncel Stok Raporunu Excel Olarak İndir",
        data=output_rapor.getvalue(),
        file_name="MayraPark_Stok_Raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_excel_rapor"
    )
else:
    st.warning("Veritabanı şu an boş veya arama kriterine uygun ürün yok.")

st.markdown("---")

sekme1, sekme2 = st.tabs(["📋 Tüm Giriş Hareketleri", "📋 Tüm Çıkış Hareketleri"])
with sekme1:
    if not girisler_df.empty:
        g_filtreli = girisler_df[girisler_df['stok_kodu'].str.lower().str.contains(arama_sorgusu, na=False) | (arama_sorgusu == "")]
        st.dataframe(g_filtreli[['stok_kodu', 'tarih', 'firma', 'adet']], use_container_width=True)
    else:
        st.caption("Kayıtlı giriş hareketi yok.")
        
with sekme2:
    if not cikisler_df.empty:
        c_filtreli = cikisler_df[cikisler_df['stok_kodu'].str.lower().str.contains(arama_sorgusu, na=False) | (arama_sorgusu == "")]
        st.dataframe(c_filtreli[['stok_kodu', 'tarih', 'kime', 'adet']], use_container_width=True)
    else:
