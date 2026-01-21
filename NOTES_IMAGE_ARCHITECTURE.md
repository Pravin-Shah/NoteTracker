# Notes Image Support - Architecture Diagram

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                            │
│                     (apps/general/pages/notes.py)                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌──────────────────┐  ┌──────────┐  ┌─────────────┐
        │  Create Form     │  │ List View│  │  Edit Form  │
        │  ❌ TODO         │  │ ❌ TODO  │  │  ❌ TODO    │
        └──────────────────┘  └──────────┘  └─────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        BUSINESS LOGIC LAYER                              │
│                   (apps/general/utils/note_ops.py)                       │
│                                                                           │
│  ✅ create_note()              ✅ add_note_attachment()                  │
│  ✅ get_note()                 ✅ remove_note_attachment()               │
│  ✅ update_note()              ⚠️  search_notes() - needs attachment load│
│  ✅ delete_note()                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATABASE LAYER                                  │
│                           (core/db.py)                                   │
│                                                                           │
│  ┌─────────────────┐              ┌──────────────────────────┐          │
│  │   gen_notes     │              │  gen_note_attachments    │          │
│  ├─────────────────┤              ├──────────────────────────┤          │
│  │ id (PK)         │              │ id (PK)                  │          │
│  │ user_id         │◄─────────────│ note_id (FK)             │          │
│  │ title           │              │ file_path                │          │
│  │ content         │              │ file_type                │          │
│  │ category        │              │ upload_date              │          │
│  │ importance      │              └──────────────────────────┘          │
│  │ created_date    │                                                     │
│  │ last_updated    │              ┌──────────────────────────┐          │
│  │ archived        │              │   gen_note_tags          │          │
│  │ pinned          │◄─────────────│ note_id (FK)             │          │
│  └─────────────────┘              │ tag                      │          │
│                                    └──────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          FILE SYSTEM                                     │
│                                                                           │
│  data/uploads/notes/                                                     │
│  ├── pasted_1234567890.123.png                                          │
│  ├── pasted_1234567891.456.png                                          │
│  └── 1234567892.789_screenshot.png                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### 1. Creating a Note with Images

```
User Action                  Frontend                Backend              Database
───────────                  ────────                ───────              ────────
                                                                          
1. Type note text       ──►  notes.py                                    
                             render_create_form()                        
                                                                          
2. Paste image (Ctrl+V) ──►  paste_image_button()                        
                             │                                            
                             ├─► save_pasted_image()                     
                             │   └─► Hash image                          
                             │   └─► Save to disk   ──────────────────►  File System
                             │   └─► Add to session state                
                             │                                            
3. Upload file          ──►  file_uploader()                             
                             │                                            
                             └─► save_uploaded_file()                    
                                 └─► Save to disk   ──────────────────►  File System
                                 └─► Add to session state                
                                                                          
4. Click "Save"         ──►  create_note()      ──►  note_ops.py        
                                                     create_note()   ──►  gen_notes
                                                     │                    (INSERT)
                                                     │                    
                                                     ├─► add_note_tag()   gen_note_tags
                                                     │                    (INSERT)
                                                     │                    
                                                     └─► add_note_        gen_note_
                                                         attachment()     attachments
                                                         (for each img)   (INSERT)
                                                                          
5. Clear session state  ──►  st.session_state.pasted_images = []         
                             st.rerun()                                   
```

### 2. Viewing Notes List with Thumbnails

```
User Action                  Frontend                Backend              Database
───────────                  ────────                ───────              ────────
                                                                          
1. Open notes page      ──►  notes.py                                    
                             main()                                       
                             │                                            
2. Search/Filter        ──►  search_notes()     ──►  note_ops.py        
                                                     search_notes()   ──►  SELECT from
                                                     │                    gen_notes
                                                     │                    
                                                     ├─► Load tags    ──►  gen_note_tags
                                                     │                    
                                                     └─► Load         ──►  gen_note_
                                                         attachments      attachments
                                                                          
3. Display cards        ──►  render_note_card()                          
                             │                                            
                             ├─► Show title, content                     
                             │                                            
                             └─► IF attachments exist:                   
                                 ├─► Show first image thumbnail          
                                 │   st.image(note['attachments'][0])    
                                 │                                        
                                 └─► Show "+ X more" button              
                                     IF len(attachments) > 1              
```

### 3. Viewing Note with Image Gallery

```
User Action                  Frontend                Backend              Database
───────────                  ────────                ───────              ────────
                                                                          
1. Click note card      ──►  get_note()         ──►  note_ops.py        
                                                     get_note()       ──►  SELECT from
                                                     │                    gen_notes
                                                     │                    
                                                     ├─► Load tags    ──►  gen_note_tags
                                                     │                    
                                                     └─► Load         ──►  gen_note_
                                                         attachments      attachments
                                                                          
2. Click "View Gallery" ──►  show_image_dialog()                         
                             │                                            
                             ├─► Display current image                   
                             │   st.image(images[index])                 
                             │                                            
                             └─► Navigation buttons                      
                                 ├─► Previous                            
                                 └─► Next                                
```

## Session State Management

```python
st.session_state = {
    'user_id': 1,                           # Current user
    'editing_note_id': None,                # Note being edited
    'show_create_form': False,              # Toggle create form
    'pasted_images': [],                    # ❌ TODO: Pasted image paths
    'processed_pastes': [],                 # ❌ TODO: MD5 hashes to prevent duplicates
    'gallery_index': 0,                     # ❌ TODO: Current image in gallery
    'form_key': 0,                          # ❌ TODO: Force form reset
}
```

## File Organization Pattern

### Observations (Reference Implementation)
```
data/uploads/observations/
├── pasted_1737363600.123.png       # Pasted images
├── pasted_1737363601.456.png
└── 1737363602.789_screenshot.jpg   # Uploaded files
```

### Notes (To Be Implemented)
```
data/uploads/notes/
├── pasted_1737363700.123.png       # Pasted images
├── pasted_1737363701.456.png
└── 1737363702.789_document.jpg     # Uploaded files
```

## Key Differences: Observations vs Notes

| Feature | Observations | Notes |
|---------|-------------|-------|
| **Table Name** | `tv_observations` | `gen_notes` |
| **Attachment Table** | `tv_observation_screenshots` | `gen_note_attachments` |
| **Upload Directory** | `data/uploads/observations/` | `data/uploads/notes/` |
| **Main Content Field** | `observation_text` | `content` |
| **Additional Fields** | `stock_name` | `title`, `category`, `importance`, `pinned` |
| **UI Style** | Telegram-like chat cards | Compact note cards |
| **Image Display** | First image shown at full width (550px) | ❌ TODO: Thumbnail in card |
| **Backend Status** | ✅ Complete | ✅ Complete (attachments ready) |
| **Frontend Status** | ✅ Complete | ❌ TODO |

## Implementation Checklist

### Frontend (notes.py)
- [ ] Import `streamlit_paste_button`, `io`, `hashlib`
- [ ] Add `save_uploaded_file()` function
- [ ] Add `save_pasted_image()` function
- [ ] Add `show_image_dialog()` function
- [ ] Update `init_session()` with image state
- [ ] Update `render_create_form()`:
  - [ ] Add paste button
  - [ ] Add file uploader
  - [ ] Add image counter
  - [ ] Save images on note creation
- [ ] Update `render_note_card()`:
  - [ ] Show first image thumbnail
  - [ ] Show image count
  - [ ] Add gallery button
- [ ] Update `render_edit_form()`:
  - [ ] Display existing attachments
  - [ ] Add new images
  - [ ] Remove images

### Backend (note_ops.py)
- [ ] Update `search_notes()` to load attachments

### File System
- [ ] Create `data/uploads/notes/` directory

## Code Reuse Strategy

Most code can be copied from `observations.py` with these replacements:

| Observations | Notes |
|-------------|-------|
| `tv_observations` | `gen_notes` |
| `tv_observation_screenshots` | `gen_note_attachments` |
| `observation_id` | `note_id` |
| `data/uploads/observations` | `data/uploads/notes` |
| `add_observation_screenshot()` | `add_note_attachment()` |
| `obs` | `note` |
| `stock_name` | `title` |
| `observation_text` | `content` |
