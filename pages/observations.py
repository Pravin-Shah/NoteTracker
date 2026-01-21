"""
Observation Page - Simple screen to log trading observations.
"""
import streamlit as st
import os
import sys
from datetime import datetime

# Add root to sys.path if not present (crucial for imports when running via Home.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ui_components import set_compact_layout, render_success_message, render_error_message
from apps.tradevault.utils.observation_ops import (
    create_observation, search_observations, add_observation_tag, 
    add_observation_screenshot, delete_observation
)

from streamlit_paste_button import paste_image_button
import io
import hashlib

def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk and return path."""
    import shutil
    upload_dir = "data/uploads/observations"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def save_pasted_image(image_data):
    """Save PIL image to disk and return path."""
    upload_dir = "data/uploads/observations"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Hash content to prevent duplicates
    img_byte_arr = io.BytesIO()
    image_data.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    img_hash = hashlib.md5(img_bytes).hexdigest()
    
    # Check if already in session state
    if img_hash in st.session_state.get('processed_pastes', []):
        return None
        
    if 'processed_pastes' not in st.session_state:
        st.session_state.processed_pastes = []
    st.session_state.processed_pastes.append(img_hash)
    
    file_path = os.path.join(upload_dir, f"pasted_{datetime.now().timestamp()}.png")
    image_data.save(file_path, "PNG")
    return file_path

@st.dialog("Image Gallery", width="large")
def show_image_dialog(images, start_index):
    """
    Dialog to show images in full size with navigation.
    params:
        images: list of dicts with 'file_path' key or str paths
        start_index: initial index to show
    """
    if "gallery_index" not in st.session_state:
        st.session_state.gallery_index = start_index

    # Ensure index is within bounds
    current_idx = st.session_state.gallery_index % len(images)
    
    # Get current image path
    current_img = images[current_idx]
    current_path = current_img['file_path'] if isinstance(current_img, dict) else current_img

    # Display Image
    st.image(current_path, use_container_width=True)
    
    # Caption if available
    if isinstance(current_img, dict) and current_img.get('caption'):
        st.caption(current_img['caption'])
        
    st.write(f"Image {current_idx + 1} of {len(images)}")

    # Navigation Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", use_container_width=True):
            st.session_state.gallery_index = (current_idx - 1) % len(images)
            st.rerun()
            
    with col3:
        if st.button("Next ➡️", use_container_width=True):
            st.session_state.gallery_index = (current_idx + 1) % len(images)
            st.rerun()

def main():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
        
    if 'pasted_images' not in st.session_state:
        st.session_state.pasted_images = []

    set_compact_layout()
    
    # Custom CSS for Telegram/Chat-like Card UI with ULTRA-tight spacing
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
        .stButton button { padding: 0px 12px !important; font-size: 0.8rem !important; height: 32px !important; margin: 0 !important; }
        
        /* Card Container */
        .obs-card { 
            background-color: white; 
            border-radius: 12px; 
            padding: 10px 12px; 
            margin-bottom: 12px; 
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            max-width: 700px;
        }
        
        /* Header: Stock Name - ZERO bottom margin */
        .obs-header { 
            color: #0891b2; 
            font-weight: 700; 
            font-size: 0.95rem; 
            margin-bottom: 0px !important; /* ZERO gap */
            margin-top: 0px !important;
            padding-bottom: 0px !important;
            font-family: sans-serif;
            line-height: 1.1;
        }
        
        /* Text Content */
        .obs-text { 
            font-size: 0.95rem; 
            color: #1f2937; 
            line-height: 1.4; 
            margin-top: 0px !important; /* ZERO gap from button */
            margin-bottom: 4px;
            padding-top: 0px !important;
            white-space: pre-wrap; 
        }
        
        /* Footer: Time & Tags */
        .obs-footer { 
            display: flex; 
            justify-content: flex-end; 
            align-items: center; 
            margin-top: 2px; 
            font-size: 0.75rem; 
            color: #9ca3af; 
            gap: 8px;
        }
        
        .tag-pill { 
            background-color: #f3f4f6; 
            color: #4b5563; 
            padding: 1px 8px; 
            border-radius: 99px; 
            font-size: 0.7rem; 
        }
        
        /* Aggressively remove ALL image margins */
        div[data-testid="stImage"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Remove element container margins */
        .element-container {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("👁️ Market Observations")

    # --- INPUT FORM ---
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
        
    if 'reset_form' in st.session_state and st.session_state.reset_form:
        st.session_state.obs_stock_name = "Nifty"
        st.session_state.obs_tags = ""
        st.session_state.obs_text = ""
        st.session_state.form_key += 1
        st.session_state.reset_form = False

    with st.expander("➕ Log New Observation", expanded=False):
        c1, c2 = st.columns([1, 2], gap="small")
        with c1:
            stock_name = st.selectbox("Stock", options=["Nifty", "NiftyFut", "BankNifty", "BankNiftyFut", "FinNifty", "CrudeOil", "Gold", "Stocks"], key="obs_stock_name", label_visibility="collapsed")
        with c2:
            tags_input = st.text_input("Tags", placeholder="Tags...", key="obs_tags", label_visibility="collapsed")
            
        observation_text = st.text_area("Observation", height=80, placeholder="Details...", key="obs_text", label_visibility="collapsed")
        
        c_p, c_u = st.columns([1, 2], gap="small")
        with c_p:
             paste_result = paste_image_button(
                label="📋 Paste",
                background_color="#4CAF50",
                hover_background_color="#45a049",
                key=f"paste_btn_{st.session_state.form_key}"
            )
        with c_u:
            uploaded_files = st.file_uploader("Upload", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], label_visibility="collapsed", key=f"obs_files_{st.session_state.form_key}")

        if paste_result.image_data is not None:
             saved_path = save_pasted_image(paste_result.image_data)
             if saved_path: st.session_state.pasted_images.append(saved_path)

        if st.session_state.pasted_images:
            st.caption(f"📎 {len(st.session_state.pasted_images)} images")
        
        b_save, b_clear = st.columns([4, 1], gap="small")
        with b_save:
            if st.button("💾 Save", use_container_width=True, type="primary"):
                if not observation_text.strip():
                    st.error("Text required")
                else:
                    try:
                        obs_id = create_observation(st.session_state.user_id, {'stock_name': stock_name, 'observation_text': observation_text})
                        if tags_input:
                            for tag in [t.strip() for t in tags_input.split(',') if t.strip()]: add_observation_tag(obs_id, tag)
                        if uploaded_files:
                            for f in uploaded_files: add_observation_screenshot(obs_id, save_uploaded_file(f))
                        if st.session_state.pasted_images:
                            for p in st.session_state.pasted_images: add_observation_screenshot(obs_id, p)
                        
                        st.success("Saved!")
                        st.session_state.pasted_images = []
                        st.session_state.processed_pastes = []
                        st.session_state.reset_form = True
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
        with b_clear:
            if st.button("Clear", use_container_width=True):
                st.session_state.pasted_images = []
                st.session_state.reset_form = True
                st.rerun()

    # --- SEARCH & FEED ---
    fs_c1, fs_c2 = st.columns([1, 3], gap="small")
    with fs_c1: filter_stock = st.selectbox("Filter", ["All", "Nifty", "NiftyFut", "BankNifty", "BankNiftyFut", "FinNifty"], label_visibility="collapsed")
    with fs_c2: search_query = st.text_input("Search", placeholder="Search...", label_visibility="collapsed")

    observations = search_observations(st.session_state.user_id, query=search_query, stock_name=filter_stock)
    
    if not observations:
        st.info("No observations found.")
    else:
        for obs in observations:
            with st.container():
                # Start Card
                st.markdown(f'<div class="obs-card">', unsafe_allow_html=True)
                
                # Header & Close
                h_c1, h_c2 = st.columns([10, 1])
                with h_c1:
                    st.markdown(f'<div class="obs-header">{obs["stock_name"]}</div>', unsafe_allow_html=True)
                with h_c2:
                    if st.button("×", key=f"d_{obs['id']}", help="Delete"):
                        delete_observation(st.session_state.user_id, obs['id'])
                        st.rerun()

                # Image (Tight Gap)
                if obs.get('screenshots'):
                    # Aggressive margin hack to pull image up VERY close to header
                    st.markdown('<div style="margin-top: -24px;"></div>', unsafe_allow_html=True)
                    
                    main_img = obs['screenshots'][0]
                    # Reduced size (width=550) or approx standard chat width
                    st.image(main_img['file_path'], width=550)
                    
                    if len(obs['screenshots']) > 1:
                        if st.button(f"+ {len(obs['screenshots'])-1} more (Open Gallery)", key=f"vg_{obs['id']}"):
                            st.session_state.gallery_index = 0
                            show_image_dialog(obs['screenshots'], 0)
                
                # Text Content (Tight Gap)
                tags_html = "".join([f"<span class='tag-pill'>#{t}</span>" for t in obs['tags']])
                time_str = datetime.strptime(obs['created_date'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M • %d %b') if obs.get('created_date') else ""
                
                st.markdown(f"""
                    <div class="obs-text">{obs['observation_text']}</div>
                    <div class="obs-footer">
                        {tags_html}
                        <span style="margin-left:8px;">{time_str}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Spacer
                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
