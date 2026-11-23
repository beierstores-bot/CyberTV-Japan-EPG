# CyberTV Japan EPG

Automated merger for Japanese XMLTV sources, including a dedicated ABEMA feed.

## Files published
- `CYBERTV_JAPAN_MASTER.xml.gz` — merged XMLTV gzip feed
- `coverage-report.json` — source results and exact `tvg-id` coverage

## Important mapping rule
The playlist snapshot in `config/channel-mapping.json` contains channel display names,
groups and identifiers only. It does **not** contain stream URLs. Existing `tvg-id`
values are treated as authoritative. The builder never invents IDs or programme data.
Channels without a verified `tvg-id` are reported for manual mapping.

## Setup
1. Create this repository as public.
2. Upload all files from this package, preserving folder structure.
3. In GitHub, open **Settings → Pages** and select **GitHub Actions** as the build/deployment source.
4. Open **Actions → Build CyberTV Japan Master EPG → Run workflow**.
5. After a successful deployment, the feed should be available at:

   `https://beierstores-bot.github.io/CyberTV-Japan-EPG/CYBERTV_JAPAN_MASTER.xml.gz`

The scheduled workflow runs every 12 hours (UTC). It retains source channel IDs and
programme records and removes exact duplicate programme entries.

## Limitations
A channel is not guaranteed to have schedule data merely because it appears in the
playlist. Coverage depends on the upstream EPG providers and verified ID mapping.
Check `coverage-report.json` after each build. Do not publish a "complete 220-channel"
claim until all 220 playlist entries have genuine matching schedule data.
