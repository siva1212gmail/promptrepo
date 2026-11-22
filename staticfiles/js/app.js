/**
 * PROMPT PETTI — CORE FRONTEND APPLICATION
 * Vanilla JavaScript (Fetch API) | Mobile-First | Zero Heavy Libraries
 */

(function () {
    'use strict';

    // Application State
    const state = {
        currentFilter: 'all',     // all, new, liked
        currentType: '',          // '', image, video
        currentCategory: 'all',
        searchQuery: '',
        currentPage: 1,
        hasNextPage: false,
        isLoading: false,
        activePromptId: null,
        activePromptSlug: null,
        savedPromptIds: JSON.parse(localStorage.getItem('petti_saved_prompts') || '[]'),
        likedPromptIds: JSON.parse(localStorage.getItem('petti_liked_prompts') || '[]'),
        isUnlocked: window.PETTI_CONFIG?.isUnlocked || false
    };

    // DOM Elements
    const elements = {
        promptsGrid: document.getElementById('prompts-grid'),
        gridLoader: document.getElementById('grid-loader'),
        searchInput: document.getElementById('prompt-search-input'),
        searchClearBtn: document.getElementById('search-clear-btn'),
        filterPills: document.querySelectorAll('.filter-pill'),
        categoryChips: document.querySelectorAll('.category-chip'),
        navSavedBtn: document.getElementById('nav-saved-btn'),
        savedBadge: document.getElementById('saved-badge'),
        mobileSavedLink: document.getElementById('mobile-saved-link'),
        mobileSavedCount: document.querySelector('.mobile-saved-count'),
        footerSavedLink: document.getElementById('footer-saved-link'),
        mobileMenuBtn: document.getElementById('mobile-menu-btn'),
        mobileMenu: document.getElementById('mobile-menu'),
        toastContainer: document.getElementById('toast-container'),

        // Countdown
        cdHours: document.getElementById('cd-hours'),
        cdMinutes: document.getElementById('cd-minutes'),
        cdSeconds: document.getElementById('cd-seconds'),

        // Terminal
        typedText: document.getElementById('terminal-typed-text'),
        terminalCopyBtn: document.getElementById('terminal-copy-btn'),

        // Request Form
        requestForm: document.getElementById('prompt-request-form'),
        reqText: document.getElementById('req-text'),
        charCounter: document.getElementById('char-counter'),
        reqImage: document.getElementById('req-image'),
        uploadLabelText: document.getElementById('upload-label-text'),
        imagePreviewWrap: document.getElementById('image-preview-wrap'),
        imagePreviewElem: document.getElementById('image-preview-elem'),
        removePreviewBtn: document.getElementById('remove-preview-btn'),
        requestStatusMsg: document.getElementById('request-status-msg'),
        requestSubmitBtn: document.getElementById('request-submit-btn'),

        // Modal
        modal: document.getElementById('prompt-modal'),
        modalCloseBtn: document.getElementById('modal-close-btn'),
        modalSliderContainer: document.getElementById('modal-slider-container'),
        modalBeforeImg: document.getElementById('modal-before-img'),
        modalAfterImg: document.getElementById('modal-after-img'),
        modalSingleImageWrap: document.getElementById('modal-single-image-wrap'),
        modalCoverImg: document.getElementById('modal-cover-img'),
        modalVideoWrap: document.getElementById('modal-video-wrap'),
        modalVideoLink: document.getElementById('modal-video-link'),
        modalCategoryLabel: document.getElementById('modal-category-label'),
        modalNewBadge: document.getElementById('modal-new-badge'),
        modalTitle: document.getElementById('modal-title'),
        modalLikeBtn: document.getElementById('modal-like-btn'),
        modalLikeCount: document.getElementById('modal-like-count'),
        modalSaveBtn: document.getElementById('modal-save-btn'),
        modalSaveText: document.getElementById('modal-save-text'),
        modalShareBtn: document.getElementById('modal-share-btn'),

        // Prompt Box Inside Modal
        promptLockedState: document.getElementById('prompt-locked-state'),
        promptUnlockedState: document.getElementById('prompt-unlocked-state'),
        step1SubscribeBtn: document.getElementById('step1-subscribe-btn'),
        step2UnlockBtn: document.getElementById('step2-unlock-btn'),
        realPromptText: document.getElementById('real-prompt-text'),
        copyRealPromptBtn: document.getElementById('copy-real-prompt-btn'),
        copyBtnLabel: document.getElementById('copy-btn-label'),
        openChatgptBtn: document.getElementById('open-chatgpt-btn'),
        openGeminiBtn: document.getElementById('open-gemini-btn'),
        scrollTopBtn: document.getElementById('scroll-top-btn')
    };

    /* ==========================================================================
       TOAST UTILITY
       ========================================================================== */
    function showToast(message, duration = 3000) {
        if (!elements.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /* ==========================================================================
       SAVED (BOOKMARK) HELPERS
       ========================================================================== */
    function updateSavedBadge() {
        const count = state.savedPromptIds.length;
        if (elements.savedBadge) {
            elements.savedBadge.textContent = count;
            elements.savedBadge.style.display = count > 0 ? 'flex' : 'none';
        }
        if (elements.mobileSavedCount) {
            elements.mobileSavedCount.textContent = count;
        }
    }

    function isPromptSaved(id) {
        return state.savedPromptIds.includes(Number(id));
    }

    function toggleSavePrompt(id) {
        id = Number(id);
        const idx = state.savedPromptIds.indexOf(id);
        if (idx > -1) {
            state.savedPromptIds.splice(idx, 1);
            showToast('Removed from Saved Prompts');
        } else {
            state.savedPromptIds.push(id);
            showToast('Saved to your collection! Tap bookmark to view.');
        }
        localStorage.setItem('petti_saved_prompts', JSON.stringify(state.savedPromptIds));
        updateSavedBadge();
        updateModalSaveButton();

        // If currently viewing "liked/saved" filter, refresh list
        if (state.currentFilter === 'liked') {
            fetchPrompts(true);
        }
    }

    function updateModalSaveButton() {
        if (!elements.modalSaveBtn || !state.activePromptId) return;
        const saved = isPromptSaved(state.activePromptId);
        elements.modalSaveBtn.classList.toggle('active', saved);
        if (elements.modalSaveText) {
            elements.modalSaveText.textContent = saved ? 'Saved ✓' : 'Save';
        }
    }

    /* ==========================================================================
       DAILY 6 PM IST COUNTDOWN TIMER
       ========================================================================== */
    function initCountdown() {
        if (!elements.cdHours) return;

        function getNextDropTime() {
            // IST is UTC + 5:30
            const now = new Date();
            const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
            const istOffset = 5.5 * 3600000;
            const nowIst = new Date(utcTime + istOffset);

            const dropIst = new Date(nowIst);
            dropIst.setHours(18, 0, 0, 0);

            if (nowIst.getTime() >= dropIst.getTime()) {
                // Drop time already passed today, target tomorrow 6 PM
                dropIst.setDate(dropIst.getDate() + 1);
            }

            // Convert back to local timestamp
            const diffFromIstNow = dropIst.getTime() - nowIst.getTime();
            return now.getTime() + diffFromIstNow;
        }

        let targetEpoch = getNextDropTime();

        function updateTimer() {
            const now = Date.now();
            let distance = targetEpoch - now;

            if (distance <= 0) {
                targetEpoch = getNextDropTime();
                distance = targetEpoch - now;
                // Fresh drop arrived!
                showToast("⚡ Fresh 6:00 PM IST Daily Drop is now live!");
            }

            const hours = Math.floor((distance / (1000 * 60 * 60)));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            elements.cdHours.textContent = String(hours).padStart(2, '0');
            elements.cdMinutes.textContent = String(minutes).padStart(2, '0');
            elements.cdSeconds.textContent = String(seconds).padStart(2, '0');
        }

        updateTimer();
        setInterval(updateTimer, 1000);
    }

    /* ==========================================================================
       HERO MOCK TERMINAL TYPING ANIMATION
       ========================================================================== */
    function initTerminalTyping() {
        if (!elements.typedText) return;

        const samplePrompts = [
            "Hyper-realistic cinematic portrait of a traditional Kathakali dancer in neon cyberpunk Fort Kochi rain, 8k octane render...",
            "Monsoon sunset at Chennai Marina Beach with dramatic storm clouds, golden hour reflections on wet sand, 85mm f/1.4 Kodachrome...",
            "Extreme macro 120fps slow-motion of grand Kerala Onam Sadhya feast, hot payasam drizzled on fresh plantain leaf...",
            "Surreal Lord Shiva deep Himalayan meditation under cosmic swirling nebula galaxy, Unreal Engine 5 render, cinematic rim lighting..."
        ];

        let promptIdx = 0;
        let charIdx = 0;
        let isDeleting = false;
        let currentString = samplePrompts[0];

        function typeLoop() {
            currentString = samplePrompts[promptIdx];

            if (!isDeleting) {
                charIdx++;
                elements.typedText.textContent = currentString.slice(0, charIdx);

                if (charIdx === currentString.length) {
                    isDeleting = true;
                    setTimeout(typeLoop, 2800); // Wait before deleting
                    return;
                }
            } else {
                charIdx--;
                elements.typedText.textContent = currentString.slice(0, charIdx);

                if (charIdx === 0) {
                    isDeleting = false;
                    promptIdx = (promptIdx + 1) % samplePrompts.length;
                    setTimeout(typeLoop, 500);
                    return;
                }
            }

            const speed = isDeleting ? 25 : (50 + Math.random() * 30);
            setTimeout(typeLoop, speed);
        }

        typeLoop();

        if (elements.terminalCopyBtn) {
            elements.terminalCopyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(currentString).then(() => {
                    showToast("Demo prompt copied to clipboard!");
                }).catch(() => {
                    showToast("Prompt copied!");
                });
            });
        }
    }

    /* ==========================================================================
       PROMPTS FETCH & GRID RENDERING
       ========================================================================== */
    function buildApiUrl() {
        const params = new URLSearchParams();
        if (state.searchQuery) params.set('q', state.searchQuery);
        if (state.currentType) params.set('type', state.currentType);
        if (state.currentCategory && state.currentCategory !== 'all') {
            params.set('category', state.currentCategory);
        }
        if (state.currentFilter) params.set('filter', state.currentFilter);
        if (state.currentFilter === 'liked' && state.savedPromptIds.length > 0) {
            params.set('ids', state.savedPromptIds.join(','));
        }
        params.set('page', state.currentPage);
        return `/api/prompts/?${params.toString()}`;
    }

    function fetchPrompts(reset = false) {
        if (reset) {
            state.currentPage = 1;
            elements.promptsGrid.innerHTML = '';
        }

        state.isLoading = true;
        if (elements.gridLoader) elements.gridLoader.style.display = 'flex';

        fetch(buildApiUrl())
            .then(res => res.json())
            .then(data => {
                state.isLoading = false;
                if (elements.gridLoader) elements.gridLoader.style.display = 'none';

                state.hasNextPage = data.has_next;

                if (reset && (!data.results || data.results.length === 0)) {
                    elements.promptsGrid.innerHTML = `
                        <div class="empty-state">
                            <p>No matching prompts found. Try a different search keyword or category!</p>
                        </div>
                    `;
                    return;
                }

                data.results.forEach(renderPromptCard);
            })
            .catch(err => {
                state.isLoading = false;
                if (elements.gridLoader) elements.gridLoader.style.display = 'none';
                console.error("Failed to fetch prompts", err);
            });
    }

    function renderPromptCard(p) {
        const card = document.createElement('article');
        card.className = 'prompt-card';
        card.setAttribute('data-prompt-id', p.id);
        card.setAttribute('data-prompt-slug', p.slug);
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
        card.setAttribute('aria-label', `View ${p.title}`);

        const typeBadge = p.type_display.toUpperCase();
        const baBadge = p.has_before_after ? '<span class="badge badge-ba">BEFORE / AFTER</span>' : '';
        const newBadge = p.is_new ? '<span class="badge badge-new">NEW</span>' : '';

        card.innerHTML = `
            <div class="card-media-wrap">
                ${p.cover_image_url ? `<img src="${p.cover_image_url}" alt="${p.title}" loading="lazy" width="400" height="500" class="card-img">` : ''}
                <div class="card-badges-top">
                    <span class="badge badge-type">${typeBadge}</span>
                    ${baBadge}
                    ${newBadge}
                </div>
            </div>
            <div class="card-body">
                <div class="card-meta">
                    <span class="card-category">${p.category_name.toUpperCase()}</span>
                    <span class="card-likes" data-likes-for="${p.id}">♥ ${p.total_likes}</span>
                </div>
                <h3 class="card-title">${p.title}</h3>
            </div>
        `;

        card.addEventListener('click', () => openPromptModal(p.id, p.slug));
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openPromptModal(p.id, p.slug);
            }
        });

        elements.promptsGrid.appendChild(card);
    }

    /* Debounce Utility */
    function debounce(func, delay) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    /* ==========================================================================
       PROMPT DETAIL POPUP (MODAL)
       ========================================================================== */
    function openPromptModal(id, slug = null) {
        state.activePromptId = id;
        state.activePromptSlug = slug;

        document.body.classList.add('modal-open');
        elements.modal.classList.add('active');
        elements.modal.setAttribute('aria-hidden', 'false');

        // Update URL cleanly for direct sharing
        if (slug && window.location.pathname !== `/p/${slug}/`) {
            history.pushState({ modalSlug: slug }, '', `/p/${slug}/`);
        }

        // Fetch prompt metadata (CRITICAL: without prompt text!)
        fetch(`/api/prompts/${id}/`)
            .then(res => res.json())
            .then(data => {
                populateModalDetails(data);

                // Check unlock state
                if (state.isUnlocked || checkUnlockCookie()) {
                    revealUnlockedPrompt(id);
                } else {
                    showLockedPrompt();
                }
            })
            .catch(err => {
                console.error("Error loading prompt details", err);
                showToast("Could not load prompt details.");
            });
    }

    function checkUnlockCookie() {
        return document.cookie.split(';').some(c => c.trim().startsWith('unlocked=true'));
    }

    function populateModalDetails(data) {
        elements.modalTitle.textContent = data.title;
        elements.modalCategoryLabel.textContent = `${data.type_display.toUpperCase()} PROMPT · ${data.category_name.toUpperCase()}`;
        elements.modalLikeCount.textContent = data.total_likes;
        elements.modalNewBadge.style.display = data.is_new ? 'inline-block' : 'none';

        // Like button active state
        const liked = data.user_liked || state.likedPromptIds.includes(data.id);
        elements.modalLikeBtn.classList.toggle('active', liked);

        // Save button active state
        updateModalSaveButton();

        // Handle Media: Before/After Slider vs Single Image vs Video
        if (data.has_before_after && data.before_image_url && data.after_image_url) {
            elements.modalSliderContainer.style.display = 'block';
            elements.modalSingleImageWrap.style.display = 'none';
            elements.modalVideoWrap.style.display = 'none';

            elements.modalBeforeImg.src = data.before_image_url;
            elements.modalAfterImg.src = data.after_image_url;

            if (window.BeforeAfterSlider) {
                window.BeforeAfterSlider.init(elements.modalSliderContainer);
            }
        } else if (data.type === 'video' && data.video_url) {
            elements.modalSliderContainer.style.display = 'none';
            elements.modalSingleImageWrap.style.display = 'none';
            elements.modalVideoWrap.style.display = 'flex';
            elements.modalVideoLink.href = data.video_url;
        } else {
            elements.modalSliderContainer.style.display = 'none';
            elements.modalVideoWrap.style.display = 'none';
            elements.modalSingleImageWrap.style.display = 'block';
            elements.modalCoverImg.src = data.cover_image_url || '';
        }
    }

    function showLockedPrompt() {
        elements.promptLockedState.style.display = 'block';
        elements.promptUnlockedState.style.display = 'none';

        // Reset step buttons
        elements.step1SubscribeBtn.style.display = 'inline-flex';
        elements.step2UnlockBtn.style.display = 'none';
    }

    function revealUnlockedPrompt(id) {
        elements.promptLockedState.style.display = 'none';
        elements.promptUnlockedState.style.display = 'block';
        elements.realPromptText.textContent = "Loading prompt secret text...";

        // Fetch real prompt text securely from /api/prompts/<id>/text/
        fetch(`/api/prompts/${id}/text/`)
            .then(res => {
                if (!res.ok) throw new Error("Prompt locked or forbidden");
                return res.json();
            })
            .then(data => {
                elements.realPromptText.textContent = data.prompt_text;
            })
            .catch(err => {
                console.error(err);
                elements.realPromptText.textContent = "Error loading prompt text. Please try unlocking again.";
            });
    }

    function closeModal() {
        document.body.classList.remove('modal-open');
        elements.modal.classList.remove('active');
        elements.modal.setAttribute('aria-hidden', 'true');
        state.activePromptId = null;
        state.activePromptSlug = null;

        if (window.BeforeAfterSlider) {
            window.BeforeAfterSlider.destroy();
        }

        // Restore clean home URL if opened via slug
        if (window.location.pathname.startsWith('/p/')) {
            history.pushState(null, '', '/');
        }
    }

    /* ==========================================================================
       UNLOCK FLOW
       ========================================================================== */
    function handleStep1Subscribe() {
        // Visitor clicks Step 1 -> opens YouTube in new tab
        // Immediately reveal Step 2 ("2. I'm subscribed ✓")
        setTimeout(() => {
            elements.step2UnlockBtn.style.display = 'inline-flex';
            elements.step2UnlockBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 600);
    }

    function handleStep2Unlock() {
        elements.step2UnlockBtn.disabled = true;
        elements.step2UnlockBtn.textContent = "Unlocking...";

        fetch('/api/unlock/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.PETTI_CONFIG.csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(res => res.json())
        .then(data => {
            state.isUnlocked = true;
            document.body.setAttribute('data-unlocked', 'true');
            showToast("✓ All prompts unlocked! Free forever.");
            if (state.activePromptId) {
                revealUnlockedPrompt(state.activePromptId);
            }
        })
        .catch(err => {
            console.error("Unlock failed", err);
            showToast("Unlock failed. Please try again.");
            elements.step2UnlockBtn.disabled = false;
            elements.step2UnlockBtn.textContent = "2. I'm subscribed ✓";
        });
    }

    /* ==========================================================================
       LIKE & SHARE
       ========================================================================== */
    function handleLikePrompt(id) {
        if (!id) return;

        fetch(`/api/prompts/${id}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.PETTI_CONFIG.csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                elements.modalLikeCount.textContent = data.total_likes;
                elements.modalLikeBtn.classList.toggle('active', data.liked);

                // Update localStorage
                const numId = Number(id);
                if (data.liked) {
                    if (!state.likedPromptIds.includes(numId)) state.likedPromptIds.push(numId);
                } else {
                    state.likedPromptIds = state.likedPromptIds.filter(x => x !== numId);
                }
                localStorage.setItem('petti_liked_prompts', JSON.stringify(state.likedPromptIds));

                // Update card like count in grid
                const cardLikes = document.querySelector(`.card-likes[data-likes-for="${id}"]`);
                if (cardLikes) {
                    cardLikes.textContent = `♥ ${data.total_likes}`;
                }
            }
        })
        .catch(err => console.error("Like error", err));
    }

    function handleSharePrompt() {
        const shareData = {
            title: elements.modalTitle.textContent,
            text: `Check out this trending AI prompt on Prompt Petti by @aswinthefilmer!`,
            url: window.location.href
        };

        if (navigator.share) {
            navigator.share(shareData).catch(() => {});
        } else {
            navigator.clipboard.writeText(shareData.url).then(() => {
                showToast("Link copied to clipboard! Share it to your story.");
            });
        }
    }

    /* ==========================================================================
       REQUEST A PROMPT FORM
       ========================================================================== */
    function initRequestForm() {
        if (!elements.requestForm) return;

        // Character counter
        if (elements.reqText && elements.charCounter) {
            elements.reqText.addEventListener('input', () => {
                const len = elements.reqText.value.length;
                elements.charCounter.textContent = `${len}/180`;
                elements.charCounter.style.color = len > 170 ? '#f59e0b' : 'var(--text-muted)';
            });
        }

        // Image file selection & preview
        if (elements.reqImage) {
            elements.reqImage.addEventListener('change', () => {
                const file = elements.reqImage.files[0];
                if (!file) return;

                // Validate 5 MB
                if (file.size > 5 * 1024 * 1024) {
                    alert("Image must be smaller than 5 MB.");
                    elements.reqImage.value = '';
                    return;
                }

                // Show preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    elements.imagePreviewElem.src = e.target.result;
                    elements.imagePreviewWrap.style.display = 'block';
                    elements.uploadLabelText.textContent = file.name;
                };
                reader.readAsDataURL(file);
            });
        }

        // Remove image preview
        if (elements.removePreviewBtn) {
            elements.removePreviewBtn.addEventListener('click', () => {
                elements.reqImage.value = '';
                elements.imagePreviewElem.src = '';
                elements.imagePreviewWrap.style.display = 'none';
                elements.uploadLabelText.textContent = "Choose photo (JPG, PNG, WebP ≤ 5MB)";
            });
        }

        // Form Submit
        elements.requestForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const submitBtn = elements.requestSubmitBtn;
            const statusMsg = elements.requestStatusMsg;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span>Dropping into box...</span>';
            statusMsg.style.display = 'none';

            const formData = new FormData(elements.requestForm);

            fetch('/api/requests/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.PETTI_CONFIG.csrfToken
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Request</span>';

                if (data.success) {
                    statusMsg.className = 'form-status-msg success';
                    statusMsg.textContent = data.message;
                    statusMsg.style.display = 'block';
                    elements.requestForm.reset();
                    elements.charCounter.textContent = '0/180';
                    elements.imagePreviewWrap.style.display = 'none';
                    elements.uploadLabelText.textContent = "Choose photo (JPG, PNG, WebP ≤ 5MB)";
                    showToast("✓ Request dropped! Thank you.");
                } else {
                    statusMsg.className = 'form-status-msg error';
                    statusMsg.textContent = data.error || 'Submission failed.';
                    statusMsg.style.display = 'block';
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>Request</span>';
                statusMsg.className = 'form-status-msg error';
                statusMsg.textContent = 'Network error. Please try again.';
                statusMsg.style.display = 'block';
            });
        });
    }

    /* ==========================================================================
       EVENT LISTENERS & INITIALIZATION
       ========================================================================== */
    function attachEventListeners() {
        // Mobile Menu Toggle
        if (elements.mobileMenuBtn && elements.mobileMenu) {
            elements.mobileMenuBtn.addEventListener('click', () => {
                const isOpen = elements.mobileMenu.classList.toggle('open');
                elements.mobileMenuBtn.setAttribute('aria-expanded', isOpen);
                elements.mobileMenu.setAttribute('aria-hidden', !isOpen);
            });

            // Close mobile menu when link tapped
            elements.mobileMenu.querySelectorAll('[data-close-menu]').forEach(link => {
                link.addEventListener('click', () => {
                    elements.mobileMenu.classList.remove('open');
                    elements.mobileMenuBtn.setAttribute('aria-expanded', 'false');
                    elements.mobileMenu.setAttribute('aria-hidden', 'true');
                });
            });
        }

        // Search Input (Live & Debounced)
        if (elements.searchInput) {
            const debouncedSearch = debounce(() => {
                state.searchQuery = elements.searchInput.value.trim();
                elements.searchClearBtn.style.display = state.searchQuery ? 'block' : 'none';
                fetchPrompts(true);
            }, 300);

            elements.searchInput.addEventListener('input', debouncedSearch);

            if (elements.searchClearBtn) {
                elements.searchClearBtn.addEventListener('click', () => {
                    elements.searchInput.value = '';
                    state.searchQuery = '';
                    elements.searchClearBtn.style.display = 'none';
                    fetchPrompts(true);
                });
            }
        }

        // Filter Pills
        elements.filterPills.forEach(pill => {
            pill.addEventListener('click', () => {
                elements.filterPills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');

                const filterVal = pill.getAttribute('data-filter');
                const typeVal = pill.getAttribute('data-type');

                if (typeVal) {
                    state.currentType = typeVal;
                    state.currentFilter = 'all';
                } else if (filterVal) {
                    state.currentFilter = filterVal;
                    state.currentType = '';
                }

                fetchPrompts(true);
            });
        });

        // Category Chips
        elements.categoryChips.forEach(chip => {
            chip.addEventListener('click', () => {
                elements.categoryChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');

                state.currentCategory = chip.getAttribute('data-category');
                fetchPrompts(true);
            });
        });

        // Saved (Bookmark) Button in Navbar & Footer
        function triggerSavedView() {
            elements.filterPills.forEach(p => p.classList.remove('active'));
            const likedPill = document.querySelector('.filter-pill[data-filter="liked"]');
            if (likedPill) likedPill.classList.add('active');

            state.currentFilter = 'liked';
            state.currentType = '';
            fetchPrompts(true);

            const promptsSection = document.getElementById('prompts');
            if (promptsSection) {
                promptsSection.scrollIntoView({ behavior: 'smooth' });
            }
        }

        if (elements.navSavedBtn) elements.navSavedBtn.addEventListener('click', triggerSavedView);
        if (elements.mobileSavedLink) elements.mobileSavedLink.addEventListener('click', triggerSavedView);
        if (elements.footerSavedLink) {
            elements.footerSavedLink.addEventListener('click', (e) => {
                e.preventDefault();
                triggerSavedView();
            });
        }

        // Modal Close Button & Backdrop
        if (elements.modalCloseBtn) {
            elements.modalCloseBtn.addEventListener('click', closeModal);
        }

        if (elements.modal) {
            elements.modal.addEventListener('click', (e) => {
                if (e.target === elements.modal) {
                    closeModal();
                }
            });
        }

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && elements.modal.classList.contains('active')) {
                closeModal();
            }
        });

        window.addEventListener('popstate', (e) => {
            if (elements.modal.classList.contains('active')) {
                closeModal();
            }
        });

        // Modal Actions
        if (elements.modalLikeBtn) {
            elements.modalLikeBtn.addEventListener('click', () => {
                handleLikePrompt(state.activePromptId);
            });
        }

        if (elements.modalSaveBtn) {
            elements.modalSaveBtn.addEventListener('click', () => {
                toggleSavePrompt(state.activePromptId);
            });
        }

        if (elements.modalShareBtn) {
            elements.modalShareBtn.addEventListener('click', handleSharePrompt);
        }

        // Modal Unlock Buttons
        if (elements.step1SubscribeBtn) {
            elements.step1SubscribeBtn.addEventListener('click', handleStep1Subscribe);
        }

        if (elements.step2UnlockBtn) {
            elements.step2UnlockBtn.addEventListener('click', handleStep2Unlock);
        }

        // Copy Real Prompt Button
        if (elements.copyRealPromptBtn) {
            elements.copyRealPromptBtn.addEventListener('click', () => {
                const text = elements.realPromptText.textContent;
                navigator.clipboard.writeText(text).then(() => {
                    elements.copyBtnLabel.textContent = "Copied ✓";
                    showToast("Prompt copied to clipboard! Ready to paste into ChatGPT or Gemini.");
                    setTimeout(() => {
                        elements.copyBtnLabel.textContent = "Copy Prompt";
                    }, 2000);
                }).catch(() => {
                    showToast("Prompt copied!");
                });
            });
        }

        // Open in ChatGPT / Gemini Buttons
        if (elements.openChatgptBtn) {
            elements.openChatgptBtn.addEventListener('click', () => {
                const text = elements.realPromptText.textContent;
                navigator.clipboard.writeText(text);
                showToast("Prompt copied! Opening ChatGPT ↗");
                window.open('https://chatgpt.com', '_blank');
            });
        }

        if (elements.openGeminiBtn) {
            elements.openGeminiBtn.addEventListener('click', () => {
                const text = elements.realPromptText.textContent;
                navigator.clipboard.writeText(text);
                showToast("Prompt copied! Opening Gemini ↗");
                window.open('https://gemini.google.com', '_blank');
            });
        }

        // Scroll to top button
        if (elements.scrollTopBtn) {
            elements.scrollTopBtn.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        // Existing Card Clicks (Server-Rendered Initial Grid & Most Liked)
        document.querySelectorAll('.prompt-card, .ranked-card').forEach(card => {
            const promptId = card.getAttribute('data-prompt-id');
            const promptSlug = card.getAttribute('data-prompt-slug');
            card.addEventListener('click', () => openPromptModal(promptId, promptSlug));
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openPromptModal(promptId, promptSlug);
                }
            });
        });
    }

    // App Initialization
    function init() {
        updateSavedBadge();
        initCountdown();
        initTerminalTyping();
        initRequestForm();
        attachEventListeners();

        // Check if page loaded directly with initial_prompt_slug (e.g. /p/<slug>/)
        if (window.PETTI_CONFIG?.initialPromptSlug) {
            const initialCard = document.querySelector(`[data-prompt-slug="${window.PETTI_CONFIG.initialPromptSlug}"]`);
            if (initialCard) {
                const id = initialCard.getAttribute('data-prompt-id');
                openPromptModal(id, window.PETTI_CONFIG.initialPromptSlug);
            }
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();
