# Rewarded ads architecture (option A scaffolding)

## The rule

Google **AdSense forbids incentivizing ad interaction**: you may never reward,
pay, or compensate a user for viewing or clicking an AdSense ad. AdSense also
has no rewarded/incentivized format for the web.

So the "watch a rewarded ad → earn Bx" mechanic must be powered by a **dedicated
rewarded-ads network** (Google Ad Manager rewarded units, or a third-party SSP),
**strictly separate from AdSense**. AdSense (`AdSlot`) stays passive display only
and is **never** the trigger of a reward.

## What is in place (scaffolding, network-agnostic)

The plumbing is ready; only a real network account needs to be plugged in.

### Frontend — `features/billing/rewarded/rewardedAdProvider.ts`

- `RewardedAdProvider` interface: `isConfigured()` + `showRewarded(onProgress)`
  → `{ rewarded, rewardToken, provider }`.
- `stubRewardedAdProvider`: dev stub — a 15s engagement timer, **no real ad**,
  returns `rewardToken: null`.
- `getRewardedAdProvider()`: picks the provider from `VITE_REWARDED_PROVIDER`
  (default → stub).
- `PowerStationPage` calls `showRewarded()`; on reward it credits via
  `billingService.activeRecharge(rewardToken)`. It never touches an `AdSlot`.

### Backend — `core/domain/services/rewarded_ad_verifier.py`

- `verify_rewarded_ad(reward_token)` is called by `WalletWatchAdView` **before**
  crediting:
  - **stub mode** (`REWARDED_ADS_PROVIDER` unset/`stub`): allowed without a token
    (dev — the front plays the engagement timer).
  - **real network configured**: a valid signed token is **mandatory**; missing
    or unverified → `402` (fail-closed). No credit is ever granted on an
    unverified token.

## To plug a real network (remaining work)

1. Open a **dedicated rewarded** account (GAM rewarded units web, or a third-party
   SSP). *External action — no code can create this.*
2. Implement the real provider in `rewardedAdProvider.ts`: `showRewarded()` loads
   the SDK, shows the rewarded ad, waits for the network's reward event, returns
   the signed token. Expose it in `getRewardedAdProvider()`. Never reuse an
   `AdSlot`.
3. Implement signature verification (SSV) in `verify_rewarded_ad` (validate the
   GAM signature, or call the SSP's verification API).
4. Configure env: `VITE_REWARDED_PROVIDER` (front), `REWARDED_ADS_PROVIDER` +
   the network IDs/secret (back).
5. Re-calibrate `ad_reward_bx()` to the network's real revenue.

## Never

- Wire an AdSense ad behind the recharge button.
- Re-introduce "watch ad / reward ads" wording near the `AdSlot` display units.
- Credit Bx on a token that wasn't server-verified once a real network is live.
