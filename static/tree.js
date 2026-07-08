document.addEventListener('DOMContentLoaded', async () => {
    // Extract username from URL path: /u/{username}
    const pathParts = window.location.pathname.split('/');
    const username = pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2];

    const loadingState = document.getElementById('loading-state');
    const treeContent = document.getElementById('tree-content');
    const errorState = document.getElementById('error-state');

    if (!username) {
        showError();
        return;
    }

    try {
        const response = await fetch(`/api/users/${username}/tree`);
        
        if (!response.ok) {
            throw new Error('User not found');
        }
        
        const data = await response.json();
        renderTree(data);
    } catch (err) {
        console.error(err);
        showError();
    }

    function renderTree(data) {
        document.title = `${data.username} | Swoosh Link Tree`;
        
        document.getElementById('profile-username').textContent = `@${data.username}`;
        
        const bioEl = document.getElementById('profile-bio');
        if (data.bio) {
            bioEl.textContent = data.bio;
        } else {
            bioEl.style.display = 'none';
        }
        
        // Render Socials
        if (data.social_links && data.social_links.length > 0) {
            const socialContainer = document.getElementById('social-container');
            socialContainer.classList.remove('hidden');
            
            data.social_links.forEach(social => {
                const a = document.createElement('a');
                a.href = social.url;
                a.target = '_blank';
                a.className = 'social-btn';
                a.title = social.platform;
                
                // Try to find matching SVG icon
                const iconId = `icon-${social.platform.toLowerCase()}`;
                
                a.innerHTML = `<svg width="22" height="22"><use href="#${iconId}"/></svg>`;
                socialContainer.appendChild(a);
            });
        }
        
        // Render Links
        const linksContainer = document.getElementById('links-container');
        if (data.links && data.links.length > 0) {
            data.links.forEach(link => {
                const a = document.createElement('a');
                a.href = `/${link.short_code}`; // Redirects through our tracker
                a.target = '_blank';
                a.className = 'tree-link-btn';
                
                // Prioritize title, fallback to original url
                let displayTitle = link.title;
                if (!displayTitle) {
                    try {
                        const urlObj = new URL(link.original_url);
                        displayTitle = urlObj.hostname + (urlObj.pathname.length > 1 ? urlObj.pathname.substring(0, 15) + '...' : '');
                    } catch {
                        displayTitle = link.original_url.substring(0, 30) + '...';
                    }
                }
                
                a.textContent = displayTitle;
                linksContainer.appendChild(a);
            });
        } else {
            linksContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted);">No links to show yet.</p>';
        }

        // Switch Views
        loadingState.classList.add('hidden');
        treeContent.classList.remove('hidden');
    }

    function showError() {
        loadingState.classList.add('hidden');
        errorState.classList.remove('hidden');
    }
});
