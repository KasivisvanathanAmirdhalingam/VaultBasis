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

    function onTierSelectionChange() {
      const tierSelect = document.getElementById('req-tier');
      const modalTitle = document.getElementById('modal-title');
      const modalDesc = document.getElementById('modal-desc');
      const btn = document.getElementById('btn-submit-req');
      const tier = tierSelect ? tierSelect.value : 'PRACTICE';

      if (tier === 'TRIAL') {
        if (modalTitle) modalTitle.innerText = 'Start Free Evaluation';
        if (modalDesc) modalDesc.innerText = 'VaultBasis runs entirely on your local computer. Enter your details to receive your evaluation download authorization via email.';
        if (btn) btn.innerText = 'Get Evaluation Download';
      } else if (tier === 'ESSENTIAL') {
        if (modalTitle) modalTitle.innerText = 'Order Solo Practitioner License';
        if (modalDesc) modalDesc.innerText = 'VaultBasis Solo License ($499/year) covers up to 10 client cases with 100% local computer storage and signed Evidence Receipts.';
        if (btn) btn.innerText = 'Continue to Checkout ($499/yr) →';
      } else if (tier === 'PRACTICE') {
        if (modalTitle) modalTitle.innerText = 'Order Practice License';
        if (modalDesc) modalDesc.innerText = 'VaultBasis Practice License ($1,499/year) covers up to 50 client cases for CPA firms with preparer provenance on Evidence Receipts.';
        if (btn) btn.innerText = 'Continue to Checkout ($1,499/yr) →';
      } else if (tier === 'ENTERPRISE') {
        if (modalTitle) modalTitle.innerText = 'Enterprise & Larger Firms';
        if (modalDesc) modalDesc.innerText = 'Custom case volume (250+ cases), multi-seat firm deployments, and priority CPA workflow support.';
        if (btn) btn.innerText = 'Submit Enterprise Inquiry →';
      }
    }

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
      const btn = document.getElementById('btn-submit-req');

      if (form) form.style.display = 'block';
      if (success) success.style.display = 'none';
      if (name) name.value = '';
      if (email) email.value = '';
      if (tierSelect && tier) {
        tierSelect.value = tier;
      }
      onTierSelectionChange();
      if (btn) btn.disabled = false;

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
      if (btn) { btn.innerText = 'Continue to Checkout ($1,499/yr) →'; btn.disabled = false; }

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
      const tierSelect = document.getElementById('req-tier');
      const tier = tierSelect ? tierSelect.value : 'PRACTICE';
      const btn = document.getElementById('btn-submit-req');
      if (!name || !email) { alert('Please provide your name and work email address.'); return; }
      
      const originalBtnText = btn.innerText;
      btn.innerText = 'Processing…';
      btn.disabled = true;

      try {
        let endpoint = '/api/request-access';
        let payload = { name, email, tier };

        if (tier === 'ESSENTIAL' || tier === 'PRACTICE') {
          endpoint = '/api/checkout';
          payload = { plan: (tier === 'ESSENTIAL' ? 'SOLO' : 'PRACTICE'), name, email };
        } else if (tier === 'ENTERPRISE') {
          endpoint = '/api/enterprise-inquiry';
          payload = { name, email, plan: 'ENTERPRISE' };
        }

        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        let data = {};
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          data = await res.json();
        } else {
          const rawText = await res.text();
          data = { error: `Server returned unexpected response (HTTP ${res.status}).` };
        }

        if (res.ok) {
          if (tier === 'TRIAL') {
            document.getElementById('request-form-container').style.display = 'none';
            const succ = document.getElementById('request-success');
            const title = document.getElementById('success-title');
            const desc = document.getElementById('success-desc');
            if (title) title.innerText = 'Evaluation Authorization Dispatched';
            if (desc) desc.innerText = `Your free evaluation download link has been sent to ${email}. Check your work inbox within 2 minutes.`;
            succ.style.display = 'block';
          } else if (tier === 'ENTERPRISE') {
            document.getElementById('request-form-container').style.display = 'none';
            const succ = document.getElementById('request-success');
            const title = document.getElementById('success-title');
            const desc = document.getElementById('success-desc');
            if (title) title.innerText = 'Enterprise Inquiry Received';
            if (desc) desc.innerText = `Thank you, ${name}. Our enterprise team will follow up at ${email} with custom deployment options.`;
            succ.style.display = 'block';
          } else {
            // Commercial Self-Serve Checkout (Solo or Practice)
            if (data.checkoutUrl && data.checkoutUrl.startsWith('http') && !data.checkoutUrl.includes('checkout-session')) {
              window.location.href = data.checkoutUrl;
            } else {
              document.getElementById('request-form-container').style.display = 'none';
              const succ = document.getElementById('request-success');
              const title = document.getElementById('success-title');
              const desc = document.getElementById('success-desc');
              if (title) title.innerText = `Order Created: ${data.orderId || 'PENDING'}`;
              if (desc) desc.innerText = `Your ${data.orderSummary ? data.orderSummary.displayName : 'commercial'} order has been registered. Checkout session initiated for ${email}.`;
              succ.style.display = 'block';
            }
          }
        } else {
          alert(data.error || `Request could not be processed (HTTP ${res.status}). Please try again.`);
          btn.innerText = originalBtnText;
          btn.disabled = false;
        }
      } catch (err) {
        console.error('[VaultBasis] Access submission failure:', err);
        if (err instanceof TypeError && String(err.message).toLowerCase().includes('fetch')) {
          alert('Unable to reach the server. Please check your internet connection and try again.');
        } else {
          alert(`Submission error: ${err.message || 'Please try again later.'}`);
        }
        btn.innerText = originalBtnText;
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
