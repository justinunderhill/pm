## Scripts Overview

- `start.ps1`, `start.bat`, `start.sh`: build Docker image and start container `pm-mvp` on port `8000`.
- `stop.ps1`, `stop.bat`, `stop.sh`: stop and remove container `pm-mvp` if present.
- Scripts optionally pass root `.env` to Docker at runtime when available.
