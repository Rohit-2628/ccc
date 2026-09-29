// Latveria CI Orchestrator Client Script

document.addEventListener('DOMContentLoaded', () => {
    const triggerForm = document.getElementById('trigger-build-form');
    const resultBox = document.getElementById('trigger-result');

    if (triggerForm) {
        triggerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const repo = document.getElementById('build-repo').value;
            const branch = document.getElementById('build-branch').value;
            const hook = document.getElementById('build-hook').value;
            const submitBtn = document.getElementById('btn-submit-build');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Dispatching to Runner...';
            resultBox.style.display = 'none';

            try {
                const resp = await fetch('/api/builds/trigger', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        repo: repo,
                        branch: branch,
                        build_hook: hook,
                        build_params: { CUSTOM_TEST_HOOK: hook }
                    })
                });

                const data = await resp.json();
                if (resp.ok) {
                    resultBox.className = 'alert-box alert-success';
                    resultBox.innerHTML = `<strong>${data.message}</strong> <br> Redirecting to console in 2 seconds... (<a href="${data.url}">Click here</a>)`;
                    resultBox.style.display = 'block';
                    setTimeout(() => {
                        window.location.href = data.url;
                    }, 1500);
                } else {
                    resultBox.className = 'alert-box alert-error';
                    resultBox.textContent = data.error || 'Failed to dispatch build.';
                    resultBox.style.display = 'block';
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Dispatch Build Job';
                }
            } catch (err) {
                resultBox.className = 'alert-box alert-error';
                resultBox.textContent = 'Network error contacting CI gateway.';
                resultBox.style.display = 'block';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Dispatch Build Job';
            }
        });
    }

    // Auto-poll console log if on build detail page
    const liveConsole = document.getElementById('live-console');
    if (liveConsole) {
        const pathParts = window.location.pathname.split('/');
        const buildId = pathParts[pathParts.length - 1];
        if (buildId && !isNaN(buildId)) {
            const pollInterval = setInterval(async () => {
                try {
                    const resp = await fetch(`/api/builds/${buildId}`);
                    if (resp.ok) {
                        const data = await resp.json();
                        liveConsole.textContent = data.logs.join('\n');
                        if (data.status === 'SUCCESS' || data.status === 'FAILED') {
                            clearInterval(pollInterval);
                        }
                    }
                } catch (e) {
                    clearInterval(pollInterval);
                }
            }, 1000);
        }
    }
});
