document.addEventListener('DOMContentLoaded', () => {
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    // --- UI Views ---
    const landingView = document.getElementById('landing-view');
    const loginView = document.getElementById('login-view');
    const dashboardView = document.getElementById('dashboard-view');
    const headerSubtitle = document.getElementById('header-subtitle');

    // --- Navbar Elements ---
    const navLoginBtn = document.getElementById('nav-login-btn');
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
    const customCodeInput = document.getElementById('custom_code');
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
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    let currentEditCode = null;
    let currentEditShowOnTree = false;

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
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function handle401(r) {
        if (r.status === 401) {
            logout(false);
            return true;
        }
        return false;
    }

    function getFriendlyErrorMessage(err) {
        const rawMessage = String(err?.message || '');
        if (rawMessage.includes('Cloud storage not configured') || rawMessage.includes('Avatar storage is not configured') || rawMessage.includes('Cloudinary config is absent') || rawMessage.includes('503')) {
            return 'Avatar storage is not configured';
        }
        if (err instanceof TypeError || rawMessage.includes('Cannot read') || rawMessage.includes('undefined') || rawMessage.includes('Failed to fetch')) {
            return 'An unexpected error occurred. Please try again.';
        }
        return rawMessage || 'An unexpected error occurred.';
    }

    function logout(showConfirmation = true) {
        localStorage.removeItem('swoosh_token');
        localStorage.removeItem('swoosh_role');
        localStorage.removeItem('swoosh_active_profile');
        localStorage.removeItem('swoosh_default_tab');
        showLanding();
        if (showConfirmation) showToast('Logged out successfully', 'success');
    }

    // --- View Routing ---
    const featureSelectionView = document.getElementById('feature-selection-view');
    const profileSelectionView = document.getElementById('profile-selection-view');
    const createProfileView = document.getElementById('create-profile-view');
    const adminView = document.getElementById('admin-view');
    const adminCreateUserView = document.getElementById('admin-create-user-view');

    let isStandaloneMode = false;

    function hideAllViews() {
        window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0, behavior: 'auto' }));
        landingView.classList.add('hidden');
        loginView.classList.add('hidden');
        dashboardView.classList.add('hidden');
        if (featureSelectionView) featureSelectionView.classList.add('hidden');
        if (profileSelectionView) profileSelectionView.classList.add('hidden');
        createProfileView.classList.add('hidden');
        if (adminView) adminView.classList.add('hidden');
        if (adminCreateUserView) adminCreateUserView.classList.add('hidden');

        // Hide top sticky nav by default
        document.getElementById('main-top-nav')?.classList.add('hidden');
        document.body.classList.remove('top-nav-visible');
        document.body.classList.remove('profile-picker-visible');
        document.body.classList.remove('landing-visible');
    }

    function showLanding() {
        hideAllViews();
        landingView.classList.remove('hidden');
        document.body.classList.add('landing-visible');
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
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';

        // Show sticky top nav on mobile
        document.getElementById('main-top-nav')?.classList.remove('hidden');
        document.body.classList.add('top-nav-visible');

        if (isStandaloneMode) {
            // Hide tree and profile tabs from sidebar/dock
            document.querySelectorAll('[data-tab="tree"]').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[data-tab="profile"]').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[data-tab="links"]').forEach(el => el.classList.remove('hidden'));
            document.getElementById('sidebar-switch-profile')?.classList.add('hidden');

            // Show shortener menu in top nav
            document.getElementById('top-nav-shortener')?.classList.remove('hidden');
            document.getElementById('top-nav-tree')?.classList.add('hidden');
            document.getElementById('top-nav-admin')?.classList.add('hidden');

            switchTab('links');
        } else {
            // Hide links tab from sidebar/dock
            document.querySelectorAll('[data-tab="links"]').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[data-tab="tree"]').forEach(el => el.classList.remove('hidden'));
            document.querySelectorAll('[data-tab="profile"]').forEach(el => el.classList.remove('hidden'));
            document.getElementById('sidebar-switch-profile')?.classList.remove('hidden');

            // Show tree menu in top nav
            document.getElementById('top-nav-shortener')?.classList.add('hidden');
            document.getElementById('top-nav-tree')?.classList.remove('hidden');
            document.getElementById('top-nav-admin')?.classList.add('hidden');

            const defaultTab = localStorage.getItem('swoosh_default_tab') || 'tree';
            switchTab(defaultTab);
            localStorage.removeItem('swoosh_default_tab');
        }

        if (isStandaloneMode) {
            loadLinks();
        } else {
            loadDashboardData();
        }
        loadAnalytics();
    }

    function showCreateProfile() {
        hideAllViews();
        createProfileView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';
    }

    function showProfileSelection() {
        hideAllViews();
        profileSelectionView?.classList.remove('hidden');
        document.body.classList.add('profile-picker-visible');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';
        loadProfiles();
    }

    function showAdminDashboard() {
        hideAllViews();
        adminView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';

        // Show sticky top nav and admin menu
        document.getElementById('main-top-nav')?.classList.remove('hidden');
        document.body.classList.add('top-nav-visible');
        document.getElementById('top-nav-shortener')?.classList.add('hidden');
        document.getElementById('top-nav-tree')?.classList.add('hidden');
        document.getElementById('top-nav-admin')?.classList.remove('hidden');

        // Show Users button and hide Back button in top-nav-admin
        document.getElementById('top-nav-admin-users')?.classList.remove('hidden');
        document.getElementById('top-nav-admin-back')?.classList.add('hidden');

        loadAdminUsers();
    }

    function showAdminCreateUser() {
        hideAllViews();
        adminCreateUserView.classList.remove('hidden');
        navLoginBtn.classList.add('hidden');
        headerSubtitle.style.display = 'none';
        const mainHeader = document.getElementById('main-header');
        if (mainHeader) mainHeader.style.display = 'none';

        // Show sticky top nav and admin menu
        document.getElementById('main-top-nav')?.classList.remove('hidden');
        document.body.classList.add('top-nav-visible');
        document.getElementById('top-nav-shortener')?.classList.add('hidden');
        document.getElementById('top-nav-tree')?.classList.add('hidden');
        document.getElementById('top-nav-admin')?.classList.remove('hidden');

        // Hide Users button and show Back button in top-nav-admin
        document.getElementById('top-nav-admin-users')?.classList.add('hidden');
        document.getElementById('top-nav-admin-back')?.classList.remove('hidden');
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
            logout();
        });
    });

    if (document.getElementById('admin-create-user-form')) {
        const adminForm = document.getElementById('admin-create-user-form');
        adminForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const unInput = document.getElementById('new-user-username');
            const pwInput = document.getElementById('new-user-password');
            const errDiv = document.getElementById('admin-create-user-error');
            const submitBtn = adminForm.querySelector('button[type="submit"]');

            const un = unInput.value.trim();
            const pw = pwInput.value.trim();

            if (!un || !pw) {
                errDiv.textContent = 'Please provide both username and password';
                errDiv.classList.remove('hidden');
                return;
            }

            errDiv.classList.add('hidden');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating...';
            submitBtn.disabled = true;
            unInput.disabled = true;
            pwInput.disabled = true;

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
                unInput.value = '';
                pwInput.value = '';
                showAdminDashboard();
            } catch (err) {
                errDiv.textContent = err.message;
                errDiv.classList.remove('hidden');
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
                unInput.disabled = false;
                pwInput.disabled = false;
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

    document.getElementById('cancel-create-profile-btn').addEventListener('click', () => {
        if (window.appProfiles?.length) showProfileSelection();
        else showFeatureSelection();
    });

    // Feature Selection Listeners
    document.getElementById('select-standalone-feature')?.addEventListener('click', () => {
        isStandaloneMode = true;
        localStorage.removeItem('swoosh_active_profile');
        showDashboard();
    });

    document.getElementById('select-tree-feature')?.addEventListener('click', () => {
        isStandaloneMode = false;
        localStorage.setItem('swoosh_default_tab', 'tree');
        showProfileSelection();
    });

    document.getElementById('fs-logout-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        logout();
    });

    async function loadProfiles() {
        try {
            const r = await fetch('/api/profiles', {
                method: 'GET',
                headers: headers()
            });
            if (handle401(r)) return;
            const data = await r.json();
            if (!r.ok) throw new Error('Failed to fetch profiles');

            window.appProfiles = data.profiles;
            const maxProfiles = data.max_profiles || 5;

            if (data.profiles.length === 0) {
                showCreateProfile();
                return;
            }

            const countBadge = document.getElementById('profile-count-badge');
            const addButton = document.getElementById('add-profile-btn');
            const limitMessage = document.getElementById('profile-limit-message');
            const profilesGrid = document.getElementById('profiles-grid');
            const atLimit = data.profiles.length >= maxProfiles;

            countBadge.textContent = `${data.profiles.length} / ${maxProfiles}`;
            addButton.disabled = atLimit;
            addButton.classList.toggle('hidden', atLimit);
            limitMessage.classList.toggle('hidden', !atLimit);
            profilesGrid.replaceChildren();

            data.profiles.forEach(profile => {
                const card = document.createElement('button');
                card.type = 'button';
                card.className = 'profile-card';
                card.setAttribute('aria-label', `Open ${profile.username} Link Tree profile`);

                const avatar = document.createElement('span');
                avatar.className = 'profile-avatar';
                if (profile.avatar_url) {
                    const image = document.createElement('img');
                    image.src = profile.avatar_url;
                    image.alt = '';
                    avatar.appendChild(image);
                } else {
                    avatar.textContent = profile.username.charAt(0).toUpperCase();
                }

                const name = document.createElement('span');
                name.className = 'profile-name';
                name.textContent = profile.username;

                const views = document.createElement('span');
                views.className = 'profile-views';
                views.textContent = `${profile.tree_views || 0} views`;

                card.append(avatar, name, views);
                card.addEventListener('click', () => {
                    localStorage.setItem('swoosh_active_profile', profile.username);
                    localStorage.setItem('swoosh_default_tab', 'tree');
                    showDashboard();
                });
                profilesGrid.appendChild(card);
            });
        } catch (err) {
            console.error(err);
            showToast(err.message, 'error');
        }
    }

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
            document.getElementById('new-profile-username').value = '';
            document.getElementById('create-profile-error').classList.add('hidden');
            localStorage.setItem('swoosh_active_profile', data.username);
            showDashboard();
        } catch (err) {
            const errDiv = document.getElementById('create-profile-error');
            errDiv.textContent = err.message;
            errDiv.classList.remove('hidden');
        }
    });

    navLoginBtn.addEventListener('click', showLogin);
    backToHomeBtn.addEventListener('click', showLanding);

    // Sidebar specific listeners
    const sidebarBackFeatures = document.getElementById('sidebar-back-features');
    if(sidebarBackFeatures) sidebarBackFeatures.addEventListener('click', () => {
        showFeatureSelection();
    });

    document.querySelectorAll('.switch-profile-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            localStorage.removeItem('swoosh_active_profile');
            showProfileSelection();
        });
    });

    document.getElementById('back-to-features-ps')?.addEventListener('click', showFeatureSelection);
    document.getElementById('add-profile-btn')?.addEventListener('click', showCreateProfile);
    document.getElementById('alt-logout-btn')?.addEventListener('click', () => logout());

    const sidebarLogout = document.getElementById('sidebar-logout');
    if(sidebarLogout) sidebarLogout.addEventListener('click', () => logout());

    document.querySelectorAll('.back-features-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            showFeatureSelection();
        });
    });

    document.querySelectorAll('.top-nav-logout').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });

    document.getElementById('top-nav-admin-users')?.addEventListener('click', showAdminDashboard);
    document.getElementById('top-nav-admin-back')?.addEventListener('click', showAdminDashboard);

    // --- Tabs Logic ---
    const allTabBtns = document.querySelectorAll('.dock-btn[data-tab], .sidebar-btn[data-tab], .top-nav-btn[data-tab]');

    function switchTab(tabId) {
        allTabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.add('hidden'));

        document.querySelectorAll(`.dock-btn[data-tab="${tabId}"], .sidebar-btn[data-tab="${tabId}"], .top-nav-btn[data-tab="${tabId}"]`).forEach(b => b.classList.add('active'));
        const targetId = `tab-${tabId}`;
        const targetEl = document.getElementById(targetId);
        if(targetEl) targetEl.classList.remove('hidden');
    }

    function selectTab(tabId) {
        switchTab(tabId);
        if (tabId === 'analytics') loadAnalytics();
        if (tabId === 'links' && isStandaloneMode) loadLinks();
        if ((tabId === 'tree' || tabId === 'profile') && !isStandaloneMode) {
            loadDashboardData();
        }
    }

    allTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            selectTab(btn.dataset.tab);
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

    // --- Data Loading ---
    let currentUsername = '';
    let qrCodeInstance = null;
    let modalQrFilename = 'swoosh-link-qr.png';

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

            const avatarPreview = document.getElementById('avatar-preview');
            const avatarPlaceholder = document.getElementById('avatar-placeholder');
            if (data.avatar_url) {
                avatarPreview.src = data.avatar_url;
                avatarPreview.style.display = 'block';
                avatarPlaceholder.style.display = 'none';
            } else {
                avatarPreview.style.display = 'none';
                avatarPlaceholder.style.display = 'block';
            }

            // Populate Social Links
            const socialContainer = document.getElementById('social-links-list');
            socialContainer.innerHTML = '';
            if (data.social_links && data.social_links.length > 0) {
                data.social_links.forEach(link => {
                    renderSocialLinkRow(link.platform, link.url, link.title);
                });
            } else {
                // Add one empty row by default
                renderSocialLinkRow();
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
            colorDark: '#2F3A1D',
            colorLight: '#FFFFFF',
            correctLevel: QRCode.CorrectLevel.H
        });

        document.getElementById('download-qr-btn').onclick = () => {
            downloadQrCanvas(qrContainer, `qr-${currentUsername}.png`);
        };
    }

    function downloadQrCanvas(container, filename) {
        const canvas = container.querySelector('canvas');
        if (!canvas) {
            showToast('QR code is not ready yet', 'error');
            return;
        }
        const link = document.createElement('a');
        link.download = filename;
        link.href = canvas.toDataURL('image/png');
        link.click();
        showToast('QR Code downloaded', 'success');
    }

    const qrModal = document.getElementById('qr-modal');
    document.getElementById('close-qr-modal-btn').addEventListener('click', () => {
        qrModal.classList.add('hidden');
    });
    document.getElementById('download-modal-qr-btn').addEventListener('click', () => {
        downloadQrCanvas(document.getElementById('modal-qr-code'), modalQrFilename);
    });
    qrModal.addEventListener('click', (event) => {
        if (event.target === qrModal) qrModal.classList.add('hidden');
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') qrModal.classList.add('hidden');
    });

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

    // --- Avatar Upload Logic ---
    const avatarUpload = document.getElementById('avatar-upload');
    if (avatarUpload) {
        avatarUpload.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const statusLabel = document.getElementById('avatar-upload-status');
            const uploadBtn = document.querySelector('button[onclick*="avatar-upload"]');

            // Backup current visual state
            const avatarPreview = document.getElementById('avatar-preview');
            const avatarPlaceholder = document.getElementById('avatar-placeholder');
            const originalSrc = avatarPreview.src;
            const originalDisplay = avatarPreview.style.display;
            const originalPlaceholderDisplay = avatarPlaceholder.style.display;

            statusLabel.textContent = 'Uploading...';
            statusLabel.style.display = 'block';
            statusLabel.classList.remove('status-success', 'status-error');

            // Disable input and button
            avatarUpload.disabled = true;
            if (uploadBtn) uploadBtn.disabled = true;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/profiles/avatar', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('swoosh_token')}`,
                        'X-Active-Profile': localStorage.getItem('swoosh_active_profile') || ''
                    },
                    body: formData
                });

                if (handle401(res)) return;
                const data = await res.json();

                if (!res.ok) {
                    throw new Error(
                        data.error?.message || data.detail || 'Upload failed'
                    );
                }

                statusLabel.textContent = 'Upload successful!';
                statusLabel.classList.add('status-success');

                // Immediately show preview
                avatarPreview.src = data.avatar_url;
                avatarPreview.style.display = 'block';
                avatarPlaceholder.style.display = 'none';

                setTimeout(() => { statusLabel.style.display = 'none'; }, 3000);
            } catch (err) {
                console.error(err);
                statusLabel.textContent = getFriendlyErrorMessage(err);
                statusLabel.classList.add('status-error');

                // Restore original state
                avatarPreview.src = originalSrc;
                avatarPreview.style.display = originalDisplay;
                avatarPlaceholder.style.display = originalPlaceholderDisplay;
            } finally {
                avatarUpload.disabled = false;
                if (uploadBtn) uploadBtn.disabled = false;
                avatarUpload.value = ''; // Reset input selection
            }
        });
    }

    // --- Social Links UI ---
    function renderSocialLinkRow(platform = 'website', url = '', title = '') {
        const container = document.getElementById('social-links-list');
        const row = document.createElement('div');
        row.className = 'social-link-row-container';

        // Platform Select Group
        const platformGroup = document.createElement('div');
        platformGroup.className = 'social-field-group';
        const platformLabel = document.createElement('label');
        platformLabel.textContent = 'Platform';
        const select = document.createElement('select');
        select.className = 'social-platform-select';
        select.setAttribute('aria-label', 'Platform');

        const platforms = ['twitter', 'instagram', 'linkedin', 'github', 'facebook', 'youtube', 'tiktok', 'website', 'other'];
        platforms.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p;
            opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
            if (p === platform) opt.selected = true;
            select.appendChild(opt);
        });
        platformGroup.appendChild(platformLabel);
        platformGroup.appendChild(select);

        // Title Input Group
        const titleGroup = document.createElement('div');
        titleGroup.className = 'social-field-group';
        const titleLabel = document.createElement('label');
        titleLabel.textContent = 'Title (Optional)';
        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.placeholder = 'e.g. My Portfolio';
        titleInput.value = title || '';
        titleInput.className = 'social-title-input';
        titleInput.setAttribute('aria-label', 'Link Title');
        titleGroup.appendChild(titleLabel);
        titleGroup.appendChild(titleInput);

        // URL Input Group
        const urlGroup = document.createElement('div');
        urlGroup.className = 'social-field-group url-group';
        const urlLabel = document.createElement('label');
        urlLabel.textContent = 'Profile URL';
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'https://...';
        input.value = url || '';
        input.className = 'social-url-input';
        input.setAttribute('aria-label', 'Profile URL');
        urlGroup.appendChild(urlLabel);
        urlGroup.appendChild(input);

        // Delete Button
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'social-remove-btn';
        removeBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
        `;
        removeBtn.title = 'Remove Row';
        removeBtn.setAttribute('aria-label', 'Remove Row');
        removeBtn.onclick = () => row.remove();

        row.appendChild(platformGroup);
        row.appendChild(titleGroup);
        row.appendChild(urlGroup);
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
            const t = row.querySelector('.social-title-input').value.trim();
            if (p && u) {
                newSocialLinks.push({ platform: p, url: u, title: t });
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
            localStorage.setItem('swoosh_active_profile', data.username);
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

                const displayTitle = escapeHtml(link.title || link.original_url);

                return `
                    <div class="link-item" id="portfolio-link-${escapeHtml(link.short_code)}">
                        <div class="link-info">
                            <div class="link-code">${escapeHtml(link.short_code)}</div>
                            <div class="link-url" title="${escapeHtml(link.original_url)}">${displayTitle}</div>
                        </div>
                        <div class="link-stats">
                            <div class="link-clicks">${link.click_count} clicks</div>
                            <div class="link-date">${lastAccessed}</div>
                        </div>
                        <div class="portfolio-actions-group" style="display:flex; align-items:center; gap: 0.25rem;">
                            <button class="qr-link-btn icon-btn" data-code="${escapeHtml(link.short_code)}" title="View QR Code" aria-label="View QR Code">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect><line x1="7" y1="17" x2="7" y2="17.01"></line><line x1="17" y1="17" x2="17" y2="17.01"></line><line x1="17" y1="7" x2="17" y2="7.01"></line><line x1="7" y1="7" x2="7" y2="7.01"></line></svg>
                            </button>
                            <button class="copy-link-btn icon-btn" data-code="${escapeHtml(link.short_code)}" title="Copy Link" aria-label="Copy Link">
                                ${copyIconSVG}
                            </button>
                            <a class="open-link-btn icon-btn" href="${window.location.origin}/${escapeHtml(link.short_code)}" target="_blank" rel="noopener noreferrer" title="Open Link" aria-label="Open Link" style="display:inline-flex; align-items:center; justify-content:center; padding: 0.5rem; color: var(--text-muted);">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                            </a>
                            <button class="edit-btn icon-btn" data-code="${escapeHtml(link.short_code)}" data-url="${escapeHtml(link.original_url)}" data-title="${escapeHtml(link.title || '')}" data-show-on-tree="${Boolean(link.show_on_tree)}" title="Edit Link" aria-label="Edit Link">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                            </button>
                            <button class="delete-btn icon-btn" data-code="${escapeHtml(link.short_code)}" title="Delete Link" aria-label="Delete Link">
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
                    openEditModal(
                        btn.dataset.code,
                        btn.dataset.url,
                        btn.dataset.title,
                        btn.dataset.showOnTree === 'true'
                    );
                });
            });

            document.querySelectorAll('.copy-link-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const fullUrl = `${window.location.origin}/${btn.dataset.code}`;
                    navigator.clipboard.writeText(fullUrl).then(() => {
                        btn.innerHTML = checkIconSVG;
                        btn.style.color = 'var(--accent)';
                        showToast('Link copied to clipboard', 'success');
                        setTimeout(() => {
                            btn.innerHTML = copyIconSVG;
                            btn.style.color = 'var(--text-muted)';
                        }, 2000);
                    });
                });
            });

            // Local QR Code Modal rendering
            document.querySelectorAll('.qr-link-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const code = btn.dataset.code;
                    const fullUrl = `${window.location.origin}/${code}`;
                    const modalQrCode = document.getElementById('modal-qr-code');
                    modalQrCode.innerHTML = ''; // clear old QR

                    new QRCode(modalQrCode, {
                        text: fullUrl,
                        width: 180,
                        height: 180
                    });

                    document.getElementById('modal-qr-link').textContent = fullUrl;

                    qrModal.classList.remove('hidden');
                    modalQrFilename = `qr-${code}.png`;
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

        const description = document.getElementById('analytics-description');
        description.textContent = isStandaloneMode
            ? 'Track engagement across your short links.'
            : 'Track visits to your public Link Tree.';

        analyticsList.innerHTML = '<p class="text-muted" style="text-align: center; padding: 2rem 0;">Loading analytics...</p>';
        try {
            if (isStandaloneMode) {
                // Shortener analytics: show only short-link clicks
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
                        <div class="link-item analytics-item" data-code="${escapeHtml(link.short_code)}" style="display:flex; flex-direction:column; gap: 0.5rem; padding-right:1rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(0,0,0,0.05); cursor: pointer;">
                            <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                                <div class="link-info">
                                    <div class="link-code">${escapeHtml(link.short_code)}</div>
                                </div>
                                <div class="link-stats" style="font-size: 1.2rem; font-weight: 600; color: var(--primary);">
                                    ${link.total_clicks} <span style="font-size:0.8rem; font-weight:400; color:var(--text-muted);">clicks</span>
                                </div>
                            </div>
                            <div style="display:flex; justify-content:flex-end; align-items:flex-end; height:30px; opacity:0.8;">
                                ${sparkline || '<span style="font-size:0.8rem; color:var(--text-muted);">No recent daily data</span>'}
                            </div>
                        </div>
                    `;
                }).join('');

                // Wire click handler to scroll/highlight the link in portfolio
                document.querySelectorAll('.analytics-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const code = item.dataset.code;
                        focusLinkInPortfolio(code);
                    });
                });

            } else {
                // Link Tree analytics
                const activeProfileUsername = localStorage.getItem('swoosh_active_profile');
                if (!activeProfileUsername) {
                    analyticsList.innerHTML = `<p class="text-muted text-center" style="padding: 2rem 0;">Create your Link Tree first</p>`;
                    return;
                }

                const profRes = await fetch('/api/profiles', { headers: headers() });
                if (handle401(profRes)) return;
                const profData = await profRes.json();
                const profile = profData.profiles.find(p => p.username === activeProfileUsername);

                if (!profile) {
                    analyticsList.innerHTML = `<p class="text-muted text-center" style="padding: 2rem 0;">Create your Link Tree first</p>`;
                    return;
                }

                const viewsText = profile.tree_views === 0 ? "0 Tree Views / No visits yet" : `${profile.tree_views} Tree Views`;
                const publicUrl = `${window.location.origin}/u/${profile.username}`;
                const socialLinkCount = (profile.social_links || []).length;

                const treeStatsHtml = `
                    <div class="glass-card" style="margin-bottom: 1.5rem; padding: 1.25rem;">
                        <h4 style="margin-bottom: 0.5rem; color: var(--accent);">Link Tree Overview</h4>
                        <div style="margin-bottom: 0.75rem;">
                            <span style="font-size: 0.9rem; color: var(--text-muted);">Public URL:</span>
                            <a href="${publicUrl}" target="_blank" rel="noopener noreferrer" style="display: block; font-weight: 600; color: var(--text); font-size: 1rem; word-break: break-all;">${publicUrl}</a>
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: var(--primary);">
                            ${viewsText}
                        </div>
                        <div style="margin-top: 0.5rem; color: var(--text-muted);">
                            ${socialLinkCount} social ${socialLinkCount === 1 ? 'link' : 'links'} published
                        </div>
                    </div>
                `;

                analyticsList.innerHTML = treeStatsHtml;
            }
        } catch (err) {
            console.error('loadAnalytics failed:', err);
            analyticsList.innerHTML = '<div class="text-muted" style="text-align: center; padding: 2rem 0;">Failed to load analytics</div>';
        }
    }

    function focusLinkInPortfolio(code) {
        switchTab('links');
        setTimeout(() => {
            const linkEl = document.getElementById(`portfolio-link-${code}`);
            if (linkEl) {
                linkEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                linkEl.classList.remove('highlight-pulse');
                void linkEl.offsetWidth; // trigger reflow
                linkEl.classList.add('highlight-pulse');
            }
        }, 100);
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

        if(!url) return;

        btnText.style.display = 'none';
        submitBtn.disabled = true;
        urlInput.disabled = true;
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
            const payload = {
                url: url,
                title: document.getElementById('link_title')?.value.trim() || null,
                show_on_tree: false
            };
            if (customCode) payload.custom_code = customCode;

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

            const qrCodeContainer = document.getElementById('qr-code-container');
            const qrContainer = document.getElementById('short-link-qr');
            qrContainer.innerHTML = '';
            new QRCode(qrContainer, {
                text: fullShortUrl,
                width: 150,
                height: 150
            });
            qrCodeContainer.classList.remove('hidden');

            const resultText = document.getElementById('result-message');
            let successMsg = 'Success! Your short link is ready.';
            resultText.textContent = successMsg;

            form.classList.add('hidden');
            resultSection.classList.remove('hidden');

            await loadLinks();
            await loadAnalytics();
            showToast(successMsg, 'success');

        } catch (err) {
            const message = getFriendlyErrorMessage(err);
            showToast(message, 'error');
            errorMsg.textContent = message;
            errorMsg.classList.remove('hidden');
        } finally {
            clearInterval(loadingInterval);
            btnText.style.display = 'block';
            loadingContainer.style.display = 'none';
            submitBtn.disabled = false;
            urlInput.disabled = false;
            customCodeInput.disabled = false;
        }
    });

    const copyIconSVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
    const checkIconSVG = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(shortLinkUrl.href).then(() => {
            copyBtn.innerHTML = checkIconSVG;
            copyBtn.style.color = 'var(--accent)';
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
        errorMsg.classList.add('hidden');
        urlInput.value = '';
        customCodeInput.value = '';
        const titleInput = document.getElementById('link_title');
        if (titleInput) titleInput.value = '';
        document.getElementById('short-link-qr').innerHTML = '';
        shortLinkUrl.removeAttribute('href');
        shortLinkUrl.textContent = '';
        errorMsg.textContent = '';
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
        currentEditShowOnTree = showOnTree;
        editUrlInput.value = url;
        const titleInput = document.getElementById('edit-title');
        if (titleInput) titleInput.value = title || '';
        editModal.classList.remove('hidden');
        editUrlInput.focus();
    }

    function closeEditModal() {
        editModal.classList.add('hidden');
        currentEditCode = null;
        currentEditShowOnTree = false;
        editUrlInput.value = '';
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
                title: document.getElementById('edit-title')?.value.trim() || null,
                show_on_tree: currentEditShowOnTree
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
