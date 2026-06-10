# Design Specification - Google IMA SDK Ads Integration

**Date:** 2026-06-10
**Status:** Approved

## 1. Goal Description
To replace the offline HTML5 video files in the Sponsor Hub with a real programmatic ad player using the Google Interactive Media Ads (IMA) SDK for HTML5. The player will load VAST ad tags, render linear video ads, and unlock the quota refill / 24H boost reward upon complete ad playback.

## 2. Technical Design

### A. Ad Tag URL
We will use Google Ad Manager's official linear VAST 3.0 test tag:
`https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_ad_samples&sz=640x480&ciu_szs=300x250&impl=s&gdfp_req=1&env=vp&output=vast&unviewed_position_start=1&cust_params=deployment%3Ddevsite%26sample_ct%3Dlinear&correlator=`

### B. Component Changes: `SponsorStreamModal.tsx`
- **SDK Loading:**
  - Inject a script element pointing to `https://imasdk.googleapis.com/js/sdkloader/ima3.js`.
  - Check for `window.google?.ima` to verify loading success.
- **HTML Layout:**
  - Create a parent container relative element.
  - Inside, place a `<video>` tag for content backing (hidden during ad playback).
  - Place a `div` element as the `adContainer` positioned absolute/overlay covering the video.
- **IMA Lifecycle Management:**
  - Create `google.ima.AdDisplayContainer(adContainerElement, videoElement)`.
  - Create `google.ima.AdsLoader(adDisplayContainer)`.
  - Listen to `google.ima.AdsManagerLoadedEvent.Type.ADS_MANAGER_LOADED` and `google.ima.AdErrorEvent.Type.AD_ERROR`.
  - On `ADS_MANAGER_LOADED`, retrieve the `AdsManager`, add listeners for `CONTENT_PAUSE_REQUESTED`, `CONTENT_RESUME_REQUESTED`, `ALL_ADS_COMPLETED`, `COMPLETE`, and `VOLUME_CHANGED`.
- **User Engagement Loop:**
  - Show a "Démarrer le Sponsor" button to start the ad container initialization and playback, complying with browser autoplay audio restrictions.
- **Error & Ad-Blocker Fallback:**
  - In case of ad loading errors (e.g. adblocker active, script load failure, network timeouts), catch the `AD_ERROR` event or catch script loading errors, and fallback to the offline HTML5 video players or the 10-second timer to ensure a seamless UX.

## 3. Test Verification
- Update tests in `PricingPage.test.tsx` to verify modal render states.
- Ensure that JSDOM environment does not crash due to script loading or missing window globals.
