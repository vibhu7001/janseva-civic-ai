import os
import json
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

st.set_page_config(page_title="JanSeva AI | Citizen Grievance Portal", page_icon="🏛️", layout="wide")

st.markdown("# 🏛️ JanSeva AI — Public Grievance Redressal")
st.markdown("Multilingual civic grievance routing, severity triage, and official petition drafting.")

# Sidebar Settings
st.sidebar.markdown("### ⚙️ Settings")

env_key = os.getenv("GEMINI_API_KEY")
if env_key:
    api_key = env_key
    st.sidebar.success("✅ API Key loaded from .env")
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

target_language = st.sidebar.selectbox("Draft Petition Language", ["Hindi", "English"], index=0)
st.sidebar.markdown("---")
st.sidebar.caption("Built for **Digital Public Infrastructure (DPI)**")

# Main Interface
st.markdown("### 📝 Citizen Complaint / Problem")
complaint_text = st.text_area(
    "Describe the issue in Hindi, Hinglish, or English:",
    placeholder="Jaise: Hamare ward me pichle 10 din se paani ki main pipeline phuti hui hai...",
    height=120
)

col1, col2 = st.columns(2)
with col1:
    citizen_name = st.text_input("Citizen Name", value="Concerned Citizen")
with col2:
    locality = st.text_input("Locality / Ward / City", placeholder="e.g., Ward 14, Saharanpur")

if st.button("🚀 Analyze & Generate Official Petition", type="primary"):
    if not api_key:
        st.error("Please provide a Gemini API Key in .env or the sidebar.")
    elif not complaint_text.strip():
        st.warning("Please describe your issue first.")
    else:
        with st.spinner("Processing grievance and drafting petition..."):
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            You are JanSeva AI, an expert civic triage and legal petition assistant for Indian governance.
            Citizen Name: {citizen_name}
            Location: {locality}
            Citizen Grievance: "{complaint_text}"

            Tasks:
            1. Identify the exact Competent Authority / Department in Uttar Pradesh/India (e.g., Nagar Nigam, Jal Nigam, PVVNL, PWD, Police).
            2. Determine Triage Priority: (High / Medium / Low) with brief reason.
            3. Classify Grievance Category (e.g., Water Supply, Sanitation, Roads, Electricity, Public Safety).
            4. Create a 2-sentence crisp English summary for administrative dashboard.
            5. Draft a formal representation / complaint letter addressed to the competent officer in {target_language}.
            
            Return the response strictly in valid JSON format with keys:
            "competent_dept", "triage_priority", "category", "actionable_summary", "petition_letter"
            """

            # 503 Server Spike Auto-Retry Handler
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                    break
                except Exception as err:
                    if "503" in str(err) and attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                        continue
                    else:
                        st.error(f"Error: {err}")
                        break

            if response and response.text:
                try:
                    result = json.loads(response.text)
                    st.success("✅ Complaint Successfully Processed!")

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Competent Dept", result.get("competent_dept", "N/A"))
                    m2.metric("Triage Priority", result.get("triage_priority", "N/A"))
                    m3.metric("Category", result.get("category", "N/A"))

                    st.markdown("---")
                    st.markdown("#### 📋 Actionable Summary")
                    st.info(result.get("actionable_summary", ""))

                    st.markdown("#### 🏛️ Official Representation Letter")
                    st.text_area("Ready-to-Submit Letter", value=result.get("petition_letter", ""), height=260)

                    st.download_button(
                        label="📥 Download Petition as Text File",
                        data=result.get("petition_letter", ""),
                        file_name="JanSeva_Petition.txt",
                        mime="text/plain"
                    )
                except Exception as parse_err:
                    st.error(f"JSON Parsing Error: {parse_err}")