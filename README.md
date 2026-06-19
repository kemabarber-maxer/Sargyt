# Marzban VPN Telegram Boty

Railway'de deploy edilip bilyan, Marzban panele awtomatik ulanyjy doredyan Telegram boty.

## Gurnama

### 1. GitHub Repo Doret

1. GitHub'da teze repo doredin we bu fayllary yuklen
2. [Railway](https://railway.app/)'e gidin
3. "New Project" -> "Deploy from GitHub repo"
4. Repony saylan
5. Cikis utgeyjilerini sazlan (asak seredin)
6. Deploy edin!

### 2. Cikis Utgeyjileri

Railway Dashboard -> **Variables** boluminden sazlan:

| Utgeyji | Dusundiris | Mysal |
|---------|------------|-------|
| `TELEGRAM_BOT_TOKEN` | BotFather'dan alnan token | `8761065175:AAHcSfuX2SSu1x4cJCGcAVAnwgNmzjTHhXU` |
| `MARZBAN_PANEL_URL` | Marzban panel URL'si | `https://luxuryy.turkmen-tagamlary.xyz:8443/chacakdyaie/ajehaishsel` |
| `MARZBAN_ADMIN_USERNAME` | Panel admin ulanyjy ady | `kema87` |
| `MARZBAN_ADMIN_PASSWORD` | Panel admin acar sozi | `frost` |
| `ADMIN_TELEGRAM_ID` | Admin Telegram ID | `8216327129` |

### 3. BotFather'dan Token Alma

1. Telegram'da [@BotFather](https://t.me/BotFather)'a gidin
2. `/newbot` buyrugyny iberin
3. Bot ady we ulanyjy ady berin
4. Tokeni gocurun we Railway'e yapyshdyryn

## Ulanylysy

Boty bashlatin:
```
/start
```

Teze ulanyjy doredin:
```
/create
```

Yagday barlan:
```
/status
```

## Buyruklar

| Buyruk | Dusundiris |
|--------|------------|
| `/start` | Boty bashlat |
| `/create` | Teze ulanyjy doret |
| `/status` | Yagday barla |
| `/help` | Komek menyusy |
| `/cancel` | Amaly yatyr |
