# Whatsanuker POC

This proof-of-concept runs entirely on your Mac using Docker Desktop.

## Setup

```bash
brew install docker
git clone <this repo>
cd whatsanuker
cp .env.example .env  # fill in your AWS keys and WhatsApp IDs
docker compose up --build
# scan the QR code printed by the bot container
```

## Testing and cleanup

Run unit tests:

```bash
pytest llm/tests
npm --prefix bot test
```

Build the containers:

```bash
docker compose build
```

Stop and wipe authentication/logs:

```bash
docker compose down -v
rm -rf bot/.wwebjs_auth logs/
```
