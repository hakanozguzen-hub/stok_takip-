import streamlit as st
import pandas as pd
import io
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
# 💾 DOSYASIZ BULUT BELLEK MOTORU (ÇÖKMEYİ ENGELLER)
# ==============================================================================
if "stok_deposu" not in st.session_state:
    st.session_state.stok_deposu = {}

st.set_page_config(page_title="Stok Takip Sistemi", layout="wide")

# CSS Tasarım Zorlaması
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
                if g_kod not in st.session_state.stok_deposu:
                    st.session_state.stok_deposu[g_kod] = {"aciklama": g_aciklama, "girisler": [], "cikisler": []}
                else:
                    st.session_state.stok_deposu[g_kod]["aciklama"] = g_aciklama
                
                st.session_state.stok_deposu[g_kod]["girisler"].append({
                    "Tarih": g_tarih, "Firma": g_firma, "Adet": int(g_adet)
                })
                st.success(f"**{g_kod}** başarıyla kaydedildi.")
                st.rerun()
            else:
                st.error("Lütfen Stok Kodu, Açıklama ve Firma alanlarını doldurun.")

    with st.expander(CIKIS_PANEL_UST_YAZI, expanded=True):
        c_kod = st.text_input("Stok Kodu (Çıkış):", key="c1").strip().upper()
        c_tarih = st.text_input("Teslim Tarihi:", value=datetime.now().strftime("%d.%m.%Y"), key="c2")
        c_kime = st.text_input("Kime / Alıcı Kişi:", key="c3")
        c_adet = st.number_input("Teslim Edilecek Adet:", min_value=1, step=1, key="c4")
        
        if st.button(CIKIS_KAYDET_BUTON_METNI, key="btn_c_dus"):
            if c_kod and c_kime:
                if c_kod in st.session_state.stok_deposu:
                    top_g = sum(item["Adet"] for item in st.session_state.stok_deposu[c_kod]["girisler"])
                    top_c = sum(item["Adet"] for item in st.session_state.stok_deposu[c_kod]["cikisler"])
                    kalan = top_g - top_c
                    
                    if c_adet > kalan:
                        st.error(f"Yetersiz stok! Mevcut kalan miktar: {kalan}")
                    else:
                        st.session_state.stok_deposu[c_kod]["cikisler"].append({
                            "Tarih": c_tarih, "Kime": c_kime, "Adet": int(c_adet)
                        })
                        st.success(f"**{c_kod}** stok çıkışı yapıldı.")
                        st.rerun()
                else:
                    st.error("Bu stok kodu sistemde tanımlı değil.")
            else:
                st.error("Lütfen çıkış için gerekli tüm alanları doldurun.")

# ==============================================================================
# 📊 SAĞ PANEL - AKILLI RAPORLAMA VE ÇIKTI ALMA (EXCEL)
# ==============================================================================
with sag_panel:
    st.subheader(YONETIM_UST_YAZI)
    arama_sorgusu = st.text_input("🔍 Bulmak istediğiniz Stok Kodunu veya Stok İsmini yazın:", "").strip().lower()
    
    # Tüm verileri listelemek için DataFrame listeleri hazırlama
    liste_g, liste_c, liste_ozet = [], [], []
    
    for kod, veri in st.session_state.stok_deposu.items():
        tanim = veri["aciklama"]
        t_g = sum(i["Adet"] for item in veri["girisler"] for i in [item])
        t_c = sum(i["Adet"] for item in veri["cikisler"] for i in [item])
        liste_ozet.append({"Stok Kodu": kod, "Stok Açıklaması / Ürün Adı": tanim, "Toplam Giriş": t_g, "Toplam Çıkış": t_c, "Kalan Güncel Stok": t_g - t_c})
        
        for g in veri["girisler"]:
            liste_g.append({"Stok Kodu": kod, "Stok Açıklaması / Ürün Adı": tanim, "İşlem Tarihi": g["Tarih"], "Kimden Alındı / Firma": g["Firma"], "Miktar (Giriş)": g["Adet"]})
        for c in veri["cikisler"]:
            liste_c.append({"Stok Kodu": kod, "Stok Açıklaması / Ürün Adı": tanim, "İşlem Tarihi": c["Tarih"], "Kime Teslim Edildi / Alıcı": c["Kime"], "Miktar (Çıkış)": c["Adet"]})

    df_g_all = pd.DataFrame(liste_g)
    df_c_all = pd.DataFrame(liste_c)
    df_stoklar = pd.DataFrame(liste_ozet)

    # Arama Filtreleme Yapay Zekası
    if arama_sorgusu:
        df_g_filtre = df_g_all[df_g_all['Stok Kodu'].str.lower().str.contains(arama_sorgusu) | df_g_all['Stok Açıklaması / Ürün Adı'].str.lower().str.contains(arama_sorgusu)] if not df_g_all.empty else df_g_all
        df_c_filtre = df_c_all[df_c_all['Stok Kodu'].str.lower().str.contains(arama_sorgusu) | df_c_all['Stok Açıklaması / Ürün Adı'].str.lower().str.contains(arama_sorgusu)] if not df_c_all.empty else df_c_all
    else:
        df_g_filtre = df_g_all
        df_c_filtre = df_c_all

    # Excel Rapor Çıktı Butonu
    if arama_sorgusu and (not df_g_filtre.empty or not df_c_filtre.empty):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            if not df_g_filtre.empty: df_g_filtre.to_excel(writer, sheet_name='Giriş Hareketleri', index=False)
            if not df_c_filtre.empty: df_c_filtre.to_excel(writer, sheet_name='Çıkış Hareketleri', index=False)
        st.download_button(label="📥 Seçili Raporu Excel Formatında Çıktı Al / İndir", data=buffer.getvalue(), file_name=f"Stok_Raporu_{arama_sorgusu}.xlsx", mime="application/vnd.ms-excel")

    r_sol, r_sag = st.columns(2)
    with r_sol:
        st.markdown("### 📥 Filtrelenmiş Giriş Listesi")
        if not df_g_filtre.empty: st.dataframe(df_g_filtre, width="stretch", hide_index=True)
        else: st.caption("Kayıt yok.")
    with r_sag:
        st.markdown("### 📤 Filtrelenmiş Çıkış Listesi")
        if not df_c_filtre.empty: st.dataframe(df_c_filtre, width="stretch", hide_index=True)
        else: st.caption("Kayıt yok.")

    # --- GENEL DURUM ÖZET TABLOSU ---
    st.write("---")
    st.subheader(TABLO_UST_YAZI)
    
    if not df_stoklar.empty:
        st.dataframe(df_stoklar, width="stretch", hide_index=True)
        buf_all = io.BytesIO()
        with pd.ExcelWriter(buf_all, engine='xlsxwriter') as writer: df_stoklar.to_excel(writer, sheet_name='Genel Özet', index=False)
        st.download_button(label="📊 Tüm Stok Listesini Excel Olarak İndir", data=buf_all.getvalue(), file_name="Tum_Stok_Listesi.xlsx", mime="application/vnd.ms-excel")
    else:
        st.info("Sistemde kayıtlı aktif stok bulunmuyor.")

