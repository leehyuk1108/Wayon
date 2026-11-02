# Parking Sign Notifications

The Windows ParkingVision service publishes new, validated readable floor,
zone, pillar and bay clues through the existing Wayon Cloud FCM delivery path.
It does not assert the exact parking space. Unknown or ambiguous readings do
not send a notification; neither do old jobs at activation.

## Scope

- Comma, cameras, driving models and vehicle controls are unchanged.
- Existing My Traverse v38 display assets are retained byte-for-byte in v39.
- A separate parking-notification credential grants only this notification
  endpoint, bound to the existing owner device. The AI read token stays read-only.
- No image, raw evidence, credential or private deployment artifact is published.

## Delivery

`parkingNotify` in the private server configuration selects `enabled`, a private
`credentialsFile` and `notBefore`. The credentials contain the HTTPS origin,
dedicated token and device ID. They are separate from collector credentials.

Two distinct images at least 0.5 seconds apart must support a readable clue.
The completion transaction creates an outbox entry; a separate bounded worker
sends it without blocking recognition. Failure to notify does not fail an
otherwise completed analysis. New jobs and capture times must be after activation;
parked pictures expire after 30 minutes and results after 10 minutes.

The persistent event claim prevents duplicate sends after retries/restarts.
Identical parked-only clues are suppressed for six hours; cited newer approach
evidence can identify a new encounter and bypass that content cooldown. This
does not prove the same physical parking session. No resending is attempted
after an uncertain FCM send, so an ambiguous failure can lose a notification.

Cloud validates the same evidence/phase/time contract, claims the event before
sending, and uses the existing device-bound FCM subscriptions. HTTP 202 is a
durable claim, not a phone delivery receipt. A positive Cloud sent count means
FCM accepted the message, not that a person saw it.

My Traverse v39 adds a dedicated private notification channel and a foreground
receiver. Background delivery uses the visible FCM payload. Channel/notification
permission settings are respected. Tapping opens the existing app; no new home
screen or result page is added. Approach evidence is explicitly described as
a nearby clue rather than the parked vehicle's exact position.

## Verification

- Local server suite: 86 passed, including 36 new notification tests.
- Actual Windows suite: 85 passed, one POSIX-permission-only skip. Two temporary
  SQLite test connections originally prevented Windows cleanup; explicitly
  closing them fixed cleanup without weakening assertions or runtime behavior.
- Real workerd/D1 suite: 27 passed, including the actual Python-generated wire
  payload and actual Python ACK parser, concurrent claims, expiry and auth denial.
- Android release: 81 JVM and 76 JavaScript tests passed; same installed signer.
- Production Cloud version: `3df9974a-1766-4182-86c3-3bd9d95029c0`; original three
  modules and 22 bindings preserved, plus the dedicated notification secret.
- Windows installed source hashes and original configuration fields match;
  authenticated health reports the recognition and notification workers alive.
- One explicitly labelled test traversed Windows -> Cloud -> FCM with one
  accepted recipient. It is synthetic notification content, not an OCR result.

At this verification point the phone's wireless ADB connection had dropped.
v39 installation and physical phone notification display remain unverified.
The signed v39 APK is retained locally for the next authorized device connection.
No new real readable parking sign was available to verify recognition accuracy.
