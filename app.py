import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import hashlib
import time

st.set_page_config(
    page_title="Student Enrollment and Pricing Analytics System",
    page_icon="📊",
    layout="wide"
)

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?,?)",
                  (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return result is not None

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/pragyanaischool/VTU_Internship_DataSets/refs/heads/main/student_PRICING_SCHOLARSHIP_Analysis_Project_12.csv"
    df = pd.read_csv(url)
    return df

init_db()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.authenticated:
    st.title("📊 PragyanAI Pricing & Scholarship Intelligence Engine")
    st.markdown("#### Please login to access the dashboard")
    st.divider()

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Register")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password",
                                  type="password", key="reg_pass")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("Registered! Please login.")
            else:
                st.error("Username already exists.")

else:
    st.sidebar.title("📊 PragyanAI BI Dashboard")
    st.sidebar.write(f"Welcome, **{st.session_state.username}** 👋")
    st.sidebar.divider()

    page = st.sidebar.radio("Navigate", [
        "🏠 Overview",
        "📈 Program Analysis",
        "🎯 Discount Analysis",
        "🏫 College Tier Analysis",
        "🔥 Correlation",
        "🤖 Ask AI",
        "📥 Export Data"
    ])

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    with st.spinner("Loading data..."):
        df = load_data()

    st.sidebar.divider()
    st.sidebar.subheader("Filters")

    program_filter = st.sidebar.multiselect(
        "Program Type",
        options=df['Program_Type'].unique(),
        default=df['Program_Type'].unique()
    )
    tier_filter = st.sidebar.multiselect(
        "College Tier",
        options=sorted(df['College_Tier'].unique()),
        default=sorted(df['College_Tier'].unique())
    )
    discount_filter = st.sidebar.slider(
        "Discount % Range",
        min_value=0, max_value=50,
        value=(0, 50)
    )

    filtered_df = df[
        (df['Program_Type'].isin(program_filter)) &
        (df['College_Tier'].isin(tier_filter)) &
        (df['Discount_%'] >= discount_filter[0]) &
        (df['Discount_%'] <= discount_filter[1])
    ]

    if page == "🏠 Overview":
        st.title("📊 Student Enrollment and Pricing Analytics System")
        st.markdown("**Internship Project | Sahana M S | 4GM22AI127 | PragyanAI**")
        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Students", f"{len(filtered_df):,}")
        col2.metric("Total Enrolled", f"{int(filtered_df['Converted'].sum()):,}")
        col3.metric("Conversion Rate", f"{filtered_df['Converted'].mean()*100:.1f}%")
        col4.metric("Total Revenue", f"₹{filtered_df['Revenue'].sum()/10000000:.1f} Cr")

        st.divider()
        col5, col6 = st.columns(2)
        col5.metric("Avg Final Price", f"₹{filtered_df['Final_Price'].mean():,.0f}")
        col6.metric("Avg Discount Given", f"{filtered_df['Discount_%'].mean():.1f}%")

        st.divider()
        st.subheader("Dataset Preview")
        st.dataframe(filtered_df.head(20), use_container_width=True)

    elif page == "📈 Program Analysis":
        st.title("📈 Program Type Analysis")
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            prog_rev = filtered_df.groupby(
                'Program_Type')['Revenue'].sum().reset_index()
            prog_rev['Revenue_Cr'] = (
                prog_rev['Revenue']/10000000).round(2)
            fig1 = px.bar(prog_rev, x='Program_Type', y='Revenue_Cr',
                          title='Revenue by Program Type (Crores ₹)',
                          color='Program_Type', text='Revenue_Cr')
            fig1.update_traces(texttemplate='₹%{text}Cr',
                               textposition='outside')
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            prog_conv = filtered_df.groupby(
                'Program_Type')['Converted'].mean().reset_index()
            prog_conv['Conversion_%'] = (
                prog_conv['Converted']*100).round(1)
            fig2 = px.bar(prog_conv, x='Program_Type', y='Conversion_%',
                          title='Conversion Rate by Program Type (%)',
                          color='Program_Type', text='Conversion_%')
            fig2.update_traces(texttemplate='%{text}%',
                               textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)

        prog_price = filtered_df.groupby(
            'Program_Type')['Final_Price'].mean().reset_index()
        prog_price['Avg_Price'] = prog_price['Final_Price'].round(0)
        fig3 = px.bar(prog_price, x='Program_Type', y='Avg_Price',
                      title='Average Final Price by Program Type (₹)',
                      color='Program_Type', text='Avg_Price')
        fig3.update_traces(texttemplate='₹%{text:,.0f}',
                           textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)

    elif page == "🎯 Discount Analysis":
        st.title("🎯 Discount vs Conversion Analysis")
        st.divider()

        disc_conv = filtered_df.groupby('Discount_%').agg(
            Conversion_Rate=('Converted', 'mean'),
            Total_Students=('Student_ID', 'count')
        ).reset_index()
        disc_conv['Conversion_Rate'] = (
            disc_conv['Conversion_Rate']*100).round(1)

        fig1 = px.line(disc_conv, x='Discount_%', y='Conversion_Rate',
                       title='How Discount % Affects Conversion Rate',
                       markers=True)
        fig1.add_vline(x=20, line_dash="dash", line_color="red",
                       annotation_text="Optimal: 20%")
        st.plotly_chart(fig1, use_container_width=True)

        st.info("💡 Key Insight: 20% discount is the sweet spot. "
                "Below 20% conversion is ~48%. "
                "At 20% it jumps to 70%. "
                "Above 20% no further improvement!")

        fig2 = px.histogram(filtered_df, x='Final_Price', nbins=40,
                            title='Distribution of Final Price Paid')
        st.plotly_chart(fig2, use_container_width=True)

    elif page == "🏫 College Tier Analysis":
        st.title("🏫 College Tier Analysis")
        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            tier_conv = filtered_df.groupby(
                'College_Tier')['Converted'].mean().reset_index()
            tier_conv['Conversion_%'] = (
                tier_conv['Converted']*100).round(1)
            fig1 = px.bar(tier_conv, x='College_Tier', y='Conversion_%',
                          title='Conversion Rate by College Tier (%)',
                          color='College_Tier', text='Conversion_%')
            fig1.update_traces(texttemplate='%{text}%',
                               textposition='outside')
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            tier_rev = filtered_df.groupby(
                'College_Tier')['Revenue'].sum().reset_index()
            tier_rev['Revenue_Cr'] = (
                tier_rev['Revenue']/10000000).round(2)
            fig2 = px.bar(tier_rev, x='College_Tier', y='Revenue_Cr',
                          title='Revenue by College Tier (Crores ₹)',
                          color='College_Tier', text='Revenue_Cr')
            fig2.update_traces(texttemplate='₹%{text}Cr',
                               textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)

        income_conv = filtered_df.groupby(
            'Family_Income')['Converted'].mean().reset_index()
        income_conv['Conversion_%'] = (
            income_conv['Converted']*100).round(1)
        fig3 = px.bar(income_conv, x='Family_Income', y='Conversion_%',
                      title='Conversion Rate by Family Income Group (%)',
                      color='Family_Income', text='Conversion_%')
        fig3.update_traces(texttemplate='%{text}%',
                           textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)

    elif page == "🔥 Correlation":
        st.title("🔥 Correlation Heatmap")
        st.divider()

        fig, ax = plt.subplots(figsize=(8, 6))
        corr = filtered_df[['College_Tier', 'Base_Price', 'Discount_%',
                             'Final_Price', 'Converted', 'Revenue']].corr()
        sns.heatmap(corr, annot=True, fmt='.2f',
                    cmap='coolwarm', center=0,
                    square=True, ax=ax)
        ax.set_title('Correlation Heatmap — Project 12')
        plt.tight_layout()
        st.pyplot(fig)

        st.info("💡 Converted ↔ Revenue = 0.75 (strong). "
                "Discount_% ↔ Revenue = -0.04 "
                "(more discount does NOT mean more revenue!)")

    elif page == "🤖 Ask AI":
        st.title("🤖 Ask AI About Your Data")
        st.markdown("Ask any question about the dataset in plain English!")
        st.divider()

        data_summary = f"""
        Dataset Summary for PragyanAI Pricing Project:
        - Total Students: {len(filtered_df):,}
        - Total Enrolled: {int(filtered_df['Converted'].sum()):,}
        - Conversion Rate: {filtered_df['Converted'].mean()*100:.1f}%
        - Total Revenue: Rs {filtered_df['Revenue'].sum()/10000000:.1f} Crores
        - Avg Final Price: Rs {filtered_df['Final_Price'].mean():,.0f}
        - Avg Discount: {filtered_df['Discount_%'].mean():.1f}%
        - Programs: {', '.join(filtered_df['Program_Type'].unique())}
        - College Tiers: {sorted(filtered_df['College_Tier'].unique())}
        - Revenue by Program:
          {filtered_df.groupby('Program_Type')['Revenue'].sum().to_string()}
        - Conversion by Discount%:
          {filtered_df.groupby('Discount_%')['Converted'].mean().mul(100).round(1).to_string()}
        - Conversion by College Tier:
          {filtered_df.groupby('College_Tier')['Converted'].mean().mul(100).round(1).to_string()}
        """

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_question = st.chat_input("Ask something about the data...")

        if user_question:
            st.session_state.messages.append({
                "role": "user",
                "content": user_question
            })
            with st.chat_message("user"):
                st.write(user_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        from groq import Groq
                        client = Groq(
                            api_key=st.secrets["GROQ_API_KEY"]
                        )
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {
                                    "role": "system",
                                    "content": f"""You are a Data Science 
                                    assistant analysing PragyanAI student 
                                    pricing data. Answer based on this summary:
                                    {data_summary}
                                    Keep answers short and data-driven.
                                    Use Indian number formatting."""
                                },
                                {
                                    "role": "user",
                                    "content": user_question
                                }
                            ],
                            max_tokens=500
                        )
                        answer = response.choices[0].message.content
                        st.write(answer)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })
                    except Exception as e:
                        st.error(f"AI unavailable: {e}")

        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    elif page == "📥 Export Data":
        st.title("📥 Export Filtered Data")
        st.divider()

        st.write(f"Filtered dataset: **{len(filtered_df):,} rows**")
        st.dataframe(filtered_df.head(50), use_container_width=True)

        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Filtered CSV",
            data=csv,
            file_name="project12_filtered.csv",
            mime="text/csv"
        )

        st.divider()
        st.subheader("Real-Time Simulation")
        if st.checkbox("Enable Auto Refresh (every 10 seconds)"):
            st.info("🔄 Refreshing every 10 seconds...")
            time.sleep(10)
            st.rerun()
