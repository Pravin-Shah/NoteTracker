# Quick Reference: Notes vs Observations Image Support

## Side-by-Side Comparison

### Database Tables

| Observations | Notes |
|-------------|-------|
| `tv_observations` | `gen_notes` |
| `tv_observation_screenshots` | `gen_note_attachments` |
| `tv_observation_tags` | `gen_note_tags` |

### Database Schema

#### Observations Screenshots
```sql
CREATE TABLE IF NOT EXISTS tv_observation_screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    caption TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES tv_observations(id) ON DELETE CASCADE
);
```

#### Notes Attachments
```sql
CREATE TABLE IF NOT EXISTS gen_note_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES gen_notes(id) ON DELETE CASCADE
);
```

**Key Difference:** Notes use `file_type` instead of `caption`

### Backend Functions

#### Observations (`apps/tradevault/utils/observation_ops.py`)
```python
def add_observation_screenshot(observation_id: int, file_path: str, caption: str = "") -> None:
    create_record('tv_observation_screenshots', {
        'observation_id': observation_id,
        'file_path': file_path,
        'caption': caption
    })
```

#### Notes (`apps/general/utils/note_ops.py`)
```python
def add_note_attachment(note_id: int, file_path: str, file_type: str = None, db_path: str = None) -> int:
    attachment_id = create_record('gen_note_attachments', {
        'note_id': note_id,
        'file_path': file_path,
        'file_type': file_type
    }, db_path)
    return attachment_id
```

**Key Difference:** Notes return attachment_id and support db_path parameter

### File Paths

| Feature | Observations | Notes |
|---------|-------------|-------|
| **Upload Directory** | `data/uploads/observations/` | `data/uploads/notes/` |
| **Pasted Files** | `pasted_{timestamp}.png` | `pasted_{timestamp}.png` |
| **Uploaded Files** | `{timestamp}_{filename}` | `{timestamp}_{filename}` |

### Frontend Implementation

#### Import Statements

**Observations** (`pages/observations.py`):
```python
from streamlit_paste_button import paste_image_button
import io
import hashlib
from apps.tradevault.utils.observation_ops import (
    create_observation, search_observations, add_observation_tag, 
    add_observation_screenshot, delete_observation
)
```

**Notes** (`apps/general/pages/notes.py`):
```python
from streamlit_paste_button import paste_image_button
import io
import hashlib
from apps.general.utils.note_ops import (
    create_note, get_note, update_note, delete_note, search_notes,
    pin_note, unpin_note, archive_note, unarchive_note,
    get_note_categories, get_note_tags, add_note_tag, remove_note_tag,
    add_note_attachment, remove_note_attachment  # NEW
)
```

#### Save Functions

**Both use identical implementations:**

```python
def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk and return path."""
    upload_dir = "data/uploads/[observations|notes]"  # Only difference
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def save_pasted_image(image_data):
    """Save PIL image to disk and return path."""
    upload_dir = "data/uploads/[observations|notes]"  # Only difference
    os.makedirs(upload_dir, exist_ok=True)
    
    # Hash content to prevent duplicates
    img_byte_arr = io.BytesIO()
    image_data.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    img_hash = hashlib.md5(img_bytes).hexdigest()
    
    if img_hash in st.session_state.get('processed_pastes', []):
        return None
        
    if 'processed_pastes' not in st.session_state:
        st.session_state.processed_pastes = []
    st.session_state.processed_pastes.append(img_hash)
    
    file_path = os.path.join(upload_dir, f"pasted_{datetime.now().timestamp()}.png")
    image_data.save(file_path, "PNG")
    return file_path
```

#### Image Gallery Dialog

**Both use identical implementation:**

```python
@st.dialog("Image Gallery", width="large")
def show_image_dialog(images, start_index):
    if "gallery_index" not in st.session_state:
        st.session_state.gallery_index = start_index

    current_idx = st.session_state.gallery_index % len(images)
    current_img = images[current_idx]
    current_path = current_img['file_path'] if isinstance(current_img, dict) else current_img

    st.image(current_path, use_container_width=True)
    st.write(f"Image {current_idx + 1} of {len(images)}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Previous", use_container_width=True):
            st.session_state.gallery_index = (current_idx - 1) % len(images)
            st.rerun()
    with col3:
        if st.button("Next ➡️", use_container_width=True):
            st.session_state.gallery_index = (current_idx + 1) % len(images)
            st.rerun()
```

### Create Form Comparison

#### Observations - Image Upload Section
```python
c_p, c_u = st.columns([1, 2], gap="small")
with c_p:
    paste_result = paste_image_button(
        label="📋 Paste",
        background_color="#4CAF50",
        hover_background_color="#45a049",
        key=f"paste_btn_{st.session_state.form_key}"
    )
with c_u:
    uploaded_files = st.file_uploader(
        "Upload", 
        accept_multiple_files=True, 
        type=['png', 'jpg', 'jpeg'], 
        label_visibility="collapsed", 
        key=f"obs_files_{st.session_state.form_key}"
    )

if paste_result.image_data is not None:
    saved_path = save_pasted_image(paste_result.image_data)
    if saved_path: 
        st.session_state.pasted_images.append(saved_path)

if st.session_state.pasted_images:
    st.caption(f"📎 {len(st.session_state.pasted_images)} images")
```

#### Notes - Image Upload Section (TO IMPLEMENT)
```python
col_paste, col_upload = st.columns([1, 2], gap="small")
with col_paste:
    paste_result = paste_image_button(
        label="📋 Paste Image",
        background_color="#4CAF50",
        hover_background_color="#45a049",
        key=f"paste_btn_{st.session_state.form_key}"
    )
with col_upload:
    uploaded_files = st.file_uploader(
        "Upload Images", 
        accept_multiple_files=True, 
        type=['png', 'jpg', 'jpeg'], 
        label_visibility="collapsed", 
        key=f"note_files_{st.session_state.form_key}"
    )

if paste_result.image_data is not None:
    saved_path = save_pasted_image(paste_result.image_data)
    if saved_path:
        st.session_state.pasted_images.append(saved_path)

if st.session_state.pasted_images:
    st.caption(f"📎 {len(st.session_state.pasted_images)} pasted image(s)")
```

**Differences:** Minor label changes only

### Save Operation Comparison

#### Observations - Saving Images
```python
if st.button("💾 Save", use_container_width=True, type="primary"):
    try:
        obs_id = create_observation(st.session_state.user_id, {
            'stock_name': stock_name, 
            'observation_text': observation_text
        })
        
        if tags_input:
            for tag in [t.strip() for t in tags_input.split(',') if t.strip()]: 
                add_observation_tag(obs_id, tag)
        
        if uploaded_files:
            for f in uploaded_files: 
                add_observation_screenshot(obs_id, save_uploaded_file(f))
        
        if st.session_state.pasted_images:
            for p in st.session_state.pasted_images: 
                add_observation_screenshot(obs_id, p)
        
        st.success("Saved!")
        st.session_state.pasted_images = []
        st.session_state.processed_pastes = []
        st.session_state.reset_form = True
        st.rerun()
    except Exception as e: 
        st.error(f"Error: {e}")
```

#### Notes - Saving Images (TO IMPLEMENT)
```python
if st.button("💾 Save Note", use_container_width=True):
    try:
        note_id = create_note(user_id, {
            'title': title,
            'content': content,
            'category': category.lower(),
            'importance': importance
        })

        if tags_input.strip():
            tags = [t.strip().lower() for t in tags_input.split(',')]
            for tag in tags:
                if tag:
                    add_note_tag(note_id, tag)

        if uploaded_files:
            for f in uploaded_files:
                file_path = save_uploaded_file(f)
                add_note_attachment(note_id, file_path, file_type='image')

        if st.session_state.pasted_images:
            for img_path in st.session_state.pasted_images:
                add_note_attachment(note_id, img_path, file_type='image')

        render_success_message("Note created successfully!")
        st.session_state.pasted_images = []
        st.session_state.processed_pastes = []
        st.session_state.show_create_form = False
        st.session_state.form_key += 1
        st.rerun()
    except Exception as e:
        render_error_message(f"Failed to create note: {str(e)}")
```

**Key Differences:**
- Notes use `add_note_attachment()` instead of `add_observation_screenshot()`
- Notes pass `file_type='image'` parameter
- Notes use `render_success_message()` instead of `st.success()`
- Notes increment `form_key` for form reset

### Display in List View

#### Observations - Card Display
```python
for obs in observations:
    with st.container():
        st.markdown(f'<div class="obs-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown(f'<div class="obs-header">{obs["stock_name"]}</div>', unsafe_allow_html=True)
        
        # Image (if exists)
        if obs.get('screenshots'):
            st.markdown('<div style="margin-top: -24px;"></div>', unsafe_allow_html=True)
            main_img = obs['screenshots'][0]
            st.image(main_img['file_path'], width=550)
            
            if len(obs['screenshots']) > 1:
                if st.button(f"+ {len(obs['screenshots'])-1} more (Open Gallery)", key=f"vg_{obs['id']}"):
                    st.session_state.gallery_index = 0
                    show_image_dialog(obs['screenshots'], 0)
        
        # Text content
        st.markdown(f'<div class="obs-text">{obs['observation_text']}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
```

#### Notes - Card Display (TO IMPLEMENT)
```python
for note in notes:
    # Show thumbnail if images exist
    if note.get('attachments') and len(note['attachments']) > 0:
        col_img, col_content = st.columns([1, 3])
        
        with col_img:
            first_img = note['attachments'][0]
            st.image(first_img['file_path'], width=120)
            
            if len(note['attachments']) > 1:
                st.caption(f"📷 +{len(note['attachments']) - 1} more")
                if st.button("🖼️ Gallery", key=f"gallery_{note['id']}"):
                    st.session_state.gallery_index = 0
                    show_image_dialog(note['attachments'], 0)
        
        with col_content:
            importance_emoji = "⭐" * note.get('importance', 3)
            st.write(f"**{note['title']}** {importance_emoji}")
            if note.get('content'):
                preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
                st.caption(preview)
    else:
        # Original layout without images
        # ... existing code ...
```

**Key Differences:**
- Observations use full-width image (550px) in card
- Notes use thumbnail (120px) in sidebar layout
- Observations use custom CSS styling
- Notes use standard Streamlit columns

## Summary of Changes Needed

### Files to Modify

1. **`apps/general/pages/notes.py`** - Major changes
   - Add imports
   - Add helper functions
   - Update all render functions
   
2. **`apps/general/utils/note_ops.py`** - Minor change
   - Update `search_notes()` to load attachments

3. **File System**
   - Create `data/uploads/notes/` directory

### Code Reuse

| Component | Can Reuse from Observations? | Notes |
|-----------|------------------------------|-------|
| `save_uploaded_file()` | ✅ Yes (change path) | Copy with path change |
| `save_pasted_image()` | ✅ Yes (change path) | Copy with path change |
| `show_image_dialog()` | ✅ Yes (identical) | Copy as-is |
| Paste button code | ✅ Yes (minor labels) | Copy with label changes |
| File uploader code | ✅ Yes (minor labels) | Copy with label changes |
| Save logic | ⚠️ Partial | Adapt function names |
| Display logic | ⚠️ Partial | Different layout approach |

### Estimated Lines of Code

- **New code:** ~150 lines
- **Modified code:** ~100 lines
- **Total impact:** ~250 lines across 2 files

### Testing Requirements

- [ ] Create note with pasted images
- [ ] Create note with uploaded images
- [ ] Create note with both pasted and uploaded
- [ ] View notes list with thumbnails
- [ ] Open image gallery
- [ ] Navigate in gallery
- [ ] Edit note and add images
- [ ] Edit note and remove images
- [ ] Delete note (verify cascade delete)
- [ ] Search notes with images

## Quick Copy-Paste Checklist

For rapid implementation, copy these sections from `observations.py`:

1. ✅ Lines 18-54: `save_pasted_image()` function
2. ✅ Lines 22-31: `save_uploaded_file()` function  
3. ✅ Lines 56-93: `show_image_dialog()` function
4. ✅ Lines 99-100: Session state initialization
5. ✅ Lines 202-217: Paste/upload UI components
6. ⚠️ Lines 229-232: Save logic (adapt function names)
7. ⚠️ Lines 271-282: Image display (adapt for thumbnail layout)

Remember to:
- Change `data/uploads/observations` → `data/uploads/notes`
- Change `add_observation_screenshot()` → `add_note_attachment()`
- Change `obs` → `note` variable names
- Add `file_type='image'` parameter
