import streamlit as st
import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests  # Keep requests for making API calls
from datetime import datetime

# Page configuration
st.set_page_config(page_title="X Analyzer: Financial Assistant Chatbot", page_icon="💰", layout="wide")

# Add Company Name and Logo
st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        color: #4CAF50;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        font-weight: 400;
        color: #777;
    }
    .section-title {
        color: #333;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<p class="title">X Analyzer: Financial Assistant Chatbot</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Providing financial insights and visual analysis for smarter decisions.</p>', unsafe_allow_html=True)

# Theme: Day/Night Mode Toggle
theme = st.selectbox("Choose Theme", ["Day Mode", "Night Mode"])

if theme == "Day Mode":
    st.markdown(
        """
        <style>
        body {
            background-color: #f4f4f9;
            color: #333;
        }
        .title {
            color: #4CAF50;
        }
        .subtitle {
            color: #777;
        }
        </style>
        """, unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body {
            background-color: #2C2C2C;
            color: white;
        }
        .title {
            color: #ff9800;
        }
        .subtitle {
            color: #ccc;
        }
        </style>
        """, unsafe_allow_html=True
    )

# Initialize Groq Client (Directly use `requests` here)
if "groq_client" not in st.session_state:
    api_key = st.sidebar.text_input("Enter your Groq API Key:", type="password")
    if api_key:
        st.session_state.groq_client_api_key = api_key  # Store the API key in the session state
    else:
        st.info("Please enter your Groq API key in the sidebar to start chatting.")
        st.stop()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "system",
        "content": """You are a helpful financial assistant. Provide advice on budgeting, saving, investing, and personal finance. 
        When users provide financial data (like expenses, income, budgets, investments), respond with both advice AND a JSON object 
        for visualization. Format: {"chart_type": "pie|bar|line", "title": "Chart Title", "data": {"labels": [], "values": []}}
        Always remind users to consult with licensed financial advisors for important decisions."""
    })

# Function to extract and visualize data
def create_visualization(text):
    try:
        # Try to extract JSON from response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)

            chart_type = data.get("chart_type", "bar")
            title = data.get("title", "Financial Analysis")
            chart_data = data.get("data", {})

            if "labels" in chart_data and "values" in chart_data:
                df = pd.DataFrame({
                    'Category': chart_data['labels'],
                    'Amount': chart_data['values']
                })

                st.subheader(f"📊 {title}")

                if chart_type == "pie":
                    fig = px.pie(df, names='Category', values='Amount', title=title)
                elif chart_type == "line":
                    fig = px.line(df, x='Category', y='Amount', title=title, markers=True)
                else:  # bar
                    fig = px.bar(df, x='Category', y='Amount', title=title)

                # Customizations for better visual appeal
                fig.update_layout(
                    template="plotly_dark" if theme == "Night Mode" else "plotly_white",
                    title_font=dict(size=24),
                    xaxis_title='Category',
                    yaxis_title='Amount'
                )

                st.plotly_chart(fig, use_container_width=True)
                return True
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
    return False


# Display chat history (excluding system message)
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            create_visualization(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about budgeting, savings, investments..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            headers = {
                'Authorization': f'Bearer {st.session_state.groq_client_api_key}',  # Use the stored API key
                'Content-Type': 'application/json',
            }

            data = {
                "model": "llama-3.3-70b-versatile",
                "messages": st.session_state.messages,
                "temperature": 0.7,
                "max_tokens": 1024,
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                assistant_message = response_data['choices'][0]['message']['content']
                st.markdown(assistant_message)

                # Try to create visualization
                create_visualization(assistant_message)

                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            else:
                st.error(f"Error: {response.status_code} - {response_data.get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Sidebar options
with st.sidebar:
    st.header("Options")
    if st.button("Clear Chat History"):
        st.session_state.messages = [st.session_state.messages[0]]  # Keep system message
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Visualization Examples")
    st.markdown("""
    Try these prompts:
    - "I spend $500 on rent, $300 on groceries, $150 on utilities, $100 on entertainment"
    - "My monthly income is $3000 from salary, $500 from freelance"
    - "Show my investment portfolio: $5000 in stocks, $3000 in bonds, $2000 in crypto"
    """)

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **X Analyzer** is a powerful financial assistant chatbot designed to assist you with budgeting, saving, investing, and analyzing financial data.
    The chatbot provides clear insights and actionable advice based on your financial information.
    """)

# Canvas Mode for Custom Chart Drawing
canvas_mode = st.checkbox("Enable Canvas Mode")

if canvas_mode:
    st.markdown("### Canvas Mode Activated")
    st.markdown("You can now add custom data points to visualize with charts.")
    
    # Collect Data for Custom Visualization
    categories = st.text_area("Enter categories (comma-separated, e.g., Rent, Groceries, Utilities):")
    amounts = st.text_area("Enter corresponding amounts (comma-separated, e.g., 500, 300, 150):")

    if categories and amounts:
        try:
            # Clean and split categories and amounts
            categories = [category.strip() for category in categories.split(",")]
            amounts = [amount.strip() for amount in amounts.split(",")]

            # Convert amounts to float
            amounts = list(map(float, amounts))  # Convert each amount to float

            # Ensure the number of categories matches the number of amounts
            if len(categories) == len(amounts):
                df = pd.DataFrame({
                    'Category': categories,
                    'Amount': amounts
                })

                # Display the custom bar chart
                fig = px.bar(df, x='Category', y='Amount', title="Custom Financial Chart")
                st.plotly_chart(fig)
            else:
                st.error("The number of categories and amounts must be the same.")
        except ValueError as e:
            st.error(f"Error: {str(e)}. Please make sure amounts are numeric values.")
