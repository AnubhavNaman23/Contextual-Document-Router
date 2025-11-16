"""
Enhanced Modern Web UI for Multi-Format AI System
Built with Streamlit and modern UI components
"""
import streamlit as st
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from main import detect_format, extract_text
from classifier import classify_intent
from shared_memory import load_memory, save_memory
from email_parser import parse_email, extract_email_fields, detect_tone
from format_detector import validate_json_schema

# Page configuration
st.set_page_config(
    page_title="Multi-Format AI System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main {
        background-color: #f5f7fa;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 10px 24px;
        font-size: 16px;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .upload-box {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }
    .sidebar .sidebar-content {
        background-color: #2c3e50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    if 'default_page' not in st.session_state:
        st.session_state.default_page = "📤 Process Documents"


def get_statistics() -> Dict[str, Any]:
    """Get processing statistics from memory"""
    memory = load_memory()
    results = memory.get('results', [])
    
    stats = {
        'total_processed': len(results),
        'by_format': {},
        'by_intent': {},
        'avg_confidence': 0,
        'recent_activities': []
    }
    
    confidences = []
    for result in results:
        # Count by format
        fmt = result.get('input_meta', {}).get('format', 'Unknown')
        stats['by_format'][fmt] = stats['by_format'].get(fmt, 0) + 1
        
        # Count by intent
        intent = result.get('extracted', {}).get('intent', 'Unknown')
        stats['by_intent'][intent] = stats['by_intent'].get(intent, 0) + 1
        
        # Collect confidences
        conf = result.get('extracted', {}).get('confidence', 0)
        if conf:
            confidences.append(float(conf))
        
        # Recent activities
        if len(stats['recent_activities']) < 10:
            stats['recent_activities'].append({
                'timestamp': result.get('timestamp', ''),
                'agent': result.get('agent', ''),
                'intent': intent
            })
    
    if confidences:
        stats['avg_confidence'] = sum(confidences) / len(confidences)
    
    return stats


def display_dashboard():
    """Display main dashboard with statistics"""
    st.title("🤖 Multi-Format AI System Dashboard")
    st.markdown("### Intelligent Document Processing & Classification")
    
    stats = get_statistics()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Processed",
            value=stats['total_processed'],
            delta=f"+{len(st.session_state.processed_files)} today"
        )
    
    with col2:
        st.metric(
            label="🎯 Avg Confidence",
            value=f"{stats['avg_confidence']:.2%}" if stats['avg_confidence'] else "N/A"
        )
    
    with col3:
        most_common_format = max(stats['by_format'].items(), key=lambda x: x[1])[0] if stats['by_format'] else "N/A"
        st.metric(
            label="📄 Top Format",
            value=most_common_format
        )
    
    with col4:
        most_common_intent = max(stats['by_intent'].items(), key=lambda x: x[1])[0] if stats['by_intent'] else "N/A"
        st.metric(
            label="💡 Top Intent",
            value=most_common_intent
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        if stats['by_format']:
            st.markdown("### 📊 Documents by Format")
            fig = go.Figure(data=[go.Pie(
                labels=list(stats['by_format'].keys()),
                values=list(stats['by_format'].values()),
                hole=0.4,
                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
            )])
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if stats['by_intent']:
            st.markdown("### 🎯 Classification by Intent")
            fig = go.Figure(data=[go.Bar(
                x=list(stats['by_intent'].keys()),
                y=list(stats['by_intent'].values()),
                marker=dict(color='#4CAF50')
            )])
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    if stats['recent_activities']:
        st.markdown("### 📝 Recent Activities")
        df = pd.DataFrame(stats['recent_activities'])
        st.dataframe(df, use_container_width=True)


def process_file(file_path: str, file_name: str) -> Dict[str, Any]:
    """Process uploaded file and return results"""
    start_time = time.time()
    
    try:
        # Detect format
        fmt = detect_format(file_path)
        input_text = extract_text(file_path, fmt)
        
        result = {
            'success': True,
            'filename': file_name,
            'format': fmt,
            'processing_time': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Process based on format
        if fmt == 'Email':
            parsed_text = parse_email(input_text)
            email_fields = extract_email_fields(input_text)
            tone = detect_tone(input_text)
            intent, confidence = classify_intent(parsed_text)
            
            result.update({
                'intent': intent,
                'confidence': confidence,
                'fields': email_fields,
                'tone': tone,
                'extracted_text': parsed_text[:500] + '...' if len(parsed_text) > 500 else parsed_text
            })
            
        elif fmt == 'JSON':
            data = json.loads(input_text)
            required_fields = {'event': str, 'timestamp': str, 'payload': dict}
            is_valid, anomalies = validate_json_schema(data, required_fields)
            intent, confidence = classify_intent(str(data))
            
            result.update({
                'intent': intent,
                'confidence': confidence,
                'data': data,
                'schema_valid': is_valid,
                'anomalies': anomalies
            })
            
        elif fmt == 'PDF':
            intent, confidence = classify_intent(input_text)
            result.update({
                'intent': intent,
                'confidence': confidence,
                'text_preview': input_text[:500] + '...' if len(input_text) > 500 else input_text
            })
        
        else:
            result['success'] = False
            result['error'] = f"Unsupported format: {fmt}"
        
        result['processing_time'] = time.time() - start_time
        return result
        
    except Exception as e:
        return {
            'success': False,
            'filename': file_name,
            'error': str(e),
            'processing_time': time.time() - start_time
        }


def display_file_processor():
    """Display file upload and processing interface"""
    st.title("📤 Document Processor")
    st.markdown("### Upload and analyze your documents")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["txt", "json", "pdf", "eml"],
        help="Supported formats: Email (txt, eml), JSON, PDF"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        process_button = st.button("🚀 Process File", use_container_width=True)
    
    if uploaded_file and process_button:
        # Save uploaded file
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        file_path = uploads_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Process file
        with st.spinner("🔄 Processing your document..."):
            result = process_file(str(file_path), uploaded_file.name)
            st.session_state.current_result = result
            st.session_state.processed_files.append(uploaded_file.name)
            st.session_state.processing_history.insert(0, result)
    
    # Display results
    if st.session_state.current_result:
        result = st.session_state.current_result
        
        if result.get('success'):
            st.markdown('<div class="success-box">✅ Processing completed successfully!</div>', unsafe_allow_html=True)
            
            # Results display
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Format", result['format'])
            with col2:
                if 'intent' in result:
                    st.metric("🎯 Intent", result['intent'])
            with col3:
                if 'confidence' in result:
                    confidence = result['confidence']
                    st.metric("📊 Confidence", f"{confidence:.2%}")
            
            # Detailed results
            st.markdown("### 📋 Detailed Results")
            
            tabs = st.tabs(["📊 Overview", "🔍 Extracted Data", "📈 Analysis"])
            
            with tabs[0]:
                st.json({
                    'filename': result['filename'],
                    'format': result['format'],
                    'processing_time': f"{result['processing_time']:.3f}s",
                    'timestamp': result['timestamp']
                })
            
            with tabs[1]:
                if result['format'] == 'Email':
                    st.markdown("**Email Fields:**")
                    st.json(result.get('fields', {}))
                    st.markdown("**Detected Tone:**")
                    st.info(result.get('tone', 'N/A'))
                    st.markdown("**Extracted Text (Preview):**")
                    st.text_area("", result.get('extracted_text', ''), height=200)
                
                elif result['format'] == 'JSON':
                    st.markdown("**JSON Data:**")
                    st.json(result.get('data', {}))
                    if not result.get('schema_valid'):
                        st.warning(f"⚠️ Schema Anomalies: {result.get('anomalies', [])}")
                
                elif result['format'] == 'PDF':
                    st.markdown("**Text Preview:**")
                    st.text_area("", result.get('text_preview', ''), height=300)
            
            with tabs[2]:
                if 'confidence' in result:
                    # Confidence gauge
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=result['confidence'] * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Confidence Score"},
                        delta={'reference': 70},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 75], 'color': "yellow"},
                                {'range': [75, 100], 'color': "green"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Processing metrics
                st.markdown("**Processing Metrics:**")
                metrics_df = pd.DataFrame([{
                    'Metric': 'Processing Time',
                    'Value': f"{result['processing_time']:.3f}s"
                }, {
                    'Metric': 'File Size',
                    'Value': f"{len(uploaded_file.getvalue()) / 1024:.2f} KB"
                }])
                st.table(metrics_df)
        
        else:
            st.markdown(f'<div class="error-box">❌ Error: {result.get("error", "Unknown error")}</div>', unsafe_allow_html=True)


def display_history():
    """Display processing history"""
    st.title("📜 Processing History")
    
    if not st.session_state.processing_history:
        st.info("No processing history available yet.")
        return
    
    st.markdown(f"### Total Records: {len(st.session_state.processing_history)}")
    
    # Create DataFrame
    history_data = []
    for item in st.session_state.processing_history:
        if item.get('success'):
            history_data.append({
                'Timestamp': item.get('timestamp', ''),
                'Filename': item.get('filename', ''),
                'Format': item.get('format', ''),
                'Intent': item.get('intent', 'N/A'),
                'Confidence': f"{item.get('confidence', 0):.2%}",
                'Processing Time': f"{item.get('processing_time', 0):.3f}s"
            })
    
    if history_data:
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"processing_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


def display_settings():
    """Display system settings"""
    st.title("⚙️ System Settings")
    
    st.markdown("### Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Processing Settings")
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.05)
        max_file_size = st.number_input("Max File Size (MB)", 1, 100, 10)
        enable_auto_process = st.checkbox("Auto-process on upload", value=False)
    
    with col2:
        st.markdown("#### Display Settings")
        show_detailed_logs = st.checkbox("Show detailed logs", value=True)
        enable_notifications = st.checkbox("Enable notifications", value=True)
        dark_mode = st.checkbox("Dark mode", value=False)
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")
    
    st.markdown("### System Information")
    st.info(f"""
    **Version:** 2.0.0  
    **Python Version:** {sys.version.split()[0]}  
    **Working Directory:** {os.getcwd()}  
    **Supported Formats:** Email, JSON, PDF
    """)


def main():
    """Main application"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=100)
        st.title("Navigation")
        
        page = st.radio(
            "Go to",
            ["🏠 Dashboard", "📤 Process Documents", "📜 History", "⚙️ Settings"],
            index=1,  # Set default to "Process Documents" (index 1)
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        st.metric("Files Processed", len(st.session_state.processed_files))
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        Multi-Format AI System  
        Version 2.0.0  
        
        Intelligent document processing with AI-powered classification.
        """)
    
    # Main content
    if page == "🏠 Dashboard":
        display_dashboard()
    elif page == "📤 Process Documents":
        display_file_processor()
    elif page == "📜 History":
        display_history()
    elif page == "⚙️ Settings":
        display_settings()


if __name__ == "__main__":
    main()
