# Design: Personalization Middleware

## Goal
Intercept JSON responses for authenticated users to inject "Visual Meta" (archetype drift configuration) into the response.

## Architecture
- **Location**: `backend/api/animetix/middleware/personalization_middleware.py`
- **Dependency Injection**: Uses `dependency-injector` to inject `archetype_drift_service` from the `CoreServicesContainer`.
- **Response Modification**:
  - Checks if `Content-Type` is `application/json`.
  - Checks if user is authenticated.
  - Fetches visual configuration using `drift_service.calculate_drift(user.id)`.
  - Injects `visual_config` into `meta` block of the JSON response.

## Structural Change
To follow the requested path `backend/api/animetix/middleware/personalization_middleware.py`, the existing `middleware.py` file will be converted into a package:
1. Create directory `backend/api/animetix/middleware/`.
2. Move `backend/api/animetix/middleware.py` to `backend/api/animetix/middleware/__init__.py`.
3. Create `backend/api/animetix/middleware/personalization_middleware.py`.

## Configuration
- Add `animetix.middleware.personalization_middleware.PersonalizationMiddleware` to `MIDDLEWARE` in `settings.py`.
- Position: After `animetix.middleware.UserTrackingMiddleware`.

## Testing Strategy
- Create `backend/api/animetix/tests/test_personalization_middleware.py`.
- Test cases:
  - Authenticated user receives `meta.visual_config` in JSON response.
  - Anonymous user does NOT receive `meta.visual_config`.
  - Non-JSON responses are left unchanged.
  - Middleware handles service failures gracefully (logs error and returns original response).
