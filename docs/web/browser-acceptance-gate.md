# Browser Acceptance Gate

The public web candidate must be tested from the deployed review URL before a GitHub prerelease is published.

## Required prerelease checks

- Complete both scenarios in Chromium.
- Confirm Practice, Assessment, and Facilitator behavior.
- Confirm no answer is preselected.
- Confirm all evidence must be reviewed before judgment.
- Confirm over-budget plans are blocked.
- Confirm a changed decision invalidates human confirmation.
- Confirm score and AAR remain hidden until commitment.
- Confirm saved-session resume, replacement, and deletion.
- Confirm malformed saved data is removed safely.
- Confirm storage-denial, clipboard-denial, and download-failure fallbacks.
- Confirm keyboard focus, skip link, 200% zoom, and 320-pixel reflow.
- Confirm no console error or failed first-party network request.

## Stable-release checks

Add Firefox, Safari/WebKit, physical mobile devices, complete keyboard use, and assistive-technology review. Record browser, operating system, date, deployed commit, result, limitations, and evidence.

A local harness or static contract does not replace deployed-path testing.
