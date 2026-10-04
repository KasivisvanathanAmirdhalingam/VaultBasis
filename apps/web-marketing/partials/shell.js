  <script>
    /* ── VaultBasis Canonical Shell JS ───────────────────────────────────── */

    /* Mobile nav toggle */
    function toggleNav() {
      const nav = document.getElementById('main-nav');
      const actions = document.querySelector('.header-actions');
      const btn = document.querySelector('.mobile-menu-btn');
      const open = nav.classList.toggle('open');
      if (actions) actions.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    }
    /* Close nav on outside click */
    document.addEventListener('click', function(e) {
      const nav = document.getElementById('main-nav');
      if (!nav) return;
      if (!nav.contains(e.target) && !e.target.closest('.mobile-menu-btn') && !e.target.closest('.header-actions')) {
        nav.classList.remove('open');
        const actions = document.querySelector('.header-actions');
        if (actions) actions.classList.remove('open');
        const btn = document.querySelector('.mobile-menu-btn');
        if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-label', 'Open navigation'); }
      }
    });

    /* Access modal state management (VB-WEB-INV-003) */
    let _lastFocusedElement = null;

    function openAccessModal(triggerEl, tier) {
      const modal = document.getElementById('access-modal');
      if (!modal) return;
      _lastFocusedElement = triggerEl || document.activeElement;

      // Always reset to initial FORM state
      const form = document.getElementById('request-form-container');
      const success = document.getElementById('request-success');
      const name = document.getElementById('req-name');
      const email = document.getElementById('req-email');
      const tierSelect = document.getElementById('req-tier');
      const modalTitle = document.getElementById('modal-title');
      const btn = document.getElementById('btn-submit-req');

      if (form) form.style.display = 'block';
      if (success) success.style.display = 'none';
      if (name) name.value = '';
      if (email) email.value = '';
      if (tierSelect && tier) {
        tierSelect.value = tier;
      }
      if (modalTitle) {
        modalTitle.innerText = (tier === 'TRIAL') ? 'Start Free Sample Evaluation' : 'Acquire VaultBasis License';
      }
      if (btn) {
        btn.innerText = (tier === 'TRIAL') ? 'Get Evaluation Download' : 'Proceed to Delivery';
        btn.disabled = false;
      }

      modal.style.display = 'flex';
      setTimeout(function() {
        const n = document.getElementById('req-name');
        if (n) n.focus();
      }, 50);
      document.addEventListener('keydown', _modalKeyHandler);
    }

    function closeAccessModal() {
      const modal = document.getElementById('access-modal');
      if (!modal) return;
      modal.style.display = 'none';

      const form = document.getElementById('request-form-container');
      const success = document.getElementById('request-success');
      const name = document.getElementById('req-name');
      const email = document.getElementById('req-email');
      const btn = document.getElementById('btn-submit-req');
      if (form) form.style.display = 'block';
      if (success) success.style.display = 'none';
      if (name) name.value = '';
      if (email) email.value = '';
      if (btn) { btn.innerText = 'Proceed to Delivery'; btn.disabled = false; }

      document.removeEventListener('keydown', _modalKeyHandler);
      if (_lastFocusedElement && typeof _lastFocusedElement.focus === 'function') {
        _lastFocusedElement.focus();
        _lastFocusedElement = null;
      }
    }

    function _modalKeyHandler(e) {
      if (e.key === 'Escape') closeAccessModal();
    }

    /* Close modal on overlay click */
    document.addEventListener('click', function(e) {
      const modal = document.getElementById('access-modal');
      if (modal && e.target === modal) closeAccessModal();
    });

    async function submitAccessRequest() {
      const name = document.getElementById('req-name').value.trim();
      const email = document.getElementById('req-email').value.trim();
      const tier = document.getElementById('req-tier') ? document.getElementById('req-tier').value : 'PRACTICE';
      const btn = document.getElementById('btn-submit-req');
      if (!name || !email) { alert('Please provide a name and email address.'); return; }
      btn.innerText = 'Dispatching…';
      btn.disabled = true;
      try {
        const res = await fetch('/api/request-access', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, tier })
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('request-form-container').style.display = 'none';
          document.getElementById('request-success').style.display = 'block';
        } else {
          alert(data.error || 'Request could not be submitted. Please try again.');
          btn.innerText = 'Proceed to Delivery';
          btn.disabled = false;
        }
      } catch (_err) {
        alert('A network error occurred. Please check your connection and try again.');
        btn.innerText = 'Proceed to Delivery';
        btn.disabled = false;
      }
    }

    /* Smooth scroll for same-page anchors */
    document.querySelectorAll('a[href^="/#"]').forEach(function(anchor) {
      if (window.location.pathname !== '/') return;
      anchor.addEventListener('click', function(e) {
        const id = this.getAttribute('href').substring(2);
        const el = document.getElementById(id);
        if (!el) return;
        e.preventDefault();
        const hdr = document.querySelector('header');
        const offset = hdr ? hdr.offsetHeight + 24 : 80;
        window.scrollTo({ top: el.getBoundingClientRect().top + window.pageYOffset - offset, behavior: 'smooth' });
        history.pushState(null, null, '#' + id);
      });
    });
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
      anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#' || href.length < 2) return;
        const el = document.getElementById(href.substring(1));
        if (!el) return;
        e.preventDefault();
        const hdr = document.querySelector('header');
        const offset = hdr ? hdr.offsetHeight + 24 : 80;
        window.scrollTo({ top: el.getBoundingClientRect().top + window.pageYOffset - offset, behavior: 'smooth' });
        history.pushState(null, null, href);
      });
    });
  </script>
