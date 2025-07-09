import streamlit as st
import sys
import os

# Add the current directory to Python path to import orchestrator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from orchestrator import process_legal_query
except ImportError:
    st.error("orchestrator.py not found. Please ensure it's in the same directory as this app.")
    st.stop()

def main():
    # Page configuration
    st.set_page_config(
        page_title="EU Legal Q&A Assistant",
        page_icon="🇪🇺",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header with EU flag and title
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <h1>🇪🇺 EU Legal Q&A Assistant</h1>
            <p style="font-size: 18px; color: #666;">
                AI-powered legal guidance for European Union law
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Scope and instructions
    st.markdown("""
    ---
    ### 📋 **Scope & Instructions**
    
    **🎯 Scope:** This chatbot provides information and guidance exclusively on **European Union (EU) laws**. Concretly, it focuses on the laws included in the [eur-lex-sum dataset](https://huggingface.co/datasets/dennlinger/eur-lex-sum/tree/main/data/english), where more than 1.500 EU laws are listed.
    
    **❗ Important:** This tool provides general information only and should not replace professional legal advice.
    
    **🔗 Official EU Legal Database:** [EUR-Lex - Access to European Union Law](https://eur-lex.europa.eu/homepage.html)
    
    ---
    """)
    
    # Main query interface
    st.subheader("💬 Ask Your Legal Question")
    
    # Create a form for better UX
    with st.form("legal_query_form"):
        user_query = st.text_area(
            "Enter your EU legal question:",
            height=120,
            placeholder="Example: What are the key requirements for GDPR compliance for small businesses?",
            help="Be specific about your legal question for better results."
        )
        
        submitted = st.form_submit_button("🔍 Get Legal Guidance", use_container_width=True)
    
    # Process query when submitted
    if submitted:
        if user_query.strip():
            with st.spinner("🤖 Analyzing your legal question..."):
                try:
                    # Call orchestrator.py to process the query
                    response = process_legal_query(user_query)
                    
                    # Display response
                    st.subheader("📖 Legal Guidance")
                    st.markdown(response)
                    
                    # Disclaimer
                    st.markdown("""
                    ---
                    **⚖️ Legal Disclaimer:** This response is for informational purposes only and does not constitute legal advice. 
                    For specific legal matters, please consult with a qualified legal professional.
                    """)
                    
                except Exception as e:
                    st.error(f"❌ Error processing your query: {str(e)}")
                    st.info("Please try rephrasing your question or contact support if the issue persists.")
        else:
            st.warning("⚠️ Please enter a legal question to get started.")
    
    # Footer
    st.markdown("""
    ---
    <div style="text-align: center; color: #888; font-size: 12px;">
        <p>🇪🇺 EU Legal Q&A Assistant | <b>🦈 The Sharks</b> | ELLIS ESSIR 2025</p>
        <p>📚 Official source: <a href="https://eur-lex.europa.eu/homepage.html" target="_blank">EUR-Lex</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
