# Design Specification - Unskippable Video Ads for Quota & Boost

**Date:** 2026-06-10
**Status:** Approved

## 1. Goal Description
To replace the static progress bar simulation in the Sponsor Hub with an interactive HTML5 video player. Users must watch the entire video ad before being allowed to claim their 24H tier boost or quota refill.

## 2. Technical Design

### A. Video Sources
We will use Google-hosted high-availability video files:
* **Refill Quota:** `https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4` (Duration: ~12s)
* **24H Boost:** `https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4` (Duration: ~15s)

### B. Component Changes: `SponsorStreamModal.tsx`
- **Video Element:** Replaces the static SVG animation with an HTML5 `<video>` tag.
- **Controls & Interaction:**
  - `controls={false}` to hide player seek bars and play/pause buttons.
  - Disable right-click on the video to prevent access to standard browser media controls.
  - `autoPlay` and `muted` enabled to satisfy browser policy guidelines.
  - Add custom Mute/Unmute button utilizing the HTML5 video `muted` property.
- **State & Events:**
  - `onTimeUpdate` updates the custom UI progress bar matching `(video.currentTime / video.duration) * 100`.
  - `onEnded` sets `isDone` to `true`, showing the green checkmark, enabling the "RÉCLAMER LE BONUS" button, and restoring the close button `(X)`.
  - `onError` catches any loading/playback failures and automatically starts a 10-second CSS animation timer fallback, ensuring users aren't locked out in case of connectivity issues.

### C. Test Verification
- Modify unit tests in `PricingPage.test.tsx` to handle the modal interactions correctly.
- Add mock handlers for the HTML5 video element.
