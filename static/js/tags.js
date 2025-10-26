// Tag Management Module

// Shared tag component logic
class TagManager {
    constructor(tagInputId, tagWrapperId, selectedTagsContainerId, suggestionsDropdownId, tagsHiddenId) {
        this.tagInput = document.getElementById(tagInputId);
        this.tagWrapper = document.getElementById(tagWrapperId);
        this.selectedTagsContainer = document.getElementById(selectedTagsContainerId);
        this.suggestionsDropdown = document.getElementById(suggestionsDropdownId);
        this.tagsHidden = document.getElementById(tagsHiddenId);
        
        // Verify all elements exist
        if (!this.tagInput || !this.tagWrapper || !this.selectedTagsContainer || 
            !this.suggestionsDropdown || !this.tagsHidden) {
            console.error('TagManager: One or more required elements not found', {
                tagInput: !!this.tagInput,
                tagWrapper: !!this.tagWrapper,
                selectedTagsContainer: !!this.selectedTagsContainer,
                suggestionsDropdown: !!this.suggestionsDropdown,
                tagsHidden: !!this.tagsHidden
            });
            return;
        }
        
        this.currentTags = [];
        this.allAvailableTags = [];
        this.selectedSuggestionIndex = -1;
        
        this.init();
    }
    
    init() {
        this.loadAvailableTags();
        this.setupEventListeners();
    }
    
    loadAvailableTags() {
        fetch('/api/tags')
            .then(response => response.json())
            .then(data => {
                this.allAvailableTags = data.tags || [];
            })
            .catch(error => {
                console.error('Failed to load tags:', error);
                this.allAvailableTags = [];
            });
    }
    
    addTag(tagValue) {
        tagValue = tagValue.trim();
        if (!tagValue) return;
        
        if (this.currentTags.includes(tagValue)) {
            if (this.tagInput) this.tagInput.value = '';
            return;
        }
        
        if (this.currentTags.length >= 3) {
            showErrorToast('Maximum 3 tags allowed per account');
            if (this.tagInput) this.tagInput.value = '';
            return;
        }
        
        this.currentTags.push(tagValue);
        this.updateTagDisplay();
        this.updateHiddenInput();
        if (this.tagInput) this.tagInput.value = '';
        this.hideSuggestions();
    }
    
    removeTag(tagToRemove) {
        this.currentTags = this.currentTags.filter(tag => tag !== tagToRemove);
        this.updateTagDisplay();
        this.updateHiddenInput();
        if (this.tagInput) this.tagInput.focus();
    }
    
    updateTagDisplay() {
        if (!this.selectedTagsContainer) return;
        
        this.selectedTagsContainer.innerHTML = '';
        this.currentTags.forEach(tag => {
            const badge = document.createElement('span');
            badge.className = 'tag-badge';
            badge.innerHTML = `
                ${tag}
                <button type="button" class="tag-badge-remove" data-tag="${tag}" aria-label="Remove tag">×</button>
            `;
            
            badge.querySelector('.tag-badge-remove').addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeTag(e.target.dataset.tag);
            });
            
            this.selectedTagsContainer.appendChild(badge);
        });
    }
    
    updateHiddenInput() {
        if (!this.tagsHidden) return;
        this.tagsHidden.value = JSON.stringify(this.currentTags);
    }
    
    showSuggestions(searchTerm) {
        if (!this.suggestionsDropdown) return;
        searchTerm = searchTerm.toLowerCase().trim();
        
        if (!searchTerm) {
            const availableTags = this.allAvailableTags.filter(tag => !this.currentTags.includes(tag));
            if (availableTags.length === 0) {
                this.hideSuggestions();
                return;
            }
            this.renderSuggestions(availableTags, '');
            return;
        }
        
        const matchingTags = this.allAvailableTags.filter(tag => 
            tag.toLowerCase().includes(searchTerm) && !this.currentTags.includes(tag)
        );
        
        const exactMatch = this.allAvailableTags.find(tag => tag.toLowerCase() === searchTerm);
        
        if (matchingTags.length === 0 && !exactMatch) {
            this.renderSuggestions([searchTerm], searchTerm, true);
        } else if (matchingTags.length > 0) {
            this.renderSuggestions(matchingTags, searchTerm);
        } else {
            this.hideSuggestions();
        }
    }
    
    renderSuggestions(tags, searchTerm, isNewTag = false) {
        this.suggestionsDropdown.innerHTML = '';
        this.selectedSuggestionIndex = -1;
        
        if (isNewTag) {
            const item = document.createElement('div');
            item.className = 'tag-suggestion-item';
            item.innerHTML = `
                <span class="tag-suggestion-icon">+</span>
                <span class="tag-suggestion-text">Create "<strong>${tags[0]}</strong>"</span>
            `;
            item.dataset.tag = tags[0];
            item.addEventListener('click', () => this.addTag(tags[0]));
            this.suggestionsDropdown.appendChild(item);
        } else {
            tags.forEach(tag => {
                const item = document.createElement('div');
                item.className = 'tag-suggestion-item';
                const highlightedText = this.highlightMatch(tag, searchTerm);
                item.innerHTML = `
                    <span class="tag-suggestion-icon">🏷️</span>
                    <span class="tag-suggestion-text">${highlightedText}</span>
                `;
                item.dataset.tag = tag;
                item.addEventListener('click', () => this.addTag(tag));
                this.suggestionsDropdown.appendChild(item);
            });
        }
        
        this.suggestionsDropdown.style.display = 'block';
    }
    
    highlightMatch(text, searchTerm) {
        if (!searchTerm) return text;
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }
    
    hideSuggestions() {
        this.suggestionsDropdown.style.display = 'none';
        this.selectedSuggestionIndex = -1;
    }
    
    navigateSuggestions(direction) {
        const items = this.suggestionsDropdown.querySelectorAll('.tag-suggestion-item');
        if (items.length === 0) return;
        
        if (this.selectedSuggestionIndex >= 0 && items[this.selectedSuggestionIndex]) {
            items[this.selectedSuggestionIndex].classList.remove('active');
        }
        
        if (direction === 'down') {
            this.selectedSuggestionIndex = (this.selectedSuggestionIndex + 1) % items.length;
        } else if (direction === 'up') {
            this.selectedSuggestionIndex = this.selectedSuggestionIndex <= 0 ? items.length - 1 : this.selectedSuggestionIndex - 1;
        }
        
        items[this.selectedSuggestionIndex].classList.add('active');
        items[this.selectedSuggestionIndex].scrollIntoView({ block: 'nearest' });
    }
    
    selectCurrentSuggestion() {
        const items = this.suggestionsDropdown.querySelectorAll('.tag-suggestion-item');
        if (this.selectedSuggestionIndex >= 0 && items[this.selectedSuggestionIndex]) {
            const tag = items[this.selectedSuggestionIndex].dataset.tag;
            this.addTag(tag);
            return true;
        }
        return false;
    }
    
    clearTags() {
        this.currentTags = [];
        this.updateTagDisplay();
        this.updateHiddenInput();
        this.tagInput.value = '';
        this.hideSuggestions();
    }
    
    setTags(tags) {
        this.currentTags = tags || [];
        this.updateTagDisplay();
        this.updateHiddenInput();
    }
    
    setupEventListeners() {
        if (!this.tagInput || !this.tagWrapper) return;
        
        this.tagInput.addEventListener('input', () => {
            this.showSuggestions(this.tagInput.value);
        });
        
        this.tagInput.addEventListener('focus', () => {
            this.showSuggestions(this.tagInput.value);
        });
        
        this.tagInput.addEventListener('keydown', (e) => {
            const suggestionsVisible = this.suggestionsDropdown.style.display === 'block';
            
            if (e.key === 'Enter') {
                e.preventDefault();
                if (suggestionsVisible && this.selectCurrentSuggestion()) {
                    // Selected from dropdown
                } else if (this.tagInput.value.trim()) {
                    this.addTag(this.tagInput.value);
                }
            } else if (e.key === ',' || e.key === ';') {
                e.preventDefault();
                if (this.tagInput.value.trim()) {
                    this.addTag(this.tagInput.value);
                }
            } else if (e.key === 'Backspace' && !this.tagInput.value && this.currentTags.length > 0) {
                this.removeTag(this.currentTags[this.currentTags.length - 1]);
            } else if (e.key === 'ArrowDown' && suggestionsVisible) {
                e.preventDefault();
                this.navigateSuggestions('down');
            } else if (e.key === 'ArrowUp' && suggestionsVisible) {
                e.preventDefault();
                this.navigateSuggestions('up');
            } else if (e.key === 'Escape') {
                this.hideSuggestions();
            }
        });
        
        this.tagWrapper.addEventListener('click', (e) => {
            if (e.target === this.tagWrapper || e.target === this.selectedTagsContainer) {
                this.tagInput.focus();
            }
        });
        
        document.addEventListener('click', (e) => {
            if (!this.tagWrapper.contains(e.target) && !this.suggestionsDropdown.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }
}

// Initialize tag managers
let addAssetTagManager;
let editTagsManager;

function initializeTagManagement() {
    // Wait for DOM to be ready
    if (!document.getElementById('asset-tag-input')) {
        console.error('Tag input elements not found. Retrying...');
        setTimeout(initializeTagManagement, 100);
        return;
    }
    
    addAssetTagManager = new TagManager(
        'asset-tag-input',
        'tag-input-wrapper',
        'selected-tags',
        'tag-suggestions-dropdown',
        'asset-tags-hidden'
    );
    
    // Clear tags when add asset modal opens
    const modal = document.getElementById('addAssetModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', () => {
            addAssetTagManager.clearTags();
            addAssetTagManager.loadAvailableTags();
        });
    }
}

function initializeEditTagsModal() {
    // Wait for DOM to be ready
    if (!document.getElementById('edit-tag-input')) {
        console.error('Edit tag input elements not found. Retrying...');
        setTimeout(initializeEditTagsModal, 100);
        return;
    }
    
    editTagsManager = new TagManager(
        'edit-tag-input',
        'edit-tag-input-wrapper',
        'edit-selected-tags',
        'edit-tag-suggestions-dropdown',
        'edit-tags-hidden'
    );
    
    const modal = document.getElementById('editTagsModal');
    const accountIdInput = document.getElementById('edit-tags-account-id');
    const saveBtn = document.getElementById('save-tags-btn');
    
    modal.addEventListener('show.bs.modal', () => {
        editTagsManager.loadAvailableTags();
    });
    
    modal.addEventListener('hide.bs.modal', () => {
        if (document.activeElement && modal.contains(document.activeElement)) {
            document.activeElement.blur();
        }
    });
    
    saveBtn.addEventListener('click', async () => {
        const accountId = accountIdInput.value;
        const tags = JSON.parse(document.getElementById('edit-tags-hidden').value || '[]');
        
        try {
            const response = await fetch(`/api/accounts/${accountId}/field`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.sessionData.csrfToken
                },
                body: JSON.stringify({
                    field: 'tags',
                    value: tags
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccessToast('Tags updated successfully!');
                bootstrap.Modal.getInstance(modal).hide();
                loadAccounts();
                loadAssetDetails(accountId);
            } else {
                showErrorToast('Error updating tags: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error updating tags:', error);
            showErrorToast('Error updating tags: ' + error.message);
        }
    });
    
    // Expose function to open modal
    window.openEditTagsModal = function(accountId, tagsToEdit) {
        accountIdInput.value = accountId;
        editTagsManager.setTags(tagsToEdit);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    };
}

function editTagsField(accountId) {
    const accounts = [...(AppState.accountsData.assets || []), ...(AppState.accountsData.liabilities || [])];
    const account = accounts.find(acc => acc.id === parseInt(accountId));
    
    if (!account) {
        console.error('Account not found:', accountId);
        return;
    }
    
    const currentTags = account.tags || [];
    window.openEditTagsModal(accountId, currentTags);
}

// Expose functions globally
window.initializeTagManagement = initializeTagManagement;
window.initializeEditTagsModal = initializeEditTagsModal;
window.editTagsField = editTagsField;
