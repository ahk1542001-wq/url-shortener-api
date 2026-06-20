document.addEventListener('DOMContentLoaded', () => {
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.error?.message || 'Failed to shorten URL');
            }

            const fullShortUrl = `${window.location.origin}/${data.short_code}`;

            shortLinkUrl.href = fullShortUrl;
            shortLinkUrl.textContent = fullShortUrl;

            const resultText = resultSection.querySelector('p');
            if (data.already_exists) {
                resultText.textContent = 'This URL was already shortened!';
            } else {
                resultText.textContent = 'Your short link is ready!';
            }

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
            setTimeout(() => {
                copyBtn.textContent = originalIcon;
            }, 2000);
        });
    });

    newLinkBtn.addEventListener('click', () => {
        resultSection.classList.add('hidden');
        form.classList.remove('hidden');
        urlInput.value = '';
        customCodeInput.value = '';
        urlInput.focus();
    });

    function loadLinks() {
        fetch('/api/links')
            .then(r => r.json())
            .then(data => {
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
                                <div class="link-code">${link.short_code}</div>
                                <div class="link-url">${link.original_url}</div>
                            </div>
                            <div class="link-stats">
                                <div class="link-clicks">${link.click_count}</div>
                                <div class="link-date">${lastAccessed}</div>
                            </div>
                            <button class="delete-btn" data-code="${link.short_code}" title="Delete">🗑️</button>
                        </div>
                    `;
                }).join('');

                document.querySelectorAll('.delete-btn').forEach(btn => {
                    btn.addEventListener('click', () => deleteLink(btn.dataset.code));
                });
            })
            .catch(() => {
                linksList.innerHTML = '<div class="empty-state">Failed to load links</div>';
            });
    }

    function deleteLink(code) {
        if (!confirm(`Delete short link "${code}"?`)) return;

        fetch(`/api/links/${code}`, { method: 'DELETE' })
            .then(r => {
                if (!r.ok) throw new Error('Failed to delete');
                loadLinks();
            })
            .catch(err => alert(err.message));
    }

    refreshLinksBtn.addEventListener('click', loadLinks);

    loadLinks();
});
