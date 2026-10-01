(() => {
  const cookie = name => document.cookie.split(';').map(item => item.trim()).find(item => item.startsWith(`${name}=`))?.slice(name.length + 1);
  const csrfToken = () => document.querySelector('[name=csrfmiddlewaretoken]')?.value || decodeURIComponent(cookie('csrftoken') || '');

  function showToast(message, kind = 'info') {
    let region = document.querySelector('.messages');
    if (!region) {
      region = document.createElement('div'); region.className = 'messages';
      region.setAttribute('aria-live', 'polite');
      document.querySelector('main.container')?.prepend(region);
    }
    const toast = document.createElement('div'); toast.className = `toast ${kind}`; toast.setAttribute('role', 'status');
    const icon = document.createElement('span'); icon.className = 'toast-icon'; icon.setAttribute('aria-hidden', 'true'); icon.textContent = kind === 'success' ? '✓' : kind === 'error' ? '!' : 'i';
    const text = document.createElement('p'); text.textContent = message;
    const close = document.createElement('button'); close.className = 'toast-close'; close.type = 'button'; close.setAttribute('aria-label', 'Dismiss message'); close.textContent = '×';
    const dismiss = () => { toast.classList.add('toast-leaving'); window.setTimeout(() => toast.remove(), 220); };
    close.addEventListener('click', dismiss); toast.append(icon, text, close); region.append(toast);
    window.setTimeout(dismiss, 5000);
  }

  async function send(url) {
    const response = await fetch(url, {method: 'POST', headers: {'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest'}, credentials: 'same-origin'});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
    return data;
  }

  document.querySelectorAll('.toast-close').forEach(button => button.addEventListener('click', () => {
    const toast = button.closest('.toast'); toast?.classList.add('toast-leaving');
    window.setTimeout(() => toast?.remove(), 220);
  }));
  document.querySelectorAll('.messages .toast').forEach(toast => window.setTimeout(() => {
    if (!toast.isConnected) return;
    toast.classList.add('toast-leaving'); window.setTimeout(() => toast.remove(), 220);
  }, 5500));

  document.querySelectorAll('.like-button').forEach(button => button.addEventListener('click', async () => {
    if (button.disabled) return;
    button.disabled = true; button.setAttribute('aria-busy', 'true'); button.classList.add('is-loading');
    try {
      const data = await send(button.dataset.likeUrl);
      button.setAttribute('aria-pressed', String(data.liked)); button.setAttribute('aria-label', data.liked ? 'Unlike this post' : 'Like this post');
      button.classList.toggle('is-liked', data.liked); button.querySelector('.like-label').textContent = data.liked ? 'Liked' : 'Like';
      const icon = button.querySelector('.heart-icon'); if (icon) icon.textContent = data.liked ? '♥' : '♡';
      const card = button.closest('.post-card');
      card?.querySelectorAll('.like-count').forEach(count => { count.textContent = data.count; });
      const likesLabel = card?.querySelector('.post-likes-label'); if (likesLabel) likesLabel.textContent = data.count === 1 ? 'like' : 'likes';
      if (data.liked) { button.classList.remove('like-pop'); void button.offsetWidth; button.classList.add('like-pop'); }
    } catch (error) { showToast(error.message, 'error'); }
    finally { button.disabled = false; button.removeAttribute('aria-busy'); button.classList.remove('is-loading'); }
  }));

  document.querySelectorAll('.follow-button').forEach(button => {
    const label = following => button.classList.contains('suggested-follow') ? (following ? '✓' : '+') : (following ? 'Following' : 'Follow');
    button.textContent = label(button.dataset.following === 'true');
    button.addEventListener('click', async () => {
      if (button.disabled) return;
      const wasFollowing = button.dataset.following === 'true';
      button.disabled = true; button.setAttribute('aria-busy', 'true');
      button.textContent = button.classList.contains('suggested-follow') ? '…' : (wasFollowing ? 'Unfollowing…' : 'Following…');
      try {
        const data = await send(button.dataset.followUrl); button.dataset.following = String(data.following);
        button.textContent = label(data.following); button.setAttribute('aria-label', `${data.following ? 'Unfollow' : 'Follow'} ${button.dataset.followUrl.split('/').filter(Boolean).at(-2) || 'user'}`);
        document.querySelectorAll('.follower-count').forEach(count => { count.textContent = data.count; });
      } catch (error) { button.textContent = label(wasFollowing); showToast(error.message, 'error'); }
      finally { button.disabled = false; button.removeAttribute('aria-busy'); }
    });
  });

  const themeButtons = document.querySelectorAll('.theme-toggle');
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeButtons.forEach(button => {
      const dark = theme === 'dark'; button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
      const icon = button.querySelector('span'); if (icon) icon.textContent = dark ? '☀' : '☾';
    });
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#14151d' : '#f6f7fb');
  }
  themeButtons.forEach(button => button.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme(next); try { localStorage.setItem('nexora-theme', next); } catch (_) { /* Theme remains active for this page. */ }
  }));
  applyTheme(document.documentElement.dataset.theme || 'light');

  const composer = document.querySelector('#composer textarea');
  const characterCount = document.querySelector('.character-count');
  if (composer && characterCount) {
    const updateCount = () => { characterCount.textContent = composer.value.length; characterCount.classList.toggle('limit-near', composer.value.length >= 900); };
    composer.addEventListener('input', updateCount); updateCount();
  }

  document.querySelectorAll('.search-form').forEach(form => form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (!button || !form.querySelector('input[name="q"]')?.value.trim()) return;
    button.disabled = true; button.textContent = 'Searching…';
  }));
})();
