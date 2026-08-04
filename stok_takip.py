import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==============================================================================
# 🎛️ GENEL KONTROL PANELİ (HER ŞEYE BURADAN MÜDAHALE EDEBİLİRSİNİZ)
# ==============================================================================

# --- 🎨 RENK AYARLARI ---
PENCERE_ARKA_PLAN_RENK = "#f4f6f9"  # Ekranın genel arka plan rengi
KART_ARKA_PLAN_RENK     = "#ffffff"  # Form alanlarının ve kutuların içi
ANA_BAZ_RENK            = "#2c3e50"  # Üst başlık şeridi ve detay butonlarının rengi
GIRIS_BUTON_RENK        = "#27ae60"  # Stok Giriş buton rengi
CIKIS_BUTON_RENK        = "#e74c3c"  # Stok Çıkış buton rengi
SILME_BUTON_RENK        = "#c0392b"  # Ürün Silme butonu rengi
ANA_YAZI_RENK           = "#333333"  # Formların ve düz metinlerin ana yazı rengi

# --- 📝 METİN VE YAZI AYARLARI ---
PROGRAM_ANA_BASLIGI     = "📦 MAYRA PARK Stok Takip Sistemi"
GIRIS_PANEL_UST_YAZI    = "🟩 STOK GİRİŞİ (ALIM PANELİ)"
CIKIS_PANEL_UST_YAZI   = "🟥 STOK ÇIKIŞI (TESLİMAT PANELİ)"
TABLO_UST_YAZI          = "📊 Güncel Stok Durum Raporu"
YONETIM_UST_YAZI        = "🔍 Ürün Yönetimi ve Detaylı Hareket Geçmişi"

# --- 🔘 BUTON ÜZERİNDEKİ YAZILAR ---
GIRIS_KAYDET_BUTON_METNI= "📥 STOK EKLE / SİSTEME GİRİŞ YAP"
CIKIS_KAYDET_BUTON_METNI= "📤 STOKTAN DÜŞ / TESLİMAT YAP"
URUN_SIL_BUTON_METNI    = "🗑️ BU ÜRÜNÜ VE TÜM GEÇMİŞİNİ SİSTEMDEN KALICI OLARAK SİL"

# --- 📐 BOYUT VE FONT AYARLARI ---
ANA_YAZI_FONTU          = "Arial"    # Kullanılacak yazı tipi ailesi
YAZI_BOYUTU_PIXER       = "15px"     # Form ve tablo içi yazıların boyutu

# ==============================================================================
# 💾 SQLITE VERİTABANI MOTORU VE BAĞLANTILARI
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
    st-key-btn_g_ekle button {{ background-color: {GIRIS_BUTON_RENK} !important; }}
    st-key-btn_c_dus button {{ background-color: {CIKIS_BUTON_RENK} !important; }}
    st-key-btn_silme_motoru button {{ background-color: {SILME_BUTON_RENK} !important; }}
    .stTextInput input, .stNumberInput input {{ color: {ANA_YAZI_RENK} !important; }}
    </style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="ozel-ust-baslik"><h1>{PROGRAM_ANA_BASLIGI}</h1></div>', unsafe_allow_html=True)

sol_panel, sag_panel = st.columns(2)

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
                st.success(f"**{g_kod}** kodlu stok ve alım kaydı başarıyla veritabanına işlendi.")
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
                toplam_giris = cursor.fetchone()[0] or 0
                cursor.execute("SELECT SUM(adet) FROM cikisler WHERE stok_kodu=?", (c_kod,))
                toplam_cikis = cursor.fetchone()[0] or 0
                kalan = toplam_giris - toplam_cikis
                
                if toplam_giris == 0:
                    st.error("Hata: Bu stok kodu sistemde tanımlı değil veya hiç alım yapılmamış.")
                elif c_adet > kalan:
                    st.error(f"Hata: Yetersiz stok! Depodaki mevcut miktar: {kalan}")
                else:
                    cursor.execute("INSERT INTO cikisler (stok_kodu, tarih, kime, adet) VALUES (?, ?, ?, ?)", (c_kod, c_tarih, c_kime, c_adet))
                    conn.commit()
                    st.success(f"**{c_kod}** stok çıkış kaydı başarıyla veritabanına işlendi.")
                    conn.close()
                    st.rerun()
                conn.close()
            else:
                st.error("Hata: Lütfen çıkış için gerekli tüm alanları doldurun.")

with sag_panel:
    st.subheader(TABLO_UST_YAZI)
    
    conn = sqlite3.connect(DB_YOLU)
    query = """
        SELECT 
            u.stok_kodu AS 'Stok Kodu',
            u.aciklama AS 'Stok Açıklaması',
            IFNULL(g.toplam_g, 0) AS 'Toplam Giriş',
            IFNULL(c.toplam_c, 0) AS 'Toplam Çıkış',
            (IFNULL(g.toplam_g, 0) - IFNULL(c.toplam_c, 0)) AS 'Kalan Güncel Stok'
        FROM urunler u
        LEFT JOIN (SELECT stok_kodu, SUM(adet) AS toplam_g FROM girisler GROUP BY stok_kodu) g ON u.stok_kodu = g.stok_kodu
        LEFT JOIN (SELECT stok_kodu, SUM(adet) AS toplam_c FROM cikisler GROUP BY stok_kodu) c ON u.stok_kodu = c.stok_kodu
    """
    df_stoklar = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df_stoklar.empty:
        # Kod buradaki yeni sürüm standardına (width='stretch') göre güncellendi
        st.dataframe(df_stoklar, width="stretch", hide_index=True)
    else:
        st.info("Veritabanında kayıtlı aktif stok datası bulunmuyor.")
    
    st.write("---")
    st.subheader(YONETIM_UST_YAZI)
    
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("SELECT stok_kodu FROM urunler")
    urun_listesi = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if urun_listesi:
        secilen_kod = st.selectbox("İncelemek veya silmek istediğiniz Stok Kodunu seçin:", urun_listesi)
        
        if secilen_kod:
            conn = sqlite3.connect(DB_YOLU)
            cursor = conn.cursor()
            cursor.execute("SELECT aciklama FROM urunler WHERE stok_kodu=?", (secilen_kod,))
            mevcut_tanim = cursor.fetchone()[0]
            st.info(f"📋 **Ürün Kimliği:** {mevcut_tanim}")
            
            if st.button(URUN_SIL_BUTON_METNI, key="btn_silme_motoru"):
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("DELETE FROM urunler WHERE stok_kodu=?", (secilen_kod,))
                cursor.execute("DELETE FROM girisler WHERE stok_kodu=?", (secilen_kod,))
                cursor.execute("DELETE FROM cikisler WHERE stok_kodu=?", (secilen_kod,))
                conn.commit()
                conn.close()
                st.success(f"{secilen_kod} kodlu ürün veritabanından kalıcı olarak silindi.")
                st.rerun()
                
            df_g_gecmis = pd.read_sql_query("SELECT tarih AS 'Alınma Tarihi', firma AS 'Firma Adı', adet AS 'Adet' FROM girisler WHERE stok_kodu=?", conn, params=(secilen_kod,))
