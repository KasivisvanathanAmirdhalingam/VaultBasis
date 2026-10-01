  <script>
    // Shared navigation/dialog lifecycle; no assurance semantics here.
    function setNavOpen(open, restoreFocus = false) {
      const button = document.querySelector('.mobile-menu-btn');
      document.getElementById('main-nav')?.classList.toggle('open', open);
      document.querySelector('.header-actions')?.classList.toggle('open', open);
      button?.setAttribute('aria-expanded', String(open));
      button?.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
      if (restoreFocus) button?.focus();
    }
    function toggleNav() {
      setNavOpen(document.querySelector('.mobile-menu-btn')?.getAttribute('aria-expanded') !== 'true');
    }
    document.addEventListener('click', (event) => {
      if (!event.target.closest('header, #access-modal') && !document.getElementById('access-modal')?.open) setNavOpen(false);
      if (event.target.closest('#main-nav a')) setNavOpen(false);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !document.getElementById('access-modal')?.open &&
          document.querySelector('.mobile-menu-btn')?.getAttribute('aria-expanded') === 'true') setNavOpen(false, true);
    });

    const accessDialog = document.getElementById('access-modal');
    let accessInvoker = null;
    let accessPending = false;
    let accessSubmission = null;
    function openAccessModal(invoker) {
      if (!accessDialog || accessDialog.open) return;
      // Pointer activation does not focus buttons in every browser.
      accessInvoker = invoker || document.activeElement;
      accessDialog.showModal(); // Native modality makes the background inert.
      document.body.classList.add('dialog-open');
      const target = document.getElementById('request-success').hidden
        ? document.getElementById('req-name') : document.getElementById('request-success-title');
      target.focus();
    }
    function closeAccessModal() { accessDialog?.close(); }
    accessDialog?.addEventListener('close', () => {
      document.body.classList.remove('dialog-open');
      if (accessInvoker?.isConnected) accessInvoker.focus({ preventScroll: true });
    });
    accessDialog?.addEventListener('keydown', (event) => {
      if (event.key !== 'Tab') return;
      const controls = [...accessDialog.querySelectorAll('a[href],button,input,[tabindex="0"]')]
        .filter(control => !control.disabled && control.getClientRects().length);
      // Traverse the modal's controls explicitly: platform keyboard settings
      // can otherwise skip links/buttons and move focus to browser chrome.
      event.preventDefault();
      if (!controls.length) return;
      const current = controls.indexOf(document.activeElement);
      const next = current < 0 ? (event.shiftKey ? controls.length - 1 : 0)
        : (current + (event.shiftKey ? -1 : 1) + controls.length) % controls.length;
      controls[next].focus();
    });
    // Escape uses native cancel behavior. Closing preserves in-flight state.
    accessDialog?.addEventListener('click', (event) => {
      if (event.target !== accessDialog) return;
      const box = accessDialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) closeAccessModal();
    });

    async function submitAccessRequest(event) {
      event?.preventDefault();
      if (accessPending) return;
      const name = document.getElementById('req-name');
      const email = document.getElementById('req-email');
      const status = document.getElementById('request-status');
      let firstError = null;
      for (const [field, message] of [[name, 'Enter your full name.'], [email, 'Enter a valid contact email.']]) {
        field.value = field.value.trim();
        const valid = field.value.length > 0 && field.validity.valid;
        const error = document.getElementById(field.id + '-error');
        error.textContent = valid ? '' : message;
        error.hidden = valid;
        field.setAttribute('aria-invalid', String(!valid));
        if (!valid && !firstError) firstError = field;
      }
      if (firstError) { status.textContent = 'Check the highlighted fields.'; firstError.focus(); return; }
      const button = document.getElementById('btn-submit-req');
      accessPending = true;
      status.setAttribute('tabindex', '-1');
      status.focus();
      button.disabled = true;
      button.textContent = 'Submitting…';
      status.textContent = 'Submitting your request…';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 20000);
      try {
        const fields = { name: name.value, email: email.value };
        const fingerprint = JSON.stringify(fields);
        if (!accessSubmission || accessSubmission.fingerprint !== fingerprint) {
          accessSubmission = { fingerprint, requestId: crypto.randomUUID() };
        }
        const response = await fetch('/api/request-access', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...fields, requestId: accessSubmission.requestId }), signal: controller.signal
        });
        if (!response.ok) {
          status.textContent = response.status === 429
            ? 'Too many requests. Please wait before trying again. Your access has not been granted.'
            : response.status === 503
            ? 'Access requests are temporarily unavailable. Your access has not been confirmed. Contact VaultBasis or try again later.'
            : 'We could not confirm your request. Contact VaultBasis or try again later.';
          return;
        }
        const result = await response.json();
        if (response.status !== 202 || result.status !== 'pending_review') throw new Error('Unconfirmed request response');
        document.getElementById('request-form-container').hidden = true;
        document.getElementById('request-success').hidden = false;
        status.textContent = 'Request submitted. Pending review and manual provisioning. VaultBasis will contact you using your submitted email after approval.';
        if (accessDialog.open) document.getElementById('request-success-title').focus();
      } catch (_) {
        status.textContent = 'We could not confirm the outcome. The request may have reached VaultBasis. Retry with the same details; this will not create another request.';
      } finally {
        clearTimeout(timeout);
        accessPending = false;
        button.disabled = false;
        button.textContent = 'Submit Request';
        if (accessDialog && accessDialog.open && !document.getElementById('request-form-container').hidden) {
          button.focus();
        }
      }
    }
    document.getElementById('request-form-container')?.addEventListener('submit', submitAccessRequest);

    // Native fragment/history behavior preserves reload, Back and Forward.
    const main = document.querySelector('main');
    if (main) { main.id ||= 'main-content'; main.setAttribute('tabindex', '-1'); }
    const topButton = document.querySelector('.back-to-top');
    function updateTopButton() { if (topButton) topButton.hidden = window.scrollY < window.innerHeight; }
    window.addEventListener('scroll', updateTopButton, { passive: true });
    updateTopButton();
    topButton?.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
      main?.focus({ preventScroll: true });
    });
    document.querySelectorAll('#main-nav a').forEach(link => {
      if (link.getAttribute('href') === location.pathname) link.setAttribute('aria-current', 'page');
    });
  </script>
