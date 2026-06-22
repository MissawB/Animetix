import { apiClient } from '../../../utils/apiClient';

export type AdEventType = 'impression' | 'click';
export type AdType = 'banner' | 'video';

// Best-effort analytics logging. Routes through apiClient (CSRF + Firebase auth)
// but stays fire-and-forget: it never surfaces a toast and never throws to the
// caller, so a failed log can't break the ad UX.
export const logAdEvent = (eventType: AdEventType, adType: AdType): void => {
  void apiClient('/api/v1/billing/log_ad_event/', {
    method: 'POST',
    body: JSON.stringify({ event_type: eventType, ad_type: adType }),
    skipToast: true,
  }).catch(() => {
    /* analytics is best-effort */
  });
};
