# NoteTracker - Multiple Images Support Summary

## Overview
This document explains the implementation of multiple image support in the NoteTracker project, specifically for the General App Notes feature. The implementation allows users to paste and upload multiple images when creating or viewing notes, with thumbnail display in the notes list view.

## Current Implementation Status

### ✅ What's Already Implemented

#### 1. **Database Schema** (in `core/db.py`)
The database already has full support for note attachments:

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

**Key Features:**
- Supports multiple attachments per note (one-to-many relationship)
- Stores file path and file type
- Automatic deletion when note is deleted (CASCADE)
- Tracks upload date

#### 2. **Backend Operations** (in `apps/general/utils/note_ops.py`)

The following functions are already implemented:

**a) `get_note()` - Lines 54-87**
```python
def get_note(user_id: int, note_id: int, db_path: str = None) -> Optional[Dict]:
    # ... retrieves note
    # Gets attachments
    attachments = execute_query(
        "SELECT id, file_path, file_type FROM gen_note_attachments WHERE note_id = ?",
        (note_id,),
        db_path
    )
    note['attachments'] = [dict(a) for a in attachments]
    return dict(note)
```
- Automatically loads all attachments when fetching a note
- Returns attachments as a list in the note dictionary

**b) `add_note_attachment()` - Lines 357-376**
```python
def add_note_attachment(note_id: int, file_path: str, file_type: str = None, db_path: str = None) -> int:
    attachment_id = create_record('gen_note_attachments', {
        'note_id': note_id,
        'file_path': file_path,
        'file_type': file_type
    }, db_path)
    logger.info(f"Attachment added to note {note_id}: {file_path}")
    return attachment_id
```
- Adds a single attachment to a note
- Returns the attachment ID

**c) `remove_note_attachment()` - Lines 379-393**
```python
def remove_note_attachment(attachment_id: int, db_path: str = None) -> None:
    execute_update(
        "DELETE FROM gen_note_attachments WHERE id = ?",
        (attachment_id,),
        db_path
    )
```
- Removes an attachment by ID

**d) `export_notes()` - Lines 514-539**
- Already includes attachments when exporting notes

### ❌ What's NOT Yet Implemented

#### 1. **UI for Image Upload/Paste** (in `apps/general/pages/notes.py`)
The notes page currently does NOT have:
- Image paste functionality (using `streamlit_paste_button`)
- File uploader for images
- Session state management for pasted images
- Image preview in create/edit forms

#### 2. **Image Display in Notes List**
The `render_note_card()` function (lines 96-141) does NOT:
- Show thumbnail of the first image
- Display image count indicator
- Handle image gallery/preview

#### 3. **Image Display in Note Details**
The `render_edit_form()` function (lines 144-185) does NOT:
- Show existing attachments
- Allow adding new images
- Allow removing images

## Reference Implementation: Observations Page

The **Observations page** (`pages/observations.py`) has a complete implementation that can be used as a reference:

### Key Features Implemented in Observations:

#### 1. **Image Paste Support** (Lines 18-54)
```python
from streamlit_paste_button import paste_image_button

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
```

**Features:**
- Uses `streamlit_paste_button` library
- Prevents duplicate pastes using MD5 hashing
- Saves images with timestamp-based filenames
- Stores in `data/uploads/observations/` directory

#### 2. **File Upload Support** (Line 210)
```python
uploaded_files = st.file_uploader(
    "Upload", 
    accept_multiple_files=True, 
    type=['png', 'jpg', 'jpeg'], 
    label_visibility="collapsed", 
    key=f"obs_files_{st.session_state.form_key}"
)
```

#### 3. **Session State Management** (Lines 99-100, 212-217)
```python
if 'pasted_images' not in st.session_state:
    st.session_state.pasted_images = []

if paste_result.image_data is not None:
    saved_path = save_pasted_image(paste_result.image_data)
    if saved_path: 
        st.session_state.pasted_images.append(saved_path)

if st.session_state.pasted_images:
    st.caption(f"📎 {len(st.session_state.pasted_images)} images")
```

#### 4. **Saving Images to Database** (Lines 229-232)
```python
if uploaded_files:
    for f in uploaded_files: 
        add_observation_screenshot(obs_id, save_uploaded_file(f))
if st.session_state.pasted_images:
    for p in st.session_state.pasted_images: 
        add_observation_screenshot(obs_id, p)
```

#### 5. **Image Gallery Dialog** (Lines 56-93)
```python
@st.dialog("Image Gallery", width="large")
def show_image_dialog(images, start_index):
    """Dialog to show images in full size with navigation."""
    if "gallery_index" not in st.session_state:
        st.session_state.gallery_index = start_index

    current_idx = st.session_state.gallery_index % len(images)
    current_img = images[current_idx]
    current_path = current_img['file_path'] if isinstance(current_img, dict) else current_img

    st.image(current_path, use_container_width=True)
    
    # Navigation buttons for previous/next
    # ...
```

#### 6. **Thumbnail Display in List** (Lines 271-282)
```python
if obs.get('screenshots'):
    main_img = obs['screenshots'][0]
    st.image(main_img['file_path'], width=550)
    
    if len(obs['screenshots']) > 1:
        if st.button(f"+ {len(obs['screenshots'])-1} more (Open Gallery)", key=f"vg_{obs['id']}"):
            st.session_state.gallery_index = 0
            show_image_dialog(obs['screenshots'], 0)
```

**Features:**
- Shows first image as thumbnail
- Displays count of additional images
- Opens gallery dialog to view all images
- Navigation between images in gallery

## Implementation Roadmap for Notes

To add the same functionality to Notes, you need to:

### Phase 1: Update `apps/general/pages/notes.py`

#### 1.1 Add Required Imports
```python
from streamlit_paste_button import paste_image_button
import io
import hashlib
```

#### 1.2 Add Helper Functions
- `save_uploaded_file()` - Save uploaded files to disk
- `save_pasted_image()` - Save pasted images with duplicate prevention
- `show_image_dialog()` - Image gallery dialog

#### 1.3 Update `init_session()`
Add image-related session state:
```python
if 'pasted_images' not in st.session_state:
    st.session_state.pasted_images = []
if 'processed_pastes' not in st.session_state:
    st.session_state.processed_pastes = []
```

#### 1.4 Update `render_create_form()`
Add:
- Paste button using `paste_image_button`
- File uploader for multiple images
- Image counter display
- Save pasted/uploaded images to database after note creation

#### 1.5 Update `render_note_card()`
Add:
- Thumbnail display of first image
- Image count indicator
- Gallery button if multiple images

#### 1.6 Update `render_edit_form()`
Add:
- Display existing attachments
- Option to add new images
- Option to remove images

### Phase 2: Update `apps/general/utils/note_ops.py`

#### 2.1 Update `search_notes()` (Lines 132-215)
Currently, `search_notes()` does NOT load attachments. You need to add:

```python
# After line 213, add:
for note in notes:
    # ... existing tag loading code ...
    
    # Load attachments for thumbnail display
    attachments = execute_query(
        "SELECT id, file_path, file_type FROM gen_note_attachments WHERE note_id = ?",
        (note['id'],),
        db_path
    )
    note['attachments'] = [dict(a) for a in attachments]
```

This ensures the notes list has access to attachment data for thumbnail display.

## File Structure

```
NoteTracker/
├── core/
│   ├── db.py                          # ✅ Database schema with gen_note_attachments
│   └── ...
├── apps/
│   └── general/
│       ├── pages/
│       │   └── notes.py               # ❌ Needs image UI implementation
│       └── utils/
│           └── note_ops.py            # ✅ Backend functions ready
├── pages/
│   └── observations.py                # ✅ Reference implementation
└── data/
    └── uploads/
        ├── observations/              # ✅ Existing
        └── notes/                     # ❌ Need to create
```

## Dependencies

The project already has the required dependency:
- `streamlit-paste-button` - For clipboard image paste functionality

## Summary

### What Works:
1. ✅ Database schema supports multiple attachments per note
2. ✅ Backend CRUD operations for attachments are complete
3. ✅ Reference implementation exists in Observations page
4. ✅ Image paste library is already installed

### What Needs Implementation:
1. ❌ UI for pasting/uploading images in notes create form
2. ❌ UI for displaying images in notes list (thumbnail)
3. ❌ UI for managing images in notes edit form
4. ❌ Image gallery dialog for notes
5. ❌ Update `search_notes()` to load attachments

### Estimated Effort:
- **Backend**: ~10% (mostly done, just need to update `search_notes()`)
- **Frontend**: ~90% (need to implement all UI components)

The implementation can largely copy the patterns from `observations.py` with minor adjustments for the notes context.
