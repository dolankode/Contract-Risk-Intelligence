import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="LexiGuard AI Dashboard", layout="wide")

st.title("🛡️ LexiGuard AI: Contract Risk Intelligence")
st.markdown("Unggah dokumen hukum (PDF) untuk analisis risiko instan berbasis AI.")

# Sidebar untuk Konfigurasi
st.sidebar.header("Settings")
api_key = st.sidebar.text_input("Enter X-API-KEY", type="password")
# URL diubah ke server PythonAnywhere
api_url = "http://ulosowo.pythonanywhere.com/analyze-contract"

# --- Konfigurasi Telegram Bot ---
TELEGRAM_BOT_TOKEN = "8661426539:AAF2hGPxTWEuBgFKiKp1BnUgCgkaceOH3fQ"
CHAT_ID = "743378684"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass
# -------------------------------

uploaded_file = st.file_uploader("Pilih file PDF kontrak/UU", type="pdf")

# Fungsi untuk mewarnai baris berdasarkan risiko
def color_risk(val):
    if 'Extremely High' in str(val) or 'Very High' in str(val):
        color = '#8b0000' # Dark Red
    elif 'High' in str(val):
        color = 'red'
    elif 'Medium' in str(val):
        color = 'orange'
    else:
        color = 'green'
    return f'background-color: {color}; color: white; font-weight: bold'

if st.button("Mulai Analisis"):
    if not api_key or not uploaded_file:
        st.error("Mohon masukkan API Key dan upload file!")
    else:
        with st.spinner("AI sedang membedah dokumen... Mohon tunggu."):
            # Kirim file ke FastAPI
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            headers = {"X-API-KEY": api_key}
            
            try:
                response = requests.post(api_url, headers=headers, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    # Pastikan mengambil data sesuai struktur JSON dari FastAPI
                    analysis = result.get("analysis", {}).get("risks", [])
                    
                    if not analysis:
                        st.warning("Analisis selesai, namun tidak ditemukan risiko spesifik.")
                    else:
                        st.success(f"Analisis Selesai: {result['filename']}")
                        
                        # 1. Tampilkan Ringkasan dalam Tabel
                        df = pd.DataFrame(analysis)
                        
                        st.subheader("📋 Daftar Temuan Risiko")
                        # Menggunakan .map() untuk Pandas versi terbaru
                        styled_df = df.style.map(color_risk, subset=['risk_level'])
                        st.dataframe(styled_df, use_container_width=True)
                        
                        # 2. Detail View dengan Expander
                        st.subheader("🔍 Detail & Saran Perbaikan")
                        for item in analysis:
                            # Memberikan label warna pada judul expander agar lebih jelas
                            risk_label = item.get('risk_level', 'Unknown')
                            with st.expander(f"[{risk_label}] - {item.get('clause', 'N/A')[:60]}..."):
                                st.write(f"**Pasal/Klausul:** {item.get('clause')}")
                                st.write(f"**Masalah:** {item.get('issue')}")
                                st.info(f"**Saran:** {item.get('suggestion')}")
                                
                elif response.status_code == 403:
                    st.error("Gagal: API Key salah atau tidak memiliki akses.")
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
                    send_telegram_alert(f"🚨 *Peringatan Backend LexiGuard AI*\n\nBackend memberikan respons error.\nStatus Code: {response.status_code}\nDetail: {response.text}")
                    
            except Exception as e:
                st.error(f"Gagal terhubung ke server: {e}")
                send_telegram_alert(f"🚨 *Peringatan Backend LexiGuard AI*\n\nStatus: Tidak dapat terhubung ke server.\nDetail Error: {e}")

st.divider()
st.caption("© 2026 LexiGuard AI Microservice SaaS - Powered by Gemini 1.5 Flash")
