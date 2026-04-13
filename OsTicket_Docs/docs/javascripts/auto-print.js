(() => {
  const isPrintPage = /\/print_page\/?$/.test(window.location.pathname);
  if (!isPrintPage) return;

  // Prevent repeated prompts on reload/live-reload
  const flag = 'osticket-print-dialog-opened';
  if (sessionStorage.getItem(flag) === '1') return;
  sessionStorage.setItem(flag, '1');

  // Let layout/fonts settle before opening print dialog
  window.addEventListener('load', () => {
    setTimeout(() => {
      window.print();
    }, 600);
  });
})();
