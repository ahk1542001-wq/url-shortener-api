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
    
    const statsLink = document.getElementById('stats-link');
    const statsSection = document.getElementById('stats-section');
    const statClicks = document.getElementById('stat-clicks');
    const statLastAccessed = document.getElementById('stat-last-accessed');
    const closeStatsBtn = document.getElementById('close-stats-btn');

    let currentShortCode = '';

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Reset state
        errorMsg.classList.add('hidden');
        resultSection.classList.add('hidden');
        statsSection.classList.add('hidden');
        
        const url = urlInput.value.trim();
        const customCode = customCodeInput.value.trim();
        
        if(!url) return;

        // UI Loading State
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

            // Success
            currentShortCode = data.short_code;
            const fullShortUrl = `${window.location.origin}/${currentShortCode}`;
            
            shortLinkUrl.href = fullShortUrl;
            shortLinkUrl.textContent = fullShortUrl;
            
            form.classList.add('hidden');
            resultSection.classList.remove('hidden');

        } catch (err) {
            errorMsg.textContent = err.message;
            errorMsg.classList.remove('hidden');
        } finally {
            // Restore UI State
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

    statsLink.addEventListener('click', async (e) => {
        e.preventDefault();
        if(!currentShortCode) return;

        try {
            const response = await fetch(`/api/stats/${currentShortCode}`);
            const data = await response.json();
            
            if(!response.ok) throw new Error(data.detail || 'Failed to load stats');

            statClicks.textContent = data.click_count;
            
            // Format date if not "Never"
            if(data.last_accessed && data.last_accessed !== 'Never') {
                const date = new Date(data.last_accessed + 'Z'); // SQLite assumes UTC
                statLastAccessed.textContent = date.toLocaleString();
            } else {
                statLastAccessed.textContent = 'Never';
            }

            resultSection.classList.add('hidden');
            statsSection.classList.remove('hidden');

        } catch (err) {
            alert(err.message);
        }
    });

    closeStatsBtn.addEventListener('click', () => {
        statsSection.classList.add('hidden');
        resultSection.classList.remove('hidden');
    });
});
