/* INKLINE Main Frontend Interactions */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Reading Progress Bar
  const progressBar = document.getElementById('reading-progress');
  if (progressBar) {
    window.addEventListener('scroll', function () {
      const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      if (docHeight > 0) {
        const scrolled = (window.scrollY / docHeight) * 100;
        progressBar.style.width = scrolled + '%';
      }
    });
  }

  // Helper: Get CSRF Cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  // 2. AJAX Bookmark Toggle
  document.querySelectorAll('.btn-bookmark-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const articleId = this.dataset.articleId;
      const url = `/features/bookmark/${articleId}/`;

      fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrftoken,
        }
      })
      .then(res => {
        if (res.redirected) {
          window.location.href = res.url;
          return;
        }
        return res.json();
      })
      .then(data => {
        if (data && data.status === 'ok') {
          const icon = btn.querySelector('i');
          const textSpan = btn.querySelector('.bookmark-text');
          if (data.bookmarked) {
            icon.className = 'bi bi-bookmark-fill text-burgundy';
            if (textSpan) textSpan.textContent = 'Saved';
            btn.classList.add('bookmarked');
          } else {
            icon.className = 'bi bi-bookmark';
            if (textSpan) textSpan.textContent = 'Save Story';
            btn.classList.remove('bookmarked');
          }
        }
      })
      .catch(err => console.error('Bookmark error:', err));
    });
  });

  // 3. AJAX Follow Author Toggle
  document.querySelectorAll('.btn-follow-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const authorId = this.dataset.authorId;
      const url = `/features/follow/${authorId}/`;

      fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrftoken,
        }
      })
      .then(res => {
        if (res.redirected) {
          window.location.href = res.url;
          return;
        }
        return res.json();
      })
      .then(data => {
        if (data && data.status === 'ok') {
          if (data.is_following) {
            btn.innerHTML = '<i class="bi bi-person-check-fill me-1"></i> Following';
            btn.classList.replace('btn-ink-outline', 'btn-ink-primary');
          } else {
            btn.innerHTML = '<i class="bi bi-person-plus me-1"></i> Follow Author';
            btn.classList.replace('btn-ink-primary', 'btn-ink-outline');
          }
        }
      })
      .catch(err => console.error('Follow error:', err));
    });
  });

  // 4. Newsletter Subscription AJAX
  const newsletterForm = document.getElementById('newsletter-subscription-form');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const input = document.getElementById('newsletter-email-input');
      const feedback = document.getElementById('newsletter-feedback');
      const submitBtn = newsletterForm.querySelector('button[type="submit"]');

      submitBtn.disabled = true;
      submitBtn.textContent = 'Subscribing...';

      const formData = new FormData(newsletterForm);

      fetch('/newsletter/subscribe/', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrftoken,
        }
      })
      .then(res => res.json())
      .then(data => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subscribe';
        if (data.status === 'ok') {
          feedback.innerHTML = `<div class="alert alert-success mt-2 py-2">${data.message}</div>`;
          input.value = '';
        } else {
          feedback.innerHTML = `<div class="alert alert-danger mt-2 py-2">${data.message}</div>`;
        }
      })
      .catch(err => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subscribe';
        feedback.innerHTML = `<div class="alert alert-danger mt-2 py-2">Subscription failed. Please try again later.</div>`;
      });
    });
  }

  // 5. Image Preview before submission
  const coverInput = document.getElementById('cover-image-input');
  const coverPreview = document.getElementById('cover-image-preview');
  if (coverInput && coverPreview) {
    coverInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          coverPreview.src = e.target.result;
          coverPreview.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // 6. Word Count & Headline Character Count
  const titleInput = document.getElementById('article-title-input');
  const titleCount = document.getElementById('title-char-count');
  if (titleInput && titleCount) {
    const updateTitleCount = () => {
      titleCount.textContent = `${titleInput.value.length} characters`;
    };
    titleInput.addEventListener('input', updateTitleCount);
    updateTitleCount();
  }

  const contentEditor = document.getElementById('article-content-editor');
  const wordCountDisplay = document.getElementById('editor-word-count');
  const readingTimeDisplay = document.getElementById('editor-read-time');
  if (contentEditor && wordCountDisplay) {
    const updateWordCount = () => {
      const text = contentEditor.value.replace(/<[^>]+>/g, ' ').trim();
      const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
      wordCountDisplay.textContent = `${words} words`;
      if (readingTimeDisplay) {
        const estMinutes = Math.max(1, Math.ceil(words / 200));
        readingTimeDisplay.textContent = `~${estMinutes} min read`;
      }
    };
    contentEditor.addEventListener('input', updateWordCount);
    updateWordCount();
  }
});
