import pandas as pd
import io

# Excel dosyasını sıfırdan ve hatasız oluşturma motoru
output_excel = io.BytesIO()

with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
    # 1. SEKME: CANLI DURUM RAPORU
    df_ozet = pd.DataFrame({
        "Stok Kodu": ["STK-001", "STK-002", "STK-003"],
        "Ürün Açıklaması / Adı": ["Örnek Ürün A", "Örnek Ürün B", "Örnek Ürün C"],
        "Toplam Giriş":,
        "Toplam Çıkış":,
        "Mevcut Kalan Stok":,
        "Stok Durum Alarmı": ["✅ Stok Yeterli", "✅ Stok Yeterli", "🚨 STOK TÜKENDİ!"]
    })
    df_ozet.to_excel(writer, sheet_name='📊 Canlı Stok Raporu', index=False)
    
    # 2. SEKME: STOK GİRİŞ HAREKETLERİ
    df_giris = pd.DataFrame({
        "İşlem ID":,
        "Stok Kodu": ["STK-001", "STK-002", "STK-003"],
        "Alım Tarihi": ["04.08.2026", "04.08.2026", "04.08.2026"],
        "Alınan Firma": ["Mayra Toptan Ticaret", "Park Lojistik A.Ş.", "Özdemir Sanayi"],
        "Alım Adeti": [100, 250, 50]
    })
    df_giris.to_excel(writer, sheet_name='🟩 Stok Girişleri', index=False)
    
    # 3. SEKME: STOK ÇIŞ HAREKETLERİ
    df_cikis = pd.DataFrame({
        "İşlem ID":,
        "Stok Kodu": ["STK-001", "STK-002", "STK-003"],
        "Teslim Tarihi": ["04.08.2026", "04.08.2026", "04.08.2026"],
        "Teslim Edilen Kişi / Alıcı": ["Ahmet Yılmaz", "Mehmet Kaya", "Kaan Demir"],
        "Teslim Edilen Adet": [40, 120, 50]
    })
    df_cikis.to_excel(writer, sheet_name='🟥 Stok Çıkışları', index=False)
    
    # Görsel düzenleme ve otomatik sütun genişletme motoru
    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.set_column('A:F', 25)

st.sidebar.success("🎉 Excel Tabanlı Stok Sistemi Başarıyla Hazırlandı!")
st.sidebar.download_button(
    label="📥 Mayra Park Kesin Excel Stok Takip Sistemini İndir",
    data=output_excel.getvalue(),
    file_name="Mayra_Park_Kesin_Stok_Takip.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="btn_excel_kesin_cozum"
)
