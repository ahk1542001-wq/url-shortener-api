document.addEventListener('DOMContentLoaded', () => {
    // --- UI Views ---
    const landingView = document.getElementById('landing-view');
    const loginView = document.getElementById('login-view');
    const dashboardView = document.getElementById('dashboard-view');
    const mainDock = document.getElementById('main-dock');
    const headerSubtitle = document.getElementById('header-subtitle');

    // --- Navbar Elements ---
    const navLoginBtn = document.getElementById('nav-login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const backToHomeBtn = document.getElementById('back-to-home-btn');

    // --- Login Elements ---
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const passwordBtn = document.getElementById('password-btn');
    const passwordError = document.getElementById('password-error');
    const togglePassword = document.getElementById('toggle-password');

    // --- Dashboard Tabs ---
    const tabBtns = document.querySelectorAll('.dock-btn[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');

    // --- Link Form Elements ---
    const form = document.getElementById('shorten-form');
    const urlInput = document.getElementById('url');
    const titleInput = document.getElementById('title');
    const customCodeInput = document.getElementById('custom_code');
    const linkModeInput = document.getElementById('link-mode'); // Not used anymore but keep for now
    const titleGroup = document.getElementById('title-group');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('span');
    const loadingContainer = document.getElementById('loading-container');
    const loadingText = document.getElementById('loading-text');

    const showOnTreeCheck = document.getElementById('show_on_tree');
    
    // Toggle title field visibility based on checkbox
    if (showOnTreeCheck) {
        showOnTreeCheck.addEventListener('change', () => {
            if (showOnTreeCheck.checked) {
                titleGroup.classList.remove('hidden');
                titleInput.required = true;
            } else {
                titleGroup.classList.add('hidden');
                titleInput.required = false;
                titleInput.value = ''; // clear when hiding
            }
        });
    }

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

    function getToken() {
        return localStorage.getItem('swoosh_token') || '';
    }

    function headers() {
        const h = { 'Content-Type': 'application/json' };
        const token = getToken();
        if (token) h['Authorization'] = `Bearer ${token}`;
        const ap = localStorage.getItem('swoosh_active_profile');
        if (ap) h['X-Active-Profile'] = ap;
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
            localStorage.removeItem('swoosh_token');
            localStorage.removeItem('swoosh_role');
            showLanding();
            return true;
        }
        return false;
    }

    // --- View Routing ---
    const featureSelectionView = document.getElementById('feature-selection-view');
    const profileSelectionView = document.getElementById('profile-selection-view');
    const createProfileView = document.getElementById('create-profile-view');
    const adminView = document.getElementById('admin-view');
    const adminCreateUserView = document.getElementById('admin-create-user-view');
    
    let isStandaloneMode = false;

    function hideAllViews() {
        landingView.classList.add('hidden');
        loginView.classList.add('hidden');
        dashboardView.classList.add('hidden');
        if (featureSelectionView) featureSelectionView.classList.add('hidden');
        profileSelectionView.classList.add('hidden');
        createProfileView.classList.add('hidden');
        if (adminView) adminView.classList.add('hidden');
        if (adminCreateUserView) adminCreateUserView.classList.add('hidden');
        if (mainDock) mainDock.classList.add('hidden');
    }

    function showLanding() {
        hideAllViews();
        landingView.classList.remove('hidden');
        navLoginBtn.classList.remove('hidden');
        headerSubtitle.style.display = 'block';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'flex';
    }

    function showLogin() {
        hideAllViews();
        loginView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'block';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'flex';
        
        if (usernameInput) usernameInput.value = '';
        passwordInput.value = '';
        passwordError.classList.add('hidden');
        if (usernameInput) setTimeout(() => usernameInput.focus(), 100);
        else setTimeout(() => passwordInput.focus(), 100);
    }

    function showFeatureSelection() {
        hideAllViews();
        if(featureSelectionView) featureSelectionView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'block';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'flex';
    }

    function showDashboard() {
        if (!isStandaloneMode && !localStorage.getItem('swoosh_active_profile')) {
            showProfileSelection();
            return;
        }
        hideAllViews();
        dashboardView.classList.remove('hidden');
        if (mainDock) mainDock.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';

        if (isStandaloneMode) {
            document.querySelector('.dock-btn[data-tab="tree"]')?.classList.add('hidden');
            document.querySelector('.sidebar-btn[data-tab="tree"]')?.classList.add('hidden');
            document.getElementById('switch-profile-btn')?.classList.add('hidden');
            document.getElementById('sidebar-switch-profile')?.classList.add('hidden');
            document.getElementById('show-on-tree-container')?.classList.add('hidden');
            if (typeof switchTab === 'function') switchTab('links');
        } else {
            document.querySelector('.dock-btn[data-tab="tree"]')?.classList.remove('hidden');
            document.querySelector('.sidebar-btn[data-tab="tree"]')?.classList.remove('hidden');
            document.getElementById('switch-profile-btn')?.classList.remove('hidden');
            document.getElementById('sidebar-switch-profile')?.classList.remove('hidden');
            document.getElementById('show-on-tree-container')?.classList.remove('hidden');
        }

        loadDashboardData();
        loadLinks();
        loadAnalytics();
    }

    function showProfileSelection() {
        hideAllViews();
        profileSelectionView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';
        loadProfiles();
    }
    
    function showCreateProfile() {
        hideAllViews();
        createProfileView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';
    }
    
    function showAdminDashboard() {
        hideAllViews();
        adminView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';
        loadAdminUsers();
    }
    
    function showAdminCreateUser() {
        hideAllViews();
        adminCreateUserView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';
    }

    if (document.getElementById('admin-add-user-btn')) {
        document.getElementById('admin-add-user-btn').addEventListener('click', showAdminCreateUser);
    }
    if (document.getElementById('admin-cancel-user-btn')) {
        document.getElementById('admin-cancel-user-btn').addEventListener('click', showAdminDashboard);
    }
    if (document.getElementById('nav-admin-back')) {
        document.getElementById('nav-admin-back').addEventListener('click', showAdminDashboard);
    }
    
    const adminLogoutLinks = document.querySelectorAll('.logout-link');
    adminLogoutLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            logoutBtn.click();
        });
    });

    if (document.getElementById('admin-create-user-form')) {
        document.getElementById('admin-create-user-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const un = document.getElementById('new-user-username').value.trim();
            const pw = document.getElementById('new-user-password').value.trim();
            
            try {
                const r = await fetch('/api/admin/users', {
                    method: 'POST',
                    headers: headers(),
                    body: JSON.stringify({ username: un, password: pw })
                });
                if (handle401(r)) return;
                const data = await r.json();
                if(!r.ok) throw new Error(data.detail || data.error?.message || 'Failed to create user');
                
                showToast('User created successfully', 'success');
                showAdminDashboard();
            } catch (err) {
                const errDiv = document.getElementById('admin-create-user-error');
                errDiv.textContent = err.message;
                errDiv.classList.remove('hidden');
            }
        });
    }

    async function loadAdminUsers() {
        const list = document.getElementById('admin-users-list');
        list.innerHTML = '<p class="text-muted text-center">Loading users...</p>';
        try {
            const r = await fetch('/api/admin/users', { headers: headers() });
            if (handle401(r)) return;
            const data = await r.json();
            if (!r.ok) throw new Error('Failed to fetch users');
            
            if (data.users.length === 0) {
                list.innerHTML = '<p class="text-muted text-center">No users found.</p>';
                return;
            }
            
            list.innerHTML = data.users.map(u => `
                <div class="link-item" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="link-code">${escapeHtml(u.username)} <span style="font-size: 0.8rem; color: var(--text-muted);">(${u.profile_count} profiles)</span></div>
                        <div class="link-date">Created: ${escapeHtml(u.created_at)}</div>
                    </div>
                </div>
            `).join('');
        } catch(err) {
            list.innerHTML = '<p class="text-muted text-center">Error loading users</p>';
        }
    }
    
    document.getElementById('switch-profile-btn').addEventListener('click', () => {
        localStorage.removeItem('swoosh_active_profile');
        showProfileSelection();
    });

    const altLogoutBtn = document.getElementById('alt-logout-btn');
    if (altLogoutBtn) {
        altLogoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logoutBtn.click();
        });
    }
    
    document.getElementById('add-profile-btn').addEventListener('click', showCreateProfile);
    document.getElementById('cancel-create-profile-btn').addEventListener('click', () => {
        if(window.appProfiles && window.appProfiles.length > 0) showProfileSelection();
        else showLanding();
    });

    // Feature Selection Listeners
    document.getElementById('select-standalone-feature')?.addEventListener('click', () => {
        isStandaloneMode = true;
        localStorage.removeItem('swoosh_active_profile');
        showDashboard();
    });

    document.getElementById('select-tree-feature')?.addEventListener('click', () => {
        isStandaloneMode = false;
        showProfileSelection();
    });

    document.getElementById('back-to-features-ps')?.addEventListener('click', (e) => {
        e.preventDefault();
        showFeatureSelection();
    });

    document.getElementById('back-features-dock-btn')?.addEventListener('click', () => {
        showFeatureSelection();
    });

    document.getElementById('fs-logout-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        logoutBtn.click();
    });
    
    // Create Profile Form
    document.getElementById('create-profile-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('new-profile-username').value.trim();
        if(!username) return;
        
        try {
            const r = await fetch('/api/profiles', {
                method: 'POST',
                headers: headers(),
                body: JSON.stringify({ username })
            });
            if (handle401(r)) return;
            const data = await r.json();
            if(!r.ok) throw new Error(data.detail || data.error?.message || 'Failed to create profile');
            
            showToast('Profile created successfully', 'success');
            localStorage.setItem('swoosh_active_profile', username);
            showDashboard();
        } catch (err) {
            const errDiv = document.getElementById('create-profile-error');
            errDiv.textContent = err.message;
            errDiv.classList.remove('hidden');
        }
    });
    
    async function loadProfiles() {
        const grid = document.getElementById('profiles-grid');
        grid.innerHTML = '<p class="text-muted">Loading profiles...</p>';
        try {
            const r = await fetch('/api/profiles', {
                method: 'GET',
                headers: headers()
            });
            if (handle401(r)) return;
            const data = await r.json();
            if (!r.ok) throw new Error('Failed to fetch profiles');
            
            window.appProfiles = data.profiles;
            
            if (data.profiles.length === 0) {
                showCreateProfile();
                return;
            }
            
            if (data.profiles.length >= 5) {
                document.getElementById('add-profile-btn').style.display = 'none';
                const limitMsg = document.createElement('p');
                limitMsg.style.color = 'var(--text-muted)';
                limitMsg.style.fontSize = '0.9rem';
                limitMsg.textContent = 'Maximum profile limit (5) reached.';
                grid.parentNode.insertBefore(limitMsg, grid.nextSibling);
            } else {
                document.getElementById('add-profile-btn').style.display = 'inline-block';
            }
            
            grid.innerHTML = data.profiles.map(p => `
                <div class="profile-card" data-username="${escapeHtml(p.username)}">
                    <div class="profile-avatar">${escapeHtml(p.username.charAt(0).toUpperCase())}</div>
                    <div class="profile-name">${escapeHtml(p.username)}</div>
                </div>
            `).join('');
            
            document.querySelectorAll('.profile-card').forEach(card => {
                card.addEventListener('click', () => {
                    localStorage.setItem('swoosh_active_profile', card.dataset.username);
                    showDashboard();
                });
            });
            
        } catch (err) {
            console.error(err);
            grid.innerHTML = '<p class="text-muted">Error loading profiles</p>';
        }
    }


    navLoginBtn.addEventListener('click', showLogin);
    backToHomeBtn.addEventListener('click', showLanding);

    // Sidebar specific listeners
    const sidebarBackFeatures = document.getElementById('sidebar-back-features');
    if(sidebarBackFeatures) sidebarBackFeatures.addEventListener('click', () => {
        document.getElementById('back-features-dock-btn')?.click();
    });
    
    const sidebarSwitchProfile = document.getElementById('sidebar-switch-profile');
    if(sidebarSwitchProfile) sidebarSwitchProfile.addEventListener('click', () => {
        document.getElementById('switch-profile-btn')?.click();
    });
    
    const sidebarLogout = document.getElementById('sidebar-logout');
    if(sidebarLogout) sidebarLogout.addEventListener('click', () => {
        document.getElementById('logout-btn')?.click();
    });

    // --- Tabs Logic ---
    const allTabBtns = document.querySelectorAll('.dock-btn[data-tab], .sidebar-btn[data-tab]');
    
    function switchTab(tabId) {
        allTabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.add('hidden'));
        
        document.querySelectorAll(`.dock-btn[data-tab="${tabId}"], .sidebar-btn[data-tab="${tabId}"]`).forEach(b => b.classList.add('active'));
        const targetId = `tab-${tabId}`;
        const targetEl = document.getElementById(targetId);
        if(targetEl) targetEl.classList.remove('hidden');
    }

    allTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // --- Auth Logic ---
    passwordBtn.addEventListener('click', async () => {
        const un = usernameInput ? usernameInput.value.trim() : '';
        const pw = passwordInput.value.trim();
        if (!un || !pw) {
            showToast('Please enter username and password', 'error');
            return;
        }

        const originalText = passwordBtn.querySelector('span').textContent;
        passwordBtn.querySelector('span').textContent = "Authenticating...";
        passwordBtn.disabled = true;

        try {
            const r = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: un, password: pw })
            });
            if (r.status === 401) {
                showToast('Incorrect credentials', 'error');
                return;
            }
            if (!r.ok) {
                showToast('Server connection failed', 'error');
                return;
            }
            
            const data = await r.json();

            localStorage.setItem('swoosh_token', data.token);
            localStorage.setItem('swoosh_role', data.role);
            localStorage.removeItem('swoosh_active_profile'); // Clear previous profile on login
            showToast('Authentication successful', 'success');
            
            if (data.role === 'admin') {
                showAdminDashboard();
            } else {
                // If it's a normal user, pre-load profiles from login payload or fetch them.
                window.appProfiles = data.profiles || [];
                showFeatureSelection();
            }
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
        localStorage.removeItem('swoosh_token');
        localStorage.removeItem('swoosh_role');
        localStorage.removeItem('swoosh_active_profile');
        if (document.getElementById('switch-profile-btn')) {
            document.getElementById('switch-profile-btn').classList.add('hidden');
        }
        showLanding();
        showToast('Logged out successfully', 'success');
    });

    // --- Data Loading ---
    let currentUsername = '';
    let qrCodeInstance = null;

    async function loadDashboardData() {
        try {
            const r = await fetch('/api/me', { headers: headers() });
            if (handle401(r)) return;
            if (!r.ok) throw new Error('Failed to load profile data');
            const data = await r.json();
            
            currentUsername = data.username;
            
            const myTreeUrl = `${window.location.origin}/u/${data.username}`;
            const myTreeLink = document.getElementById('my-tree-url');
            myTreeLink.href = myTreeUrl;
            myTreeLink.textContent = `swoo.sh/u/${data.username}`;
            
            document.getElementById('view-tree-btn').href = myTreeUrl;
            document.getElementById('tree-views-count').textContent = data.tree_views;
            
            // Populate profile form
            document.getElementById('profile-username').value = data.username;
            if (data.bio) {
                document.getElementById('profile-bio').value = data.bio;
            }
            
            // Populate Social Links
            const socialContainer = document.getElementById('social-links-list');
            socialContainer.innerHTML = '';
            if (data.social_links && data.social_links.length > 0) {
                data.social_links.forEach(link => {
                    renderSocialLinkRow(link.platform, link.url);
                });
            }
            
            // Generate QR Code
            generateQRCode(myTreeUrl);
            
            document.getElementById('copy-tree-btn').onclick = () => {
                navigator.clipboard.writeText(myTreeUrl).then(() => {
                    showToast('Link Tree URL copied', 'success');
                });
            };
        } catch (err) {
            console.error(err);
        }
    }

    // --- QR Code ---
    function generateQRCode(url) {
        const qrContainer = document.getElementById('tree-qr-code');
        qrContainer.innerHTML = '';
        qrCodeInstance = new QRCode(qrContainer, {
            text: url,
            width: 180,
            height: 180,
            colorDark: '#1C1917',
            colorLight: '#FFFFFF',
            correctLevel: QRCode.CorrectLevel.H
        });

        // Download QR button
        setTimeout(() => {
            const downloadBtn = document.getElementById('download-qr-btn');
            downloadBtn.onclick = () => {
                const canvas = qrContainer.querySelector('canvas');
                if (canvas) {
                    const link = document.createElement('a');
                    link.download = `qr-${currentUsername}.png`;
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                    showToast('QR Code downloaded', 'success');
                }
            };
        }, 300);
    }

    // --- Username Change Warning ---
    const profileUsernameInput = document.getElementById('profile-username');
    const usernameWarning = document.getElementById('username-warning');
    const oldUsernameDisplay = document.getElementById('old-username-display');

    profileUsernameInput.addEventListener('input', () => {
        const newVal = profileUsernameInput.value.trim().toLowerCase();
        if (newVal !== currentUsername && currentUsername) {
            oldUsernameDisplay.textContent = currentUsername;
            usernameWarning.classList.remove('hidden');
        } else {
            usernameWarning.classList.add('hidden');
        }
    });

    // --- Social Links UI ---
    function renderSocialLinkRow(platform = 'twitter', url = '') {
        const container = document.getElementById('social-links-list');
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.gap = '0.5rem';
        row.style.alignItems = 'center';
        
        const select = document.createElement('select');
        select.style.padding = '0.6rem';
        select.style.borderRadius = '8px';
        select.style.border = '1px solid #E7E5E4';
        select.style.background = '#FFFFFF';
        select.className = 'social-platform-select';
        
        const platforms = ['twitter', 'instagram', 'linkedin', 'github', 'website', 'other'];
        platforms.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p;
            opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
            if (p === platform) opt.selected = true;
            select.appendChild(opt);
        });
        
        const input = document.createElement('input');
        input.type = 'url';
        input.placeholder = 'https://...';
        input.value = url;
        input.className = 'social-url-input';
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'icon-btn';
        removeBtn.style.color = '#EF4444';
        removeBtn.innerHTML = '✕';
        removeBtn.title = 'Remove link';
        removeBtn.onclick = () => row.remove();
        
        row.appendChild(select);
        row.appendChild(input);
        row.appendChild(removeBtn);
        
        container.appendChild(row);
    }

    document.getElementById('add-social-btn').addEventListener('click', () => {
        renderSocialLinkRow();
    });

    // --- Save Profile ---
    const saveProfileBtn = document.getElementById('save-profile-btn');
    saveProfileBtn.addEventListener('click', async () => {
        const newUsername = profileUsernameInput.value.trim().toLowerCase();
        const newBio = document.getElementById('profile-bio').value.trim();
        const profileError = document.getElementById('profile-error');
        profileError.classList.add('hidden');

        // Gather social links
        const socialRows = document.getElementById('social-links-list').children;
        const newSocialLinks = [];
        for (let row of socialRows) {
            const p = row.querySelector('.social-platform-select').value;
            const u = row.querySelector('.social-url-input').value.trim();
            if (u) {
                newSocialLinks.push({ platform: p, url: u });
            }
        }

        if (!newUsername || newUsername.length < 3) {
            showToast('Username must be at least 3 characters', 'error');
            return;
        }

        // Confirm if username changed
        if (newUsername !== currentUsername) {
            if (!confirm(`⚠️ Username ကို "${currentUsername}" ကနေ "${newUsername}" ကို ပြောင်းမှာ သေချာပါသလား? URL အဟောင်း (swoo.sh/u/${currentUsername}) က အလုပ်မလုပ်တော့ပါဘူး။`)) {
                return;
            }
        }

        const originalText = saveProfileBtn.querySelector('span').textContent;
        saveProfileBtn.querySelector('span').textContent = 'Saving...';
        saveProfileBtn.disabled = true;

        try {
            const r = await fetch('/api/me', {
                method: 'PUT',
                headers: headers(),
                body: JSON.stringify({ 
                    username: newUsername, 
                    bio: newBio || null,
                    social_links: newSocialLinks.length > 0 ? newSocialLinks : null
                })
            });

            if (handle401(r)) return;
            const data = await r.json();
            
            if (!r.ok) {
                throw new Error(data.error?.message || data.detail || 'Failed to update profile');
            }

            currentUsername = data.username;
            usernameWarning.classList.add('hidden');

            // Update displayed URL and QR
            const newTreeUrl = `${window.location.origin}/u/${data.username}`;
            const myTreeLink = document.getElementById('my-tree-url');
            myTreeLink.href = newTreeUrl;
            myTreeLink.textContent = `swoo.sh/u/${data.username}`;
            document.getElementById('view-tree-btn').href = newTreeUrl;
            
            generateQRCode(newTreeUrl);

            showToast('Profile updated successfully!', 'success');
        } catch (err) {
            showToast(err.message, 'error');
            profileError.textContent = err.message;
            profileError.classList.remove('hidden');
        } finally {
            saveProfileBtn.querySelector('span').textContent = originalText;
            saveProfileBtn.disabled = false;
        }
    });

    async function loadLinks() {
        try {
            const r = await fetch('/api/links', { headers: headers() });
            if (handle401(r)) return;
            if (!r.ok) throw new Error('Failed to load portfolio');

            const data = await r.json();

            if (!data.links || data.links.length === 0) {
                linksList.innerHTML = `
                    <div class="empty-state-illustrative">
                        <div class="icon">✨</div>
                        <h3>No Links Yet</h3>
                        <p>Your portfolio is empty. Create a magical link above to get started!</p>
                    </div>`;
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
    
    async function loadAnalytics() {
        const analyticsList = document.getElementById('analytics-list');
        if (!analyticsList) return;
        
        analyticsList.innerHTML = '<p class="text-muted" style="text-align: center; padding: 2rem 0;">Loading analytics...</p>';
        try {
            const r = await fetch('/api/analytics', { headers: headers() });
            if (handle401(r)) return;
            if (!r.ok) throw new Error('Failed to load analytics');

            const data = await r.json();

            if (!data.analytics || data.analytics.length === 0) {
                analyticsList.innerHTML = `
                    <div class="empty-state-illustrative">
                        <div class="icon">📊</div>
                        <h3>No Data Yet</h3>
                        <p>Share your links to see performance metrics appear here.</p>
                    </div>`;
                return;
            }

            analyticsList.innerHTML = data.analytics.map(link => {
                const maxClicks = Math.max(...link.daily.map(d => d.clicks), 1);
                const sparkline = link.daily.slice(-7).map(d => 
                    `<div style="display:inline-block; width: 8px; height: ${Math.max(4, (d.clicks / maxClicks) * 30)}px; background: var(--accent); margin: 0 2px; border-radius: 2px;" title="${d.date}: ${d.clicks} clicks"></div>`
                ).join('');
                
                return `
                    <div class="link-item" style="display:flex; flex-direction:column; gap: 0.5rem; padding-right:1rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                            <div class="link-info">
                                <div class="link-code">${escapeHtml(link.title)} <span style="font-size:0.8rem; color:var(--text-muted);">/${escapeHtml(link.short_code)}</span></div>
                            </div>
                            <div class="link-stats" style="font-size: 1.2rem; font-weight: 600; color: var(--primary);">
                                ${link.total_clicks} <span style="font-size:0.8rem; font-weight:400; color:var(--text-muted);">total</span>
                            </div>
                        </div>
                        <div style="display:flex; justify-content:flex-end; align-items:flex-end; height:30px; opacity:0.8;">
                            ${sparkline || '<span style="font-size:0.8rem; color:var(--text-muted);">No recent daily data</span>'}
                        </div>
                    </div>
                `;
            }).join('');
            
        } catch (err) {
            console.error('loadAnalytics failed:', err);
            analyticsList.innerHTML = '<div class="text-muted" style="text-align: center; padding: 2rem 0;">Failed to load analytics</div>';
        }
    }

    refreshLinksBtn.addEventListener('click', () => {
        loadLinks();
        loadAnalytics();
    });

    // --- Link Operations ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorMsg.classList.add('hidden');
        resultSection.classList.add('hidden');

        const url = urlInput.value.trim();
        const customCode = customCodeInput.value.trim();
        const title = titleInput.value.trim();
        const showOnTree = linkModeInput.value === 'tree';

        if(!url) return;
        if(showOnTree && !title) {
            errorMsg.textContent = 'Please provide a title for your Link Tree entry.';
            errorMsg.classList.remove('hidden');
            return;
        }

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

            const resultText = document.getElementById('result-message');
            
            let successMsg = '';
            if (data.already_exists) {
                successMsg = 'This link was already in your portfolio.';
            } else if (showOnTree) {
                successMsg = 'Success! Added to your Link Tree.';
            } else {
                successMsg = 'Success! Your short link is ready.';
            }
            
            resultText.textContent = successMsg;

            form.classList.add('hidden');
            resultSection.classList.remove('hidden');
            
            document.querySelector('.mode-toggle').classList.add('hidden');

            loadLinks();
            showToast(successMsg, 'success');

        } catch (err) {
            showToast(err.message, 'error');
            errorMsg.textContent = err.message;
            errorMsg.classList.remove('hidden');
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
        document.querySelector('.mode-toggle').classList.remove('hidden');
        errorMsg.classList.add('hidden');
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
    if (getToken()) {
        if (localStorage.getItem('swoosh_role') === 'admin') {
            showAdminDashboard();
        } else {
            if (localStorage.getItem('swoosh_active_profile')) {
                isStandaloneMode = false;
                showDashboard();
            } else {
                showFeatureSelection();
            }
        }
    } else {
        showLanding();
    }
});
