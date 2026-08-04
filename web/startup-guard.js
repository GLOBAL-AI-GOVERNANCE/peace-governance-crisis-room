(() => {
  const showFailure = message => {
    if (document.documentElement.dataset.appReady === 'true' || document.documentElement.dataset.appFailed === 'true') return;
    document.documentElement.dataset.appFailed = 'true';
    const main = document.getElementById('main');
    if (!main) return;
    main.innerHTML = `<section class="panel" aria-labelledby="startup-failure-heading"><h2 id="startup-failure-heading">Unable to start the simulation</h2><p class="error">${message}</p><p>Reload in a current browser. The source and known limitations remain public:</p><ul><li><a href="https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room">Source repository</a></li><li><a href="https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/blob/main/VERIFICATION.md">Verification matrix</a></li><li><a href="https://github.com/GLOBAL-AI-GOVERNANCE/peace-os-crisis-room/issues/new/choose">Report an issue</a></li></ul></section>`;
  };
  window.addEventListener('error', event => {
    const source = event.target?.src || '';
    if (source.includes('/app.js')) showFailure('The application module did not load. No decision was committed.');
  }, true);
  window.setTimeout(() => showFailure('The application did not become ready within the expected startup window. No decision was committed.'), 12000);
})();
