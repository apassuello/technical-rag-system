# HuggingFace Spaces Upload Checklist

## 1. Create Space
- [ ] Go to https://huggingface.co/spaces
- [ ] Click "Create new Space"
- [ ] Name: technical-rag-assistant (or your choice)
- [ ] SDK: Docker ⚠️ **IMPORTANT: Choose Docker, not Streamlit**
- [ ] Hardware: CPU basic
- [ ] Visibility: Public
- [ ] License: MIT

## 2. Upload Files (from hf_deployment/ folder)
- [ ] Dockerfile ⚠️ **NEW: Docker configuration for Streamlit**
- [ ] app.py (HF Spaces entry point)
- [ ] streamlit_app.py (main application)
- [ ] requirements.txt (HF compatible)
- [ ] README.md (documentation)
- [ ] src/ (source code directory)
- [ ] shared_utils/ (utilities directory)
- [ ] data/test/ (sample documents)
- [ ] tests/ (essential tests)

## 3. Configuration
- [ ] Verify SDK is set to "Docker" ⚠️ **IMPORTANT: Docker, not Streamlit**
- [ ] Dockerfile will handle Python version automatically
- [ ] Check hardware is CPU basic (free tier)
- [ ] Ensure visibility is set as desired

## 4. Post-Deployment Testing
- [ ] Space builds successfully
- [ ] App loads without errors
- [ ] Demo mode message displays correctly
- [ ] Document upload works
- [ ] Search functionality demonstrates
- [ ] UI is responsive and professional

## 5. Portfolio Integration
- [ ] Add HF Spaces link to resume/portfolio
- [ ] Test link works from external access
- [ ] Verify professional presentation
- [ ] Share with potential employers/recruiters