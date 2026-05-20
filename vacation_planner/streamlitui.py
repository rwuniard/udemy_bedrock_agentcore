import streamlit as st
import os
from datetime import datetime
from src.vacation_planner.crew import VacationPlanner # Replace path 1

st.set_page_config(page_title="Personal AI Vacation Planner ", page_icon="✈️")

# Enhanced CSS styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 0;
}
.subtitle {
    color: #666;
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}
.feature-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.feature-card:hover {
    transform: translateY(-5px);
}
.vacation-container {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">✈️ Personal AI Vacation Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your perfect vacation with AI-powered research and itinerary planning!</p>', unsafe_allow_html=True)

# Enhanced input form
st.markdown("### 🌍 Where would you like to go?")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    with st.form("vacation_form"):
        destination = st.text_input("Destination", placeholder="e.g., London, Paris, Tokyo", help="Enter any city or country you'd like to explore!")
        
        submitted = st.form_submit_button("🚀 Plan My Dream Vacation", type="primary", use_container_width=True)

# Add some popular destinations as quick options
st.markdown("#### 🔥 Popular Destinations")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🗼 Paris", use_container_width=True):
        st.session_state.destination = "Paris"
with col2:
    if st.button("🗾 Tokyo", use_container_width=True):
        st.session_state.destination = "Tokyo"
with col3:
    if st.button("🏛️ Rome", use_container_width=True):
        st.session_state.destination = "Rome"
with col4:
    if st.button("🏖️ Bali", use_container_width=True):
        st.session_state.destination = "Bali"

# Handle quick destination selection
if 'destination' in st.session_state:
    destination = st.session_state.destination
    submitted = True
    del st.session_state.destination

if submitted and destination:
    with st.spinner("🌍 Planning your amazing vacation... This may take a few minutes."):
        try:
            inputs = {
                "topic": destination,
                "current_year": str(datetime.now().year)
            }
            
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text('🔍 Researching destination...')
            progress_bar.progress(25)
            
            # Run the crew
            result = VacationPlanner().crew().kickoff(inputs=inputs)
            
            progress_bar.progress(100)
            status_text.text('✅ Complete!')
            
            st.balloons()
            st.success(f"🎉 Your {destination} vacation plan is ready!")
            
            # Display result in enhanced container
            if os.path.exists("report.md"):
                with open("report.md", "r", encoding="utf-8") as f:
                    report_content = f.read()
                st.markdown('<div class="vacation-container">', unsafe_allow_html=True)
                st.markdown(f"## 🗺️ Your {destination} Adventure Plan")
                st.markdown(report_content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="💾 Download Your Plan",
                    data=report_content,
                    file_name=f"{destination}_vacation_plan.md",
                    mime="text/markdown"
                )
            else:
                st.markdown("## 📋 Result")
                st.write(result)
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("🛠️ Please check your AWS credentials and API keys")

elif submitted:
    st.warning("⚠️ Please enter a destination to start planning!")

# Enhanced sidebar
with st.sidebar:
    st.markdown("### 🌟 What This App Does")
    
    features = [
        ("🔍 Research destinations", "Finds interesting facts and hidden gems", "#667eea", "#764ba2"),
        ("📋 Create detailed itineraries", "Plans your daily activities", "#f093fb", "#f5576c"),
        ("🍽️ Recommend local foods", "Suggests must-try culinary experiences", "#4facfe", "#00f2fe"),
        ("🏛️ Share city history", "Provides cultural context", "#43e97b", "#38f9d7")
    ]
    
    for title, desc, color1, color2 in features:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color1} 0%, {color2} 100%); 
                    padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <p style="color: white; margin: 0; font-weight: bold;">{title}</p>
            <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Destinations Explored", "1000+")
    st.metric("Happy Travelers", "500+")
    
