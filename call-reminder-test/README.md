# AgentCoolie Call Reminder Test

This is a standalone Twilio call prototype. It does not touch the main app.

## Setup

Copy `.env.example` to `.env` and fill in:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`

For Twilio trial accounts, the recipient number must be verified in Twilio Console first.

## Run

```powershell
python .\send_twilio_call.py --to "+919000000000"
```

Custom message:

```powershell
python .\send_twilio_call.py --to "+919000000000" --message "This is AgentCoolie. Reminder: send the client email now."
```
