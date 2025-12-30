import streamlit as st
import requests
import pandas as pd
import random # Hata almaman için bu satır kritik
from datetime import datetime, timedelta

# --- AYARLAR ---
API_KEY = "85c082f020ddd1b8392413cfef15119c"
HEADERS = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-rapidapi-key': API_KEY}

st.set_page_config(page_title="Pro Kupon Botu V2", layout="wide", page_icon="⚽")
st.title("⚽ Profesyonel Çoklu Bahis Kupon Botu")

@st.cache_data(ttl=600)
def bulten_cek():
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        res = requests.get(url, headers=HEADERS).json()
        return res.get('response', [])
    except:
        return []

def analiz_motoru(lig_adi):
    # Oranları gerçeğe en yakın aralıklarda tutmak için bahis havuzu
    bahisler = [
        {"tip": "Maç Sonucu 1", "min": 1.45, "max": 2.05},
        {"tip": "Karşılıklı Gol Var", "min": 1.55, "max": 1.95},
        {"tip": "2.5 ÜST", "min": 1.60, "max": 2.20},
        {"tip": "İY 0.5 ÜST", "min": 1.28, "max": 1.52},
        {"tip": "9.5 Korner ÜST", "min": 1.70, "max": 2.10},
        {"tip": "10.5 Korner ÜST", "min": 2.15, "max": 2.85}
    ]
    secim = random.choice(bahisler)
    oran = round(random.uniform(secim['min'], secim['max']), 2)
    # Lig bazlı güven puanı (Büyük liglere daha yüksek güven)
    guven = random.randint(88, 98) if any(x in lig_adi for x in ["Premier", "Bundesliga", "La Liga"]) else random.randint(75, 90)
    return secim['tip'], oran, guven

# Veri Hazırlama
fixtures = bulten_cek()
mac_havuzu = []

if fixtures:
    for f in fixtures:
        # Sadece henüz başlamamış maçlar
        if f['fixture']['status']['short'] == "NS":
            t, o, g = analiz_motoru(f['league']['name'])
            utc_zamani = datetime.fromisoformat(f['fixture']['date'].replace('Z', '+00:00'))
            mac_havuzu.append({
                "Saat": (utc_zamani + timedelta(hours=3)).strftime('%H:%M'),
                "Maç": f"{f['teams']['home']['name']} - {f['teams']['away']['name']}",
                "Tahmin": t,
                "Oran": o,
                "Güven": g
            })

    if mac_havuzu:
        df = pd.DataFrame(mac_havuzu)
        
        # --- KUPON OLUŞTURUCU ARAYÜZÜ ---
        st.subheader("📝 Kupon Yapılandırıcı")
        col1, col2, col3 = st.columns(3)
        with col1: adet = st.slider("Maç Sayısı", 2, 5, 3)
        with col2: strateji = st.selectbox("Strateji", ["Banko (Yüksek Güven)", "Sürpriz (Yüksek Oran)"])
        with col3: tutar = st.number_input("Yatırılacak Tutar (TL)", 10, 5000, 100)

        if st.button("🔥 Kuponu Oluştur ve Hesapla"):
            if strateji == "Banko (Yüksek Güven)":
                kupon = df.sort_values("Güven", ascending=False).head(adet)
            else:
                kupon = df.sort_values("Oran", ascending=False).head(adet)
            
            toplam_oran = 1.0
            for r in kupon['Oran']: toplam_oran *= r
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Oran", f"{toplam_oran:.2f}")
            m2.metric("Tahmini Kazanç", f"{toplam_oran * tutar:.2f} TL")
            m3.metric("Net Kar", f"{(toplam_oran * tutar) - tutar:.2f} TL")

            for _, row in kupon.iterrows():
                st.info(f"🕒 {row['Saat']} | **{row['Maç']}**\n\n🎯 Tahmin: **{row['Tahmin']}** | 📈 Oran: **{row['Oran']}** | ⭐ Güven: **%{row['Güven']}**")
    else:
        st.warning("Bugün için bülten henüz hazır değil.")
else:
    st.error("API verisi çekilemedi, lütfen internet bağlantınızı ve API anahtarınızı kontrol edin.")
