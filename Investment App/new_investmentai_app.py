# Streamlit Professional Investment Research Tool (Enhanced + Refined)

import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import os
import re
from fpdf import FPDF

def generate_pdf(text, filename="AI_Investment_Report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(0, 10, "AI Investment Research Report", ln=True, align="C")
    pdf.set_font("Arial", size=11)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    output_path = f"/tmp/{filename}"
    pdf.output(output_path)
    return output_path

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def analyze_text(text, pe_ratio=None, ebitda_mult=None, advanced=False, manual_price=None, target_price=None):
    analysis_depth = "Deeply analyze and deconstruct" if advanced else "Analyze"

    user_prompt = f"""
You are a professional equity research analyst writing for institutional investors.

{analysis_depth} the following company document in detail and provide a comprehensive investment report structured as follows:

Executive Summary:
- Present a concise investment thesis highlighting structural advantages, capital discipline, and global reach.
- Use provided valuation inputs:
  - P/E: {pe_ratio}
  - EBITDA multiple: {ebitda_mult}
  - EPS: {eps if eps else "Not Provided"}
  - Calculate and include a directional target price (e.g., "appears undervalued") using EPS × P/E when applicable.
- Avoid stating actual stock price. Emphasize valuation asymmetry or mispricing.

Company Overview:
- Describe business model across insurance segments.
- Highlight underwriting discipline, global diversification, and capital strength.
- Define competitive advantages: product breadth, credit ratings, market share, and service capabilities.

Recent News & Developments:
- Outline strategic moves (e.g., M&A, regulatory changes).
- Include quantitative impact (e.g., premium contribution).
- Align news to long-term growth initiatives.

Financial Highlights:
- Present revenue, EPS, EBITDA, combined ratio, net investment income.
- Emphasize earnings durability, volatility management, and underwriting strength.
- Conclude section by linking financial performance to broader thesis of resilience.

Management Tone & Guidance:
- Use quotes or paraphrase tone.
- Highlight commitment to EPS growth, capital deployment, and strategic execution.

Risk Factors:
- Identify 5+ risks, framed in polished and professional terms.
- Include catastrophe loss volatility, FX risk, regulatory exposure, and competitive pressure in P&C lines.

Valuation Discussion:
- Discuss P/E and EV/EBITDA in relative and historical context.
- Avoid quoting the current stock price.
- Frame valuation using institutional terms like "modestly discounted," "fairly valued," or "market underappreciation."

Final Investment Recommendation:
- Short-term (≤ 1 year): Emphasize catalysts (M&A execution, underwriting strength).
- Medium-term (1–5 years): Highlight operational trajectory and strategic drivers.
- Long-term (5+ years): Assess compounding ability, capital management, and risk-adjusted returns.
- End with a high-conviction conclusion that underscores valuation asymmetry and strategic clarity.

Avoid markdown formatting. Use professional, concise, and assertive language.

Document for analysis:
{text[:16000]}
"""
# Document for analysis:
# {text[:16000]}
def analyze_text(user_prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=3000,
        temperature=0.3
    )

    return response.choices[0].message.content


st.set_page_config(page_title="AI Investment Research", layout="wide")

st.title("💼 AI-Powered Investment Research Report")
st.write("Generate a professional-grade investment research report based on financial documents and valuation inputs.")

st.markdown("""
> **Disclaimer**  
> This tool is provided for **informational and educational purposes only**. It does **not constitute financial advice, investment recommendations, or legal counsel**.  
> You should not rely solely on this tool to make investment decisions. Please consult a licensed financial advisor or conduct your own due diligence.
""")

# User acknowledgment checkbox (required to proceed)
agree = st.checkbox("I understand and accept the disclaimer above.")
if not agree:
    st.warning("Please accept the disclaimer to use this tool.")
    st.stop()

st.subheader("📁 Upload Financial Documents")
uploaded_file_1 = st.file_uploader("Primary PDF (e.g., 10-K, earnings call)", type="pdf")
uploaded_file_2 = st.file_uploader("Secondary PDF (optional)", type="pdf")
uploaded_file_3 = st.file_uploader("Tertiary PDF (optional)", type="pdf")

st.subheader("🌐 Market Information (Optional)")
yahoo_url = st.text_input("Yahoo Finance URL")

st.subheader("📊 Valuation Inputs")
pe = st.text_input("P/E Ratio")
ebitda = st.text_input("EBITDA Multiple")
eps = st.text_input("EPS Estimate (Optional, e.g., 7.85)")

manual_price = st.text_input("Current Stock Price (e.g., 185.23)")

target_price = None
if eps and pe:
    try:
        target_price = round(float(pe) * float(eps), 2)
    except ValueError:
        target_price = None

advanced_mode = st.checkbox("Enable Advanced Analyst Mode", value=True)

def clean_gpt_output(gpt_output, manual_price):
    if manual_price:
        gpt_output = re.sub(
            r'(stock price (is|was|stands at|:)?)(.*?)([\.\n])',
            fr'\1 ${manual_price}\4',
            gpt_output,
            flags=re.IGNORECASE
        )

    gpt_output = re.sub(r'(\*\*|\*|__|_)(.*?)\1', r'\2', gpt_output)
    gpt_output = re.sub(r'(?<!\*)\*(?!\*)(\S.*?)\*', r'\1', gpt_output)
    gpt_output = re.sub(r'(?<!_)_(?!_)(\S.*?)_', r'\1', gpt_output)

    gpt_output = re.sub(
        r'(Short[-\s]?term.*?)\s+(?=Medium[-\s]?term)',
        r'\1\n',
        gpt_output,
        flags=re.IGNORECASE
    )
    gpt_output = re.sub(
        r'(Medium[-\s]?term.*?)\s+(?=Long[-\s]?term)',
        r'\1\n',
        gpt_output,
        flags=re.IGNORECASE
    )

    gpt_output = re.sub(r'(\d+(?:\.\d+)?)([TBM])(?:illion)?(?:\.\d+)?', r'\1\2', gpt_output)
    return gpt_output

if uploaded_file_1 and st.button("🧠 Generate Investment Report"):
    with st.spinner("Analyzing documents and generating professional report..."):

        if manual_price and not manual_price.strip().startswith("$"):
            manual_price = f"{manual_price.strip()}"

        doc_text_1 = extract_text_from_pdf(uploaded_file_1)
        doc_text_2 = extract_text_from_pdf(uploaded_file_2) if uploaded_file_2 else ""
        doc_text_3 = extract_text_from_pdf(uploaded_file_3) if uploaded_file_3 else ""

        extra_data = f" Yahoo Finance Page: {yahoo_url}" if yahoo_url else ""
        full_text = doc_text_1 + "\n\n" + doc_text_2 + "\n\n" + doc_text_3 + extra_data

        result = analyze_text(
            full_text,
            ebitda_mult=ebitda,
            advanced=advanced_mode,
            manual_price=manual_price,
            target_price=target_price
        )

        clean_result = clean_gpt_output(result, manual_price)
        clean_result = re.sub(r'\b(\d+\.\d+)\.\d+\b', r'\1', clean_result)

        st.text_area("📄 Investment Report Output", clean_result, height=600)
        st.download_button("📥 Download Report", clean_result, file_name="AI_Investment_Report.txt")
