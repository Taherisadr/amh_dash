import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests
import time  # ⏰ for typing effect
import re



def clean_response_text(text):
    # Add space after punctuation if missing
    text = re.sub(r"([.,!?])([^\s])", r"\1 \2", text)
    # Add space between number/letter and parentheses
    text = re.sub(r"(\d|\w)([\(\)])", r"\1 \2", text)
    text = re.sub(r"([\(\)])(\d|\w)", r"\1 \2", text)
    # Add space between lowercase-uppercase if stuck together
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    # ⭐ Add space after period if next letter is Uppercase
    text = re.sub(r"(\.)([A-Z])", r"\1 \2", text)
    return text

# ----------------------
# 📦 Load Data Functions
# ----------------------
@st.cache_data
def load_data():
    df = pd.read_excel('Asset Level Data-Binary Assesment.xlsb', sheet_name='Asset Level Data', engine='pyxlsb')
    df['ZipCode'] = df['ZipCode'].astype(str).str.zfill(5).str.strip()
    return df

@st.cache_data
def load_zip_lat_lon():
    zip_df = pd.read_csv('final_us_zip_latlon_full.csv')
    zip_df['ZipCode'] = zip_df['ZipCode'].astype(str).str.zfill(5).str.strip()
    zip_lat_lon = dict(zip(zip_df['ZipCode'], zip_df[['Latitude', 'Longitude']].values))
    return zip_lat_lon

# ----------------------
# 📈 Load the Data
# ----------------------
data = load_data()
zip_lookup = load_zip_lat_lon()

# Initialize scroll target
if "scroll_to_section" not in st.session_state:
    st.session_state.scroll_to_section = None

st.title("🏡 Asset Level Data Dashboard")

st.markdown("""
This dashboard allows you to manually input values for financial features and visualize calculated output features.
""")

# ----------------------
# 📋 Sidebar for Input Features
# ----------------------
st.sidebar.header("Input Features")

property_list = data['Property'].unique()
selected_property = st.sidebar.selectbox("Select Property", property_list)

# Initialize or update session state for property selection
if "last_selected_property" not in st.session_state:
    st.session_state.last_selected_property = selected_property

if selected_property != st.session_state.last_selected_property:
    st.session_state.messages = []
    st.session_state.inputs = {}
    st.session_state.last_selected_property = selected_property
    st.session_state.scroll_to_section = "outputs"
    st.rerun()

selected_data = data[data['Property'] == selected_property].iloc[0]

# Manual Inputs
total_hoa = st.sidebar.number_input("Total HOA LTM", value=float(selected_data['Total HOA LTM']))
insurance = st.sidebar.number_input("Insurance LTM", value=float(selected_data['Insurance LTM']))
property_tax = st.sidebar.number_input("Property Tax LTM", value=float(selected_data['Property Tax LTM']))
opex_total = st.sidebar.number_input("Opex Total Expenses LTM", value=float(selected_data.get('Opex Total Expenses LTM', 0)))
capex_total = st.sidebar.number_input("Capex Grand Total LTM", value=float(selected_data.get('Capex Grand Total LTM', 0)))
capex_rec = st.sidebar.number_input("Capex Rec Total LTM", value=float(selected_data.get('Capex Rec Total LTM', 0)))
estimated_rent = st.sidebar.number_input("Estimated Annual Rent LTM", value=float(selected_data.get('Estimated Annual Rent LTM', 0)))
market_value = st.sidebar.number_input("Market Value Of Asset LTM", value=float(selected_data.get('Market Value Of Asset LTM', 0)))
rental_collection_pct = st.sidebar.number_input("Rental Collections Percentage", min_value=0.0, max_value=100.0, value=float(selected_data.get('Rental Collections Percentage', 100.0)))

# 🛠️ Detect if any input changed and reset chat if so
if "inputs" not in st.session_state:
    st.session_state.inputs = {
        "total_hoa": total_hoa,
        "insurance": insurance,
        "property_tax": property_tax,
        "opex_total": opex_total,
        "capex_total": capex_total,
        "capex_rec": capex_rec,
        "estimated_rent": estimated_rent,
        "market_value": market_value,
        "rental_collection_pct": rental_collection_pct
    }

current_inputs = {
    "total_hoa": total_hoa,
    "insurance": insurance,
    "property_tax": property_tax,
    "opex_total": opex_total,
    "capex_total": capex_total,
    "capex_rec": capex_rec,
    "estimated_rent": estimated_rent,
    "market_value": market_value,
    "rental_collection_pct": rental_collection_pct
}

if current_inputs != st.session_state.inputs:
    st.session_state.messages = []
    st.session_state.inputs = current_inputs
    st.session_state.scroll_to_section = "outputs"
    st.rerun()

# ----------------------
# 📊 Calculate Outputs
# ----------------------

# Anchor for outputs
st.markdown('<div id="outputs"></div>', unsafe_allow_html=True)

net_revenue_ltm = estimated_rent * (rental_collection_pct / 100)
gross_yield_pct = (net_revenue_ltm - total_hoa - insurance - property_tax) / market_value if market_value else np.nan
noi_ltm = net_revenue_ltm - opex_total
economic_noi_ltm = net_revenue_ltm - opex_total - capex_total
all_in_noi_ltm = net_revenue_ltm - opex_total - capex_total - capex_rec
noi_margin_ltm = noi_ltm / net_revenue_ltm if net_revenue_ltm else np.nan
economic_noi_margin_ltm = economic_noi_ltm / net_revenue_ltm if net_revenue_ltm else np.nan
all_in_noi_margin_ltm = all_in_noi_ltm / net_revenue_ltm if net_revenue_ltm else np.nan
noi_yield_ltm = noi_ltm / market_value if market_value else np.nan
economic_noi_yield_ltm = economic_noi_ltm / market_value if market_value else np.nan
all_in_noi_yield_ltm = all_in_noi_ltm / market_value if market_value else np.nan

output_df = pd.DataFrame({
    "Output Features": [
        "Net Revenue LTM",
        "Gross Yield Pct. Asset Value Property Level LTM",
        "NOI LTM",
        "Economic NOI LTM",
        "All In NOI LTM",
        "NOI Margin LTM",
        "Economic NOI Margin LTM",
        "All In NOI Margin LTM",
        "NOI Yield LTM",
        "Economic NOI Yield LTM",
        "All In NOI Yield LTM"
    ],
    "Values": [
        net_revenue_ltm,
        gross_yield_pct,
        noi_ltm,
        economic_noi_ltm,
        all_in_noi_ltm,
        noi_margin_ltm,
        economic_noi_margin_ltm,
        all_in_noi_margin_ltm,
        noi_yield_ltm,
        economic_noi_yield_ltm,
        all_in_noi_yield_ltm
    ]
})

# ----------------------
# 📋 Display Table
# ----------------------
st.subheader(f"Calculated Output Features for Property: {selected_property}")
st.table(output_df.style.format({"Values": "{:.4f}"}))

# ----------------------
# 💾 Download CSV
# ----------------------
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(output_df)
st.download_button(
    label="Download Output Features as CSV",
    data=csv,
    file_name=f'output_features_{selected_property}.csv',
    mime='text/csv',
)

# ----------------------
# 🗺️ Show Map
# ----------------------
coords = zip_lookup.get(selected_data['ZipCode'], [np.nan, np.nan])

if not np.isnan(coords[0]) and not np.isnan(coords[1]):
    st.subheader("Property Location")

    map_data = pd.DataFrame({
        "lat": [coords[0]],
        "lon": [coords[1]],
        "Property": [selected_property],
        "ZipCode": [selected_data['ZipCode']]
    })

    view_state = pdk.ViewState(latitude=coords[0], longitude=coords[1], zoom=12, pitch=0)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position='[lon, lat]',
        get_fill_color=[255, 0, 0],
        get_radius=10,
        radius_units='pixels',
        pickable=True,
    )

    tooltip = {
        "html": "<b>Property:</b> {Property} <br/> <b>ZIP:</b> {ZipCode}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    ))
else:
    st.warning(f"Missing location for ZIP code: {selected_data['ZipCode']}")

# ----------------------
# 🔥 Chatbot Assistant (with Typing Effect)
# ----------------------
st.markdown("---")
st.markdown('<div id="chatbot"></div>', unsafe_allow_html=True)
st.header("💬 Need Help? Ask Our Dashboard Assistant!")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Clear chat button
if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.session_state.scroll_to_section = "chatbot"
    st.rerun()

# Predefined quick questions
st.subheader("🔍 Quick Questions:")
col1, col2, col3 = st.columns(3)

user_input = None
with col1:
    if st.button("Evaluate Property"):
        user_input = "Based on my numbers, how would you evaluate my property investment?"
with col2:
    if st.button("Summarize NOI"):
        user_input = "Can you summarize my Net Operating Income (NOI) and what affects it?"
with col3:
    if st.button("Explain Gross Yield"):
        user_input = "Can you explain my Gross Yield Percentage based on the dashboard?"

# Free text input
if user_input is None:
    user_input = st.chat_input("Ask me anything about the dashboard, your inputs, or outputs...")

if user_input:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "user", "content": user_input})

    user_context = f"""
    The user is working with property: {selected_property}.
    Manual inputs:
    - Total HOA LTM: {total_hoa}
    - Insurance LTM: {insurance}
    - Property Tax LTM: {property_tax}
    - Opex Total Expenses LTM: {opex_total}
    - Capex Grand Total LTM: {capex_total}
    - Capex Rec Total LTM: {capex_rec}
    - Estimated Annual Rent LTM: {estimated_rent}
    - Market Value Of Asset LTM: {market_value}
    - Rental Collections Percentage: {rental_collection_pct}%

    Calculated outputs:
    - Net Revenue LTM: {net_revenue_ltm}
    - Gross Yield Pct: {gross_yield_pct}
    - NOI LTM: {noi_ltm}
    - Economic NOI LTM: {economic_noi_ltm}
    - All In NOI LTM: {all_in_noi_ltm}
    - NOI Margin LTM: {noi_margin_ltm}
    - Economic NOI Margin LTM: {economic_noi_margin_ltm}
    - All In NOI Margin LTM: {all_in_noi_margin_ltm}
    - NOI Yield LTM: {noi_yield_ltm}
    - Economic NOI Yield LTM: {economic_noi_yield_ltm}
    - All In NOI Yield LTM: {all_in_noi_yield_ltm}
    """

    OPENROUTER_API_KEY = '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'  # 🚨 Replace with your real key
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": user_context},
            {"role": "user", "content": user_input}
        ]
    }

    with st.spinner("Assistant is thinking..."):
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": reply})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "❌ Failed to get a response. Please try again later."})

    st.session_state.scroll_to_section = "chatbot"
    st.rerun()

# 🖼️ Show full conversation (with Typing Effect)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            placeholder = st.empty()
            full_reply = ""
            assistant_text = clean_response_text(msg["content"])  # 🔥 cleaned text
            for char in assistant_text:
                full_reply += char
                placeholder.write(full_reply)
                time.sleep(0.01)
        else:
            st.markdown(msg["content"])


# ----------------------
# 🚀 Smooth Scroll After Rerun
# ----------------------
if st.session_state.scroll_to_section:
    scroll_target = st.session_state.scroll_to_section
    st.session_state.scroll_to_section = None
    st.markdown(f"""
        <script>
            const element = document.getElementById("{scroll_target}");
            if (element) {{
                element.scrollIntoView({{ behavior: 'smooth' }});
            }}
        </script>
    """, unsafe_allow_html=True)
