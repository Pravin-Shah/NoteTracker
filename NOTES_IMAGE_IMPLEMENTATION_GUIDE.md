# Implementation Guide: Adding Image Support to Notes

This guide provides the exact code changes needed to add multiple image support to the Notes feature.

## Step 1: Update Imports in `apps/general/pages/notes.py`

**Location:** Top of file, after existing imports

```python
# Add these new imports
from streamlit_paste_button import paste_image_button
import io
import hashlib
```

## Step 2: Add Helper Functions

**Location:** After imports, before `init_session()` function

```python
def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk and return path."""
    import shutil
    upload_dir = "data/uploads/notes"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def save_pasted_image(image_data):
    """Save PIL image to disk and return path."""
    upload_dir = "data/uploads/notes"
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
```

## Step 3: Update `init_session()` Function

**Location:** Replace existing `init_session()` function (lines 26-33)

```python
def init_session():
    """Initialize session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1
    if 'editing_note_id' not in st.session_state:
        st.session_state.editing_note_id = None
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    # NEW: Image support
    if 'pasted_images' not in st.session_state:
        st.session_state.pasted_images = []
    if 'processed_pastes' not in st.session_state:
        st.session_state.processed_pastes = []
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
```

## Step 4: Update `render_create_form()` Function

**Location:** Replace existing function (lines 36-93)

```python
def render_create_form():
    """Render note creation form."""
    user_id = st.session_state.user_id

    st.subheader("Create New Note")

    col1, col2 = st.columns([2, 1])

    with col1:
        title = st.text_input("Title", key="new_note_title", label_visibility="collapsed", placeholder="Note title")

    with col2:
        importance = st.select_slider("Importance", options=[1, 2, 3, 4, 5], value=3, key="new_note_importance")

    category = st.selectbox("Category", options=["Personal", "Work", "Ideas", "Reference", "Other"],
                           key="new_note_category", label_visibility="collapsed")

    content = st.text_area("Content", height=120, key="new_note_content", placeholder="Note content")

    tags_input = st.text_input("Tags (comma-separated)", key="new_note_tags", label_visibility="collapsed")

    # NEW: Image upload section
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

    # Handle pasted image
    if paste_result.image_data is not None:
        saved_path = save_pasted_image(paste_result.image_data)
        if saved_path:
            st.session_state.pasted_images.append(saved_path)

    # Show image count
    if st.session_state.pasted_images:
        st.caption(f"📎 {len(st.session_state.pasted_images)} pasted image(s)")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Note", use_container_width=True):
            if not title.strip():
                render_error_message("Title is required")
                return

            try:
                note_id = create_note(user_id, {
                    'title': title,
                    'content': content,
                    'category': category.lower(),
                    'importance': importance
                })

                # Add tags
                if tags_input.strip():
                    tags = [t.strip().lower() for t in tags_input.split(',')]
                    for tag in tags:
                        if tag:
                            add_note_tag(note_id, tag)

                # NEW: Add uploaded images
                if uploaded_files:
                    from apps.general.utils.note_ops import add_note_attachment
                    for f in uploaded_files:
                        file_path = save_uploaded_file(f)
                        add_note_attachment(note_id, file_path, file_type='image')

                # NEW: Add pasted images
                if st.session_state.pasted_images:
                    from apps.general.utils.note_ops import add_note_attachment
                    for img_path in st.session_state.pasted_images:
                        add_note_attachment(note_id, img_path, file_type='image')

                render_success_message("Note created successfully!")
                
                # Clear image state
                st.session_state.pasted_images = []
                st.session_state.processed_pastes = []
                st.session_state.show_create_form = False
                st.session_state.search_query = ""
                st.session_state.form_key += 1
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to create note: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.pasted_images = []
            st.session_state.processed_pastes = []
            st.session_state.show_create_form = False
            st.session_state.form_key += 1
            st.rerun()
```

## Step 5: Update `render_note_card()` Function

**Location:** Replace existing function (lines 96-141)

```python
def render_note_card(note: Dict):
    """Render individual note card with actions."""
    user_id = st.session_state.user_id

    # NEW: Show thumbnail if images exist
    if note.get('attachments') and len(note['attachments']) > 0:
        col_img, col_content = st.columns([1, 3])
        
        with col_img:
            # Show first image as thumbnail
            first_img = note['attachments'][0]
            st.image(first_img['file_path'], width=120)
            
            # Show image count if multiple
            if len(note['attachments']) > 1:
                st.caption(f"📷 +{len(note['attachments']) - 1} more")
                if st.button("🖼️ Gallery", key=f"gallery_{note['id']}", help="View all images"):
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
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            importance_emoji = "⭐" * note.get('importance', 3)
            st.write(f"**{note['title']}** {importance_emoji}")
            if note.get('content'):
                preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
                st.caption(preview)

        # Action buttons
        with col2:
            if st.button("✏️", key=f"edit_{note['id']}", help="Edit"):
                st.session_state.editing_note_id = note['id']
                st.rerun()
            if st.button("📌" if not note.get('pinned') else "📍", key=f"pin_{note['id']}", help="Toggle pin"):
                try:
                    if note.get('pinned'):
                        unpin_note(user_id, note['id'])
                    else:
                        pin_note(user_id, note['id'])
                    render_success_message("Note updated")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

        with col3:
            if st.button("🗑️", key=f"delete_{note['id']}", help="Delete"):
                try:
                    delete_note(user_id, note['id'])
                    render_success_message("Note deleted")
                    st.rerun()
                except Exception as e:
                    render_error_message(str(e))

    # Tags and metadata
    if note.get('tags'):
        tags_display = " ".join([f"🏷️ {tag}" for tag in note['tags']])
        st.caption(tags_display)

    st.divider()
```

## Step 6: Update `render_edit_form()` Function

**Location:** Replace existing function (lines 144-185)

```python
def render_edit_form(note: Dict):
    """Render note edit form."""
    user_id = st.session_state.user_id

    st.subheader(f"Edit Note: {note['title']}")

    # NEW: Display existing attachments
    if note.get('attachments') and len(note['attachments']) > 0:
        st.write("**Existing Images:**")
        cols = st.columns(4)
        for idx, attachment in enumerate(note['attachments']):
            with cols[idx % 4]:
                st.image(attachment['file_path'], width=100)
                if st.button("🗑️", key=f"del_att_{attachment['id']}", help="Remove"):
                    try:
                        from apps.general.utils.note_ops import remove_note_attachment
                        remove_note_attachment(attachment['id'])
                        render_success_message("Image removed")
                        st.rerun()
                    except Exception as e:
                        render_error_message(f"Failed to remove image: {str(e)}")
        st.divider()

    title = st.text_input("Title", value=note['title'], key="edit_note_title")
    importance = st.select_slider("Importance", options=[1, 2, 3, 4, 5],
                                 value=note.get('importance', 3), key="edit_note_importance")
    category = st.selectbox("Category", options=["Personal", "Work", "Ideas", "Reference", "Other"],
                           index=0, key="edit_note_category")
    content = st.text_area("Content", value=note.get('content', ''), height=120, key="edit_note_content")

    # NEW: Add more images
    st.write("**Add More Images:**")
    col_paste, col_upload = st.columns([1, 2], gap="small")
    with col_paste:
        paste_result = paste_image_button(
            label="📋 Paste Image",
            background_color="#4CAF50",
            hover_background_color="#45a049",
            key=f"edit_paste_btn_{note['id']}"
        )
    with col_upload:
        uploaded_files = st.file_uploader(
            "Upload Images", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg'], 
            label_visibility="collapsed", 
            key=f"edit_files_{note['id']}"
        )

    # Handle pasted image
    if paste_result.image_data is not None:
        saved_path = save_pasted_image(paste_result.image_data)
        if saved_path:
            st.session_state.pasted_images.append(saved_path)

    if st.session_state.pasted_images:
        st.caption(f"📎 {len(st.session_state.pasted_images)} new image(s) to add")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes", use_container_width=True):
            if not title.strip():
                render_error_message("Title is required")
                return

            try:
                update_note(user_id, note['id'], {
                    'title': title,
                    'content': content,
                    'category': category.lower(),
                    'importance': importance
                })

                # NEW: Add new uploaded images
                if uploaded_files:
                    from apps.general.utils.note_ops import add_note_attachment
                    for f in uploaded_files:
                        file_path = save_uploaded_file(f)
                        add_note_attachment(note['id'], file_path, file_type='image')

                # NEW: Add new pasted images
                if st.session_state.pasted_images:
                    from apps.general.utils.note_ops import add_note_attachment
                    for img_path in st.session_state.pasted_images:
                        add_note_attachment(note['id'], img_path, file_type='image')

                render_success_message("Note updated successfully!")
                st.session_state.pasted_images = []
                st.session_state.processed_pastes = []
                st.session_state.editing_note_id = None
                st.rerun()

            except ValidationError as e:
                render_error_message(f"Validation error: {str(e)}")
            except Exception as e:
                render_error_message(f"Failed to update note: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.pasted_images = []
            st.session_state.processed_pastes = []
            st.session_state.editing_note_id = None
            st.rerun()

    st.divider()
```

## Step 7: Update `search_notes()` in `apps/general/utils/note_ops.py`

**Location:** In `apps/general/utils/note_ops.py`, update the `search_notes()` function (lines 132-215)

**Find this section (around line 206-213):**
```python
    else:
        # Add all tags
        for note in notes:
            note_tags = execute_query(
                "SELECT tag FROM gen_note_tags WHERE note_id = ?",
                (note['id'],),
                db_path
            )
            note['tags'] = [t['tag'] for t in note_tags]

    return notes
```

**Replace with:**
```python
    else:
        # Add all tags
        for note in notes:
            note_tags = execute_query(
                "SELECT tag FROM gen_note_tags WHERE note_id = ?",
                (note['id'],),
                db_path
            )
            note['tags'] = [t['tag'] for t in note_tags]
            
            # NEW: Load attachments for thumbnail display
            attachments = execute_query(
                "SELECT id, file_path, file_type FROM gen_note_attachments WHERE note_id = ?",
                (note['id'],),
                db_path
            )
            note['attachments'] = [dict(a) for a in attachments]

    return notes
```

## Step 8: Create Upload Directory

Run this command in terminal:

```bash
mkdir -p data/uploads/notes
```

Or on Windows:
```cmd
mkdir data\uploads\notes
```

## Testing Checklist

After implementing all changes, test the following:

### Create Note
- [ ] Can paste image using Ctrl+V
- [ ] Can upload multiple images
- [ ] Image counter shows correct count
- [ ] Images are saved to database
- [ ] Images are saved to file system

### View Notes List
- [ ] Notes with images show thumbnail
- [ ] Image count is displayed correctly
- [ ] Gallery button appears for multiple images
- [ ] Gallery dialog opens and shows images
- [ ] Can navigate between images in gallery

### Edit Note
- [ ] Existing images are displayed
- [ ] Can remove existing images
- [ ] Can add new images (paste/upload)
- [ ] Changes are saved correctly

### Edge Cases
- [ ] Pasting same image twice doesn't duplicate
- [ ] Deleting note removes attachments (CASCADE)
- [ ] Notes without images still display correctly
- [ ] Large images are handled properly

## Common Issues and Solutions

### Issue 1: Images not showing
**Solution:** Check file paths are correct and files exist in `data/uploads/notes/`

### Issue 2: Paste button not working
**Solution:** Ensure `streamlit-paste-button` is installed: `pip install streamlit-paste-button`

### Issue 3: Duplicate images on paste
**Solution:** Check that `processed_pastes` session state is being managed correctly

### Issue 4: Images not loading in list view
**Solution:** Verify `search_notes()` is loading attachments (Step 7)

## Performance Considerations

1. **Lazy Loading**: Consider loading attachments only when needed for large note lists
2. **Image Optimization**: Consider resizing images before saving
3. **Caching**: Use `@st.cache_data` for image loading if needed
4. **Pagination**: Implement pagination for notes list if you have many notes

## Future Enhancements

1. **Image Captions**: Add caption field to attachments
2. **Image Reordering**: Allow drag-and-drop to reorder images
3. **Image Compression**: Automatically compress large images
4. **Image Preview**: Show larger preview on hover
5. **Bulk Operations**: Select and delete multiple images at once
