# User Feedback — URL Shortener API

- **How collected:** Chat messages from friends testing the app (3 people)
- **When:** July 8, 2026

## Raw feedback

1. "The dark UI looks sick, but what if I want to change a link's destination after I create it?"
2. "I noticed there's no way to delete a link if I make a typo in the custom code."
3. "It would be cool if the success page showed a QR code so I could just scan it from my phone."

## Themes (what keeps coming up)

- Users want CRUD capabilities (Edit and Delete) for their generated links, not just Create and Read.
- Mobile friendliness/sharing (QR Codes).

## Top 3 things to fix

- [x] Add an "Edit Link" feature.
- [x] Add a "Delete Link" feature.
- [x] Implement local QR Code generation for shortened URLs and Link Tree pages.

## Resolution

All three requests are implemented. QR codes are generated locally in the browser so sharing does not depend on an external QR API.
