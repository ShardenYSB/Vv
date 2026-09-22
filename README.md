# OP Bot core

Safe, framework-independent core for an Aiogram 3 bot. `SponsorService` sends active
blacklist IDs to BotoHub's extended endpoint and then filters returned tasks locally.
`LinkResolver` permits only supported Telegram URL formats, so malformed URLs cannot
create invalid inline buttons. SQL migration contains moderation/audit tables.
