import streamlit as st
import requests
import json

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
.main-header {
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FECA57, #FF9FF3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-family: 'Poppins', sans-serif;
    font-size: 4rem;
    font-weight: 700;
    text-align: center;
    animation: glow 2s ease-in-out infinite alternate;
}
.powered-by {
    text-align: center;
    font-weight: 900;
    background: linear-gradient(45deg, #FF6B35, #F7931E, #FF0080, #7928CA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-family: 'Poppins', sans-serif;
    font-size: 2.5rem;
    margin: 3rem 0;
    animation: pulse 1.5s infinite;
    text-shadow: 0 0 20px rgba(255,107,53,0.6);
}
.vacation-input {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: 3px solid transparent;
    border-radius: 25px;
    padding: 2.5rem;
    margin: 2rem 0;
    box-shadow: 0 15px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2);
    background-clip: padding-box;
    position: relative;
}
.vacation-input::before {
    content: '';
    position: absolute;
    top: -3px;
    left: -3px;
    right: -3px;
    bottom: -3px;
    background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FECA57, #FF9FF3);
    border-radius: 25px;
    z-index: -1;
    animation: borderGlow 3s ease-in-out infinite alternate;
}
@keyframes borderGlow {
    0% { opacity: 0.7; transform: scale(1); }
    100% { opacity: 1; transform: scale(1.02); }
}
@keyframes glow {
    from { text-shadow: 0 0 20px rgba(255,107,107,0.5); }
    to { text-shadow: 0 0 30px rgba(78,205,196,0.8); }
}
@keyframes pulse {
    0% { transform: scale(1); opacity: 0.8; }
    50% { transform: scale(1.15); opacity: 1; }
    100% { transform: scale(1); opacity: 0.8; }
}
</style>
""", unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    st.markdown("### 🌎 Menu")
    menu = st.selectbox("Navigation", ["Plan Vacation", "About", "Contact"], label_visibility="collapsed")

st.markdown('<h1 class="main-header">✈️ Vacation Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="powered-by">Powered by Amazon Bedrock AgentCore</p>', unsafe_allow_html=True)

#1 Replace with your actual API endpoint
API_URL = "https://hqdxhy4pu1.execute-api.us-west-2.amazonaws.com/dev/vacation_planner_resource"

if menu == "Plan Vacation":
    st.markdown('<div class="vacation-input">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        destination = st.text_input("🌍 Dream Destination:", placeholder="✨ Paris, Tokyo, Bali, Rome...")
    st.markdown('</div>', unsafe_allow_html=True)

    # Quick destination buttons
    st.markdown("### 🔥 Popular Destinations")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🗼 Paris", use_container_width=True):
            destination = "Paris"
    with col2:
        if st.button("🗾 Tokyo", use_container_width=True):
            destination = "Tokyo"
    with col3:
        if st.button("🏛️ Rome", use_container_width=True):
            destination = "Rome"
    with col4:
        if st.button("🏖️ Bali", use_container_width=True):
            destination = "Bali"

    if st.button("🚀 Plan My Dream Vacation", type="primary"):
        if destination:
            with st.spinner("Planning your vacation..."):
                try:
                    response = requests.post(API_URL, json={"prompt": destination})
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.balloons()
                        st.success(f"🎉 Your {destination} vacation plan is ready!")
                        st.markdown("## 🗺️ Your Dream Vacation Plan")
                        st.markdown(f"**Destination:** {destination}")

                        # API Gateway wraps Lambda body as a JSON string
                        body = json.loads(data["body"]) if isinstance(data.get("body"), str) else data
                        result = body.get("result")

                        if isinstance(result, dict) and "error" in result:
                            st.error(result["error"])
                        elif isinstance(result, str):
                            st.markdown(result)
                        else:
                            st.markdown(str(result))
                    else:
                        st.error(f"API Error: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a destination")

elif menu == "About":
    st.markdown("## 🎆 About Vacation Planner")
    st.write("AI-powered vacation planning using Amazon Bedrock AgentCore")
    
elif menu == "Contact":
    st.markdown("## 📞 Contact Us")
    st.write("📧 Email: support@vacationplanner.ai")