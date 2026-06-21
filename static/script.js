document.addEventListener('DOMContentLoaded', () => {
    const passwordCard = document.getElementById('password-card');
    const appCard = document.getElementById('app-card');
    const passwordInput = document.getElementById('password');
    const passwordBtn = document.getElementById('password-btn');
    const passwordError = document.getElementById('password-error');
    const togglePassword = document.getElementById('toggle-password');
    const logoutBtn = document.getElementById('logout-btn');
    const myLinksCard = document.getElementById('my-links-card');

    const form = document.getElementById('shorten-form');
    const urlInput = document.getElementById('url');
    const customCodeInput = document.getElementById('custom_code');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('span');
    const loader = document.getElementById('btn-loader');

    const errorMsg = document.getElementById('error-message');
    const resultSection = document.getElementById('result-section');
    const shortLinkUrl = document.getElementById('short-link-url');
    const copyBtn = document.getElementById('copy-btn');
    const newLinkBtn = document.getElementById('new-link-btn');

    const refreshLinksBtn = document.getElementById('refresh-links-btn');
    const linksList = document.getElementById('links-list');

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
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function handle401(r) {
        if (r.status === 401) {
            localStorage.removeItem('swoosh_password');
            location.reload();
            return true;
        }
        return false;
    }

    function showApp() {
        passwordCard.classList.add('hidden');
        appCard.classList.remove('hidden');
        myLinksCard.classList.remove('hidden');
        logoutBtn.classList.remove('hidden');
        loadLinks();
    }

    function showPasswordError(msg) {
        passwordError.textContent = msg;
        passwordError.classList.remove('hidden');
    }

    passwordBtn.addEventListener('click', async () => {
        const pw = passwordInput.value.trim();
        if (!pw) return showPasswordError('Please enter a password');

        try {
            const health = await fetch('/api/health');
            if (!health.ok) return showPasswordError('Server error');
        } catch {
            return showPasswordError('Server error');
        }

        const r = await fetch('/api/links', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json', 'X-Access-Password': pw }
        });
        if (r.status === 401) return showPasswordError('Wrong password');
        if (!r.ok) return showPasswordError('Server error');

        localStorage.setItem('swoosh_password', pw);
        passwordError.classList.add('hidden');
        showApp();
    });

    passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') passwordBtn.click();
    });

    togglePassword.addEventListener('click', () => {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        togglePassword.querySelector('.eye-open').classList.toggle('hidden', !isPassword);
        togglePassword.querySelector('.eye-closed').classList.toggle('hidden', isPassword);
        togglePassword.title = isPassword ? 'Hide password' : 'Show password';
    });

    if (getPassword()) showApp();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorMsg.classList.add('hidden');
        resultSection.classList.add('hidden');

        const url = urlInput.value.trim();
        const customCode = customCodeInput.value.trim();

        if(!url) return;

        btnText.style.display = 'none';
        loader.style.display = 'block';
        submitBtn.disabled = true;

        try {
            const payload = { url };
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

            const resultText = resultSection.querySelector('p');
            resultText.textContent = data.already_exists
                ? 'This URL was already shortened!'
                : 'Your short link is ready!';

            form.classList.add('hidden');
            resultSection.classList.remove('hidden');

            loadLinks();

        } catch (err) {
            errorMsg.textContent = err.message;
            errorMsg.classList.remove('hidden');
        } finally {
            btnText.style.display = 'block';
            loader.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(shortLinkUrl.href).then(() => {
            const originalIcon = copyBtn.textContent;
            copyBtn.textContent = '✅';
            setTimeout(() => copyBtn.textContent = originalIcon, 2000);
        });
    });

    newLinkBtn.addEventListener('click', () => {
        resultSection.classList.add('hidden');
        form.classList.remove('hidden');
        urlInput.value = '';
        customCodeInput.value = '';
        urlInput.focus();
    });

    async function loadLinks() {
        try {
            const r = await fetch('/api/links', { headers: headers() });
            if (handle401(r)) return;
            if (!r.ok) throw new Error('Failed to load links');

            const data = await r.json();

            if (!data.links || data.links.length === 0) {
                linksList.innerHTML = '<div class="empty-state">No links yet. Shorten a URL above!</div>';
                return;
            }

            linksList.innerHTML = data.links.map(link => {
                const lastAccessed = link.last_accessed === 'Never'
                    ? 'Never'
                    : new Date(link.last_accessed + 'Z').toLocaleDateString();
                return `
                    <div class="link-item">
                        <div class="link-info">
                            <div class="link-code">${escapeHtml(link.short_code)}</div>
                            <div class="link-url">${escapeHtml(link.original_url)}</div>
                        </div>
                        <div class="link-stats">
                            <div class="link-clicks">${link.click_count}</div>
                            <div class="link-date">${lastAccessed}</div>
                        </div>
                        <button class="delete-btn" data-code="${escapeHtml(link.short_code)}" title="Delete">🗑️</button>
                    </div>
                `;
            }).join('');

            document.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteLink(btn.dataset.code));
            });
        } catch (err) {
            console.error('loadLinks failed:', err);
            linksList.innerHTML = '<div class="empty-state">Failed to load links</div>';
        }
    }

    function deleteLink(code) {
        if (!confirm(`Delete short link "${code}"?`)) return;

        fetch(`/api/links/${code}`, {
            method: 'DELETE',
            headers: headers()
        })
            .then(r => {
                if (handle401(r)) return;
                if (!r.ok) throw new Error('Failed to delete');
                loadLinks();
            })
            .catch(err => alert(err.message));
    }

    refreshLinksBtn.addEventListener('click', loadLinks);

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('swoosh_password');
        location.reload();
    });
});
