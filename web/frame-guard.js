if (window.top !== window.self) {
  try {
    window.top.location = window.self.location.href;
  } catch {
    document.addEventListener('DOMContentLoaded', () => {
      document.body.innerHTML = `
        <main class="frame-blocked" aria-labelledby="frame-blocked-title">
          <h1 id="frame-blocked-title">Open Peace OS: Crisis Room directly</h1>
          <p>This review client does not permit embedded operation. Open the page in its own browser tab.</p>
          <p><a href="${window.location.href}" target="_top" rel="noopener">Open the simulation</a></p>
        </main>`;
    });
  }
}
