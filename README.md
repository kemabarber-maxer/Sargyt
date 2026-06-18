# Marzban VPN Telegram Boty

Railway'de deploy edilip bilýän, Marzban panele awtomatik ulanyjy döredýän Telegram boty.

## Özellikler

- 🤖 Telegram üsti bilen ulanyjy döretme
- 📊 Awtomatik 125 GB data limiti
- ⏰ Awtomatik 30 günlük wagt
- 🔗 Abunalyk linki we konfigurasiýa linkleri
- 👮 Admin barlagy

## Gurnama

### 1. Railway'de Deploy Etme

1. GitHub'da täze repo dörediň we bu faýllary ýükläň
2. [Railway](https://railway.app/)'e gidiň
3. "New Project" → "Deploy from GitHub repo"
4. Repony saýlaň
5. Çykyş üýtgeýjilerini sazlaň (aşak serediň)
6. Deploy ediň!

### 2. Çykyş Üýtgeýjileri

Railway Dashboard → Variables bölüminden sazlaň:

| Üýtgeýji | Düşündiriş | Mysal |
|----------|------------|-------|
| `TELEGRAM_BOT_TOKEN` | BotFather'dan alnan token | `123456:ABC...` |
| `MARZBAN_PANEL_URL` | Marzban panel URL'si | `https://luxuryy.turkmen-tagamlary.xyz:8443` |
| `MARZBAN_ADMIN_USERNAME` | Panel admin ulanyjy ady | `admin` |
| `MARZBAN_ADMIN_PASSWORD` | Panel admin açar sözi | `password` |
| `ADMIN_TELEGRAM_ID` | Admin Telegram ID (opsional) | `123456789` |

### 3. BotFather'dan Token Alma

1. Telegram'da [@BotFather](https://t.me/BotFather)'a gidiň
2. `/newbot` buýrugyny iberiň
3. Bot ady we ulanyjy ady beriň
4. Tokeni göçüriň we Railway'e ýapyşdyryň

## Ulanylyşy

Boty başlatyň:
```
/start
```

Täze ulanyjy dörediň:
```
/create
```

Ýagdaý barlaň:
```
/status
```

## Buýruklar

| Buýruk | Düşündiriş |
|--------|------------|
| `/start` | Boty başlat |
| `/create` | Täze ulanyjy döret |
| `/status` | Ýagdaý barla |
| `/help` | Kömek menýusy |
| `/cancel` | Amaly ýatyr |
