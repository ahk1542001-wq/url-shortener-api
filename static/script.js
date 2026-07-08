document.addEventListener('DOMContentLoaded', () => {
    // --- UI Views ---
    const landingView = document.getElementById('landing-view');
    const loginView = document.getElementById('login-view');
    const dashboardView = document.getElementById('dashboard-view');
    const headerSubtitle = document.getElementById('header-subtitle');

    // --- Navbar Elements ---
    const navLoginBtn = document.getElementById('nav-login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const backToHomeBtn = document.getElementById('back-to-home-btn');

    // --- Login Elements ---
    const passwordInput = document.getElementById('password');
    const passwordBtn = document.getElementById('password-btn');
    const passwordError = document.getElementById('password-error');
    const togglePassword = document.getElementById('toggle-password');

    // --- Dashboard Tabs ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // --- Link Form Elements ---
    const form = document.getElementById('shorten-form');
    const urlInput = document.getElementById('url');
    const titleInput = document.getElementById('title');
    const customCodeInput = document.getElementById('custom_code');
    const showOnTreeCheck = document.getElementById('show_on_tree');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('span');
    const loadingContainer = document.getElementById('loading-container');
    const loadingText = document.getElementById('loading-text');

    const errorMsg = document.getElementById('error-message');
    const resultSection = document.getElementById('result-section');
    const shortLinkUrl = document.getElementById('short-link-url');
    const copyBtn = document.getElementById('copy-btn');
    const newLinkBtn = document.getElementById('new-link-btn');
    const refreshLinksBtn = document.getElementById('refresh-links-btn');
    const linksList = document.getElementById('links-list');

    // --- Edit Modal Elements ---
    const editModal = document.getElementById('edit-modal');
    const editForm = document.getElementById('edit-form');
    const editUrlInput = document.getElementById('edit-url');
    const editTitleInput = document.getElementById('edit-title');
    const editShowTreeCheck = document.getElementById('edit-show-tree');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    let currentEditCode = null;

    // Loading Messages
    const loadingMessages = [
        "Waking up the server...",
        "Establishing secure connection...",
        "Almost there, please hold on...",
        "Finalizing your premium link..."
    ];
    let loadingInterval = null;

    // --- Helpers ---
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? '✨' : '⚠️';
        toast.innerHTML = `<span style="font-size: 1.2rem;">${icon}</span> <span>${escapeHtml(message)}</span>`;
        
        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function getPassword() {
        return localStorage.getItem('swoosh_password') || '';
    }

    function headers() {
        const h = { 'Content-Type': 'application/json' };
        const pw = getPassword();
        if (pw) h['X-Access-Password'] = pw;
        return h;
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function handle401(r) {
        if (r.status === 401) {
            localStorage.removeItem('swoosh_password');
            showLanding();
            return true;
        }
        return false;
    }

    // --- View Routing ---
    function hideAllViews() {
        landingView.classList.add('hidden');
        loginView.classList.add('hidden');
        dashboardView.classList.add('hidden');
    }

    function showLanding() {
        hideAllViews();
        landingView.classList.remove('hidden');
        navLoginBtn.classList.remove('hidden');
        logoutBtn.classList.add('hidden');
        headerSubtitle.style.display = 'block';
    }

    function showLogin() {
        hideAllViews();
        loginView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        logoutBtn.classList.add('hidden');
        headerSubtitle.style.display = 'block';
        passwordInput.value = '';
        passwordError.classList.add('hidden');
        setTimeout(() => passwordInput.focus(), 100);
    }

    function showDashboard() {
        hideAllViews();
        dashboardView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        logoutBtn.classList.remove('hidden');
        headerSubtitle.style.display = 'none';
        
        loadDashboardData();
        loadLinks();
    }

    navLoginBtn.addEventListener('click', showLogin);
    backToHomeBtn.addEventListener('click', showLanding);

    // --- Tabs Logic ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            // Add active to clicked
            btn.classList.add('active');
            const targetId = `tab-${btn.dataset.tab}`;
            document.getElementById(targetId).classList.remove('hidden');
        });
    });

    // --- Auth Logic ---
    passwordBtn.addEventListener('click', async () => {
        const pw = passwordInput.value.trim();
        if (!pw) {
            showToast('Please enter a passcode', 'error');
            return;
        }

        const originalText = passwordBtn.querySelector('span').textContent;
        passwordBtn.querySelector('span').textContent = "Authenticating...";
        passwordBtn.disabled = true;

        try {
            const r = await fetch('/api/me', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', 'X-Access-Password': pw }
            });
            if (r.status === 401) {
                showToast('Incorrect passcode', 'error');
                return;
            }
            if (!r.ok) {
                showToast('Server connection failed', 'error');
                return;
            }

            localStorage.setItem('swoosh_password', pw);
            showToast('Authentication successful', 'success');
            showDashboard();
        } catch(err) {
            showToast('Network error', 'error');
        } finally {
            passwordBtn.querySelector('span').textContent = originalText;
            passwordBtn.disabled = false;
        }
    });

    passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') passwordBtn.click();
    });

    togglePassword.addEventListener('click', () => {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        togglePassword.querySelector('.eye-open').classList.toggle('hidden', !isPassword);
        togglePassword.querySelector('.eye-closed').classList.toggle('hidden', isPassword);
        togglePassword.title = isPassword ? 'Hide passcode' : 'Show passcode';
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('swoosh_password');
        showLanding();
        showToast('Logged out successfully', 'success');
    });

    // --- Data Loading ---
    async function loadDashboardData() {
        try {
            const r = await fetch('/api/me', { headers: headers() });
            if (handle401(r)) return;
            if (!r.ok) throw new Error('Failed to load profile data');
            const data = await r.json();
            
            const myTreeUrl = `${window.location.origin}/u/${data.username}`;
            const myTreeLink = document.getElementById('my-tree-url');
            myTreeLink.href = myTreeUrl;
            myTreeLink.textContent = `swoo.sh/u/${data.username}`;
            
            document.getElementById('view-tree-btn').href = myTreeUrl;
            document.getElementById('tree-views-count').textContent = data.tree_views;
            
            if (data.bio) {
                document.getElementById('profile-bio').value = data.bio;
            }
            
            document.getElementById('copy-tree-btn').onclick = () => {
                navigator.clipboard.writeText(myTreeUrl).then(() => {
                    showToast('Link Tree URL copied', 'success');
                });
            };
        } catch (err) {
            console.error(err);
        }
    }

    async function loadLinks() {
        try {
            const r = await fetch('/api/links', { headers: headers() });
            if (handle401(r)) return;
            if (!r.ok) throw new Error('Failed to load portfolio');

            const data = await r.json();

            if (!data.links || data.links.length === 0) {
                linksList.innerHTML = '<div class="text-muted" style="text-align: center; padding: 2rem 0;">Your portfolio is empty. Create a link above.</div>';
                return;
            }

            const checkIconSVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            const copyIconSVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;

            linksList.innerHTML = data.links.map(link => {
                const lastAccessed = link.last_accessed === 'Never'
                    ? 'Unvisited'
                    : new Date(link.last_accessed + 'Z').toLocaleDateString();
                    
                const treeBadge = link.show_on_tree ? `<span style="font-size: 0.7rem; background: var(--accent-glow); color: var(--accent); padding: 0.1rem 0.4rem; border-radius: 4px; margin-left: 0.5rem;">On Tree</span>` : '';
                const displayTitle = link.title || escapeHtml(link.original_url);

                return `
                    <div class="link-item">
                        <div class="link-info">
                            <div class="link-code">${escapeHtml(link.short_code)} ${treeBadge}</div>
                            <div class="link-url" title="${escapeHtml(link.original_url)}">${displayTitle}</div>
                        </div>
                        <div class="link-stats">
                            <div class="link-clicks">${link.click_count}</div>
                            <div class="link-date">${lastAccessed}</div>
                        </div>
                        <div style="display:flex; align-items:center;">
                            <button class="copy-link-btn" data-code="${escapeHtml(link.short_code)}" title="Copy Link">
                                ${copyIconSVG}
                            </button>
                            <button class="edit-btn" data-code="${escapeHtml(link.short_code)}" data-url="${escapeHtml(link.original_url)}" data-title="${escapeHtml(link.title || '')}" data-tree="${link.show_on_tree}" title="Edit">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            </button>
                            <button class="delete-btn" data-code="${escapeHtml(link.short_code)}" title="Delete">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            document.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteLink(btn.dataset.code));
            });

            document.querySelectorAll('.edit-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    openEditModal(btn.dataset.code, btn.dataset.url, btn.dataset.title, btn.dataset.tree === 'true');
                });
            });

            document.querySelectorAll('.copy-link-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const fullUrl = `${window.location.origin}/${btn.dataset.code}`;
                    navigator.clipboard.writeText(fullUrl).then(() => {
                        btn.innerHTML = checkIconSVG;
                        btn.style.color = '#10B981';
                        showToast('Link copied to clipboard', 'success');
                        setTimeout(() => { 
                            btn.innerHTML = copyIconSVG; 
                            btn.style.color = 'var(--text-muted)';
                        }, 2000);
                    });
                });
            });
        } catch (err) {
            console.error('loadLinks failed:', err);
            linksList.innerHTML = '<div class="text-muted" style="text-align: center; padding: 2rem 0;">Failed to load portfolio</div>';
        }
    }

    refreshLinksBtn.addEventListener('click', loadLinks);

    // --- Link Operations ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorMsg.classList.add('hidden');
        resultSection.classList.add('hidden');

        const url = urlInput.value.trim();
        const customCode = customCodeInput.value.trim();
        const title = titleInput.value.trim();
        const showOnTree = showOnTreeCheck.checked;

        if(!url) return;

        btnText.style.display = 'none';
        submitBtn.disabled = true;
        urlInput.disabled = true;
        titleInput.disabled = true;
        customCodeInput.disabled = true;
        loadingContainer.style.display = 'block';
        loadingText.textContent = loadingMessages[0];
        
        let msgIndex = 1;
        loadingInterval = setInterval(() => {
            if(msgIndex < loadingMessages.length) {
                loadingText.textContent = loadingMessages[msgIndex];
                msgIndex++;
            }
        }, 12000);

        try {
            const payload = { url, show_on_tree: showOnTree };
            if (customCode) payload.custom_code = customCode;
            if (title) payload.title = title;

            const response = await fetch('/api/shorten', {
                method: 'POST',
                headers: headers(),
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                if (handle401(response)) return;
                throw new Error(data.detail || data.error?.message || 'Failed to shorten URL');
            }

            const fullShortUrl = `${window.location.origin}/${data.short_code}`;

            shortLinkUrl.href = fullShortUrl;
            shortLinkUrl.textContent = fullShortUrl;

            const qrCodeImg = document.getElementById('qr-code-img');
            const qrCodeContainer = document.getElementById('qr-code-container');
            qrCodeImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(fullShortUrl)}`;
            qrCodeContainer.classList.remove('hidden');

            const resultText = resultSection.querySelector('p');
            resultText.textContent = data.already_exists
                ? 'This link was already in your portfolio.'
                : 'Your premium link is ready.';

            form.classList.add('hidden');
            resultSection.classList.remove('hidden');

            loadLinks();
            showToast('Link shortened successfully', 'success');

        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            clearInterval(loadingInterval);
            btnText.style.display = 'block';
            loadingContainer.style.display = 'none';
            submitBtn.disabled = false;
            urlInput.disabled = false;
            titleInput.disabled = false;
            customCodeInput.disabled = false;
        }
    });

    const copyIconSVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
    const checkIconSVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(shortLinkUrl.href).then(() => {
            copyBtn.innerHTML = checkIconSVG;
            copyBtn.style.color = '#10B981';
            showToast('Link copied to clipboard', 'success');
            setTimeout(() => {
                copyBtn.innerHTML = copyIconSVG;
                copyBtn.style.color = 'var(--text-muted)';
            }, 2000);
        });
    });

    newLinkBtn.addEventListener('click', () => {
        resultSection.classList.add('hidden');
        document.getElementById('qr-code-container').classList.add('hidden');
        form.classList.remove('hidden');
        urlInput.value = '';
        customCodeInput.value = '';
        titleInput.value = '';
        urlInput.focus();
    });

    function deleteLink(code) {
        if (!confirm(`Delete short link "${code}" from your portfolio?`)) return;

        fetch(`/api/links/${code}`, {
            method: 'DELETE',
            headers: headers()
        })
            .then(r => {
                if (handle401(r)) return;
                if (!r.ok) throw new Error('Failed to delete');
                showToast('Link removed from portfolio', 'success');
                loadLinks();
            })
            .catch(err => showToast(err.message, 'error'));
    }

    function openEditModal(code, url, title, showOnTree) {
        currentEditCode = code;
        editUrlInput.value = url;
        editTitleInput.value = title;
        editShowTreeCheck.checked = showOnTree;
        editModal.classList.remove('hidden');
        editUrlInput.focus();
    }

    function closeEditModal() {
        editModal.classList.add('hidden');
        currentEditCode = null;
        editUrlInput.value = '';
        editTitleInput.value = '';
    }

    cancelEditBtn.addEventListener('click', closeEditModal);

    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newUrl = editUrlInput.value.trim();
        if (!newUrl || !currentEditCode) return;

        const saveBtn = document.getElementById('save-edit-btn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Saving...';
        saveBtn.disabled = true;

        try {
            const payload = {
                original_url: newUrl,
                title: editTitleInput.value.trim(),
                show_on_tree: editShowTreeCheck.checked
            };

            const r = await fetch(`/api/links/${currentEditCode}`, {
                method: 'PUT',
                headers: headers(),
                body: JSON.stringify(payload)
            });

            if (handle401(r)) return;
            
            const data = await r.json();
            if (!r.ok) throw new Error(data.error?.message || data.detail || 'Failed to update link');

            showToast('Link updated successfully', 'success');
            closeEditModal();
            loadLinks();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }
    });

    // --- Init ---
    if (getPassword()) {
        showDashboard();
    } else {
        showLanding();
    }
});
