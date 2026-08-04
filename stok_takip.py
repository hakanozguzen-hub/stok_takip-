import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# ==============================================================================
# 🎛️ GENEL KONTROL PANELİ
# ==============================================================================
PROGRAM_ANA_BASLIGI     = "📦 MAYRA PARK Gelişmiş Stok Takip Sistemi"
GIRIS_PANEL_UST_YAZI    = "🟩 STOK GİRİŞİ (ALIM PANELİ)"
CIKIS_PANEL_UST_YAZI   = "🟥 STOK ÇIKIŞI (TESLİMAT PANELİ)"
TABLO_UST_YAZI          = "📊 Güncel Stok Durum Raporu"
YONETIM_UST_YAZI        = "🔍 Gelişmiş Filtreleme ve Hareket Geçmişi Raporu"

GIRIS_KAYDET_BUTON_METNI= "📥 STOK EKLE / SİSTEME GİRİŞ YAP"
CIKIS_KAYDET_BUTON_METNI= "📤 STOKTAN DÜŞ / TESLİMAT YAP"
URUN_SIL_BUTON_METNI    = "🗑️ BU ÜRÜNÜ SİSTEMDEN KALICI OLARAK SİL"

# ==============================================================================
# 💾 SQLITE VERİTABANI MOTORU
# ==============================================================================
DB_YOLU = "mayra_stok_veritabani_final_fixed.db"

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
# 🎨 TEMİZ STANDART TASARIM MOTORU
# ==============================================================================
st.set_page_config(page_title="Stok Takip Sistemi", layout="wide")

st.markdown("""
    <style>
    div.stButton > button { width: 100%; font-weight: bold; padding: 12px; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🛡️ VERİ KORUMA PANELİ (SOL YAN MENÜ)
# ==============================================================================
with st.sidebar:
    st.markdown("## 🛡️ Mayra Park Veri Koruma")
    st.write("GitHub güncellemesi yapmadan önce yedek alın, güncelleme bitince yedeği yükleyin.")
    
    conn = sqlite3.connect(DB_YOLU)
    u_df_b = pd.read_sql_query("SELECT * FROM urunler", conn)
    g_df_b = pd.read_sql_query("SELECT * FROM girisler", conn)
    c_df_b = pd.read_sql_query("SELECT * FROM cikisler", conn)
    conn.close()
        
    output_backup = io.BytesIO()
    with pd.ExcelWriter(output_backup, engine='xlsxwriter') as writer:
        u_df_b.to_excel(writer, sheet_name='Urunler', index=False)
        g_df_b.to_excel(writer, sheet_name='Girisler', index=False)
        c_df_b.to_excel(writer, sheet_name='Cikisler', index=False)
    
    st.download_button(
        label="📥 Güncelleme Öncesi Verileri Yedekle",
        data=output_backup.getvalue(),
        file_name=f"mayrapark_stok_yedek_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_yedek_indir"
    )

    st.markdown("---")
    
    yuklenen_dosya = st.file_uploader("📤 Güncelleme Sonrası Yedeği Yükle (.xlsx)", type=["xlsx"], key="yedek_sec")
    if yuklenen_dosya is not None:
        if st.button("⚙️ Eski Verileri Sisteme Geri Yükle", key="btn_yedek_yukle"):
            try:
                excel_u = pd.read_excel(yuklenen_dosya, sheet_name='Urunler')
                excel_g = pd.read_excel(yuklenen_dosya, sheet_name='Girisler')
                excel_c = pd.read_excel(yuklenen_dosya, sheet_name='Cikisler')
                
                conn = sqlite3.connect(DB_YOLU)
                excel_u.to_sql('urunler', conn, if_exists='replace', index=False)
                excel_g.to_sql('girisler', conn, if_exists='replace', index=False)
                excel_c.to_sql('cikisler', conn, if_exists='replace', index=False)
                conn.commit()
                conn.close()
                st.success("🎉 Verileriniz başarıyla kurtarıldı!")
                st.rerun()
            except Exception as hata:
                st.error(f"Yükleme başarısız oldu: {hata}")

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
    
    df_ozet = pd.DataFrame(stok_durumu)
    st.dataframe(df_ozet, use_container_width=True)
    
    if len(stok_durumu) > 0:
        output_rapor = io.BytesIO()
        with pd.ExcelWriter(output_rapor, engine='xlsxwriter') as writer:
            df_ozet.to_excel(writer, sheet_name='Stok_Durumu', index=False)
        st.download_button(
