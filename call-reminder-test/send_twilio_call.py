from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.parse
import urllib.request


def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def place_call(to_number: str, message: str) -> dict[str, str]:
    account_sid = required_env("TWILIO_ACCOUNT_SID")
    auth_token = required_env("TWILIO_AUTH_TOKEN")
    from_number = required_env("TWILIO_FROM_NUMBER")

    twiml = f"""
<Response>
  <Say voice="alice">{message}</Say>
</Response>
""".strip()

    form = urllib.parse.urlencode(
        {
            "To": to_number,
            "From": from_number,
            "Twiml": twiml,
        }
    ).encode("utf-8")

    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json",
        data=form,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return {"status": str(response.status), "body": body}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Twilio returned HTTP {exc.code}:\n{body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Twilio: {exc}") from exc


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Place a test AgentCoolie reminder call.")
    parser.add_argument("--to", required=True, help="Recipient phone number, e.g. +919000000000")
    parser.add_argument(
        "--message",
        default="This is AgentCoolie. Your important task is due now.",
        help="Text Twilio should speak during the call.",
    )
    args = parser.parse_args()

    result = place_call(args.to, args.message)
    print(f"Twilio accepted the call request. HTTP {result['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
