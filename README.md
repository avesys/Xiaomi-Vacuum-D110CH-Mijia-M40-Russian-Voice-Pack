# Xiaomi Vacuum D110CH (Mijia M40) Russian Voice Pack (MIoT Local)

This repository contains a **Russian voice pack workflow** for the
**`xiaomi.vacuum.d110ch` (Mijia M40)** model:

1.  Generate `.ogg` files (OGG Vorbis, mono, 24 kHz) from a TSV list
    using **Microsoft Edge TTS** (`edge-tts`) + `ffmpeg`.
2.  Pack the generated files into a `voicepack.tar.gz`.
3.  Host the archive on a local HTTP server.
4.  Instruct the robot to download & install the voice pack via **MIoT
    local** using IP + token (`python-miio`).

> ⚠️ Disclaimer: Use at your own risk. Modifying/setting custom voice
> packs may be unsupported by the vendor and could affect warranty or
> device behavior. Never publish your Xiaomi token.

------------------------------------------------------------------------

## Repository contents

-   `make_ogg.py` --- TTS generator (TSV → WAV → OGG Vorbis)
-   `ru.tsv` --- mapping `filename.ogg<TAB>Text`
-   `out/` --- generated `.ogg` output directory (created automatically)
-   `set_voice_d110ch.py` --- installs voice pack via MIoT local (URL +
    md5 + size)

------------------------------------------------------------------------

## Requirements

### For voice generation

-   Python 3
-   `edge-tts`
-   `ffmpeg`

Install:

``` bash
python3 -m pip install --user edge-tts
sudo apt update
sudo apt install -y ffmpeg
```

### For installing to the robot (MIoT local)

-   Python 3
-   `python-miio`

Install:

``` bash
sudo apt update
sudo apt install -y python3-pip
python3 -m pip install --user python-miio
```

------------------------------------------------------------------------

## 1) Generate OGG files

Install `edge-tts`:

``` bash
python3 -m pip install --user edge-tts
```

Make sure `ffmpeg` is installed:

``` bash
sudo apt update
sudo apt install -y ffmpeg
```

Run:

``` bash
python3 make_ogg.py
```

Result: `.ogg` files will be placed into `out/`.

------------------------------------------------------------------------

## 2) Create the voice pack archive and host it

### Create `voicepack.tar.gz` from `out/` (Ubuntu)

From the repository root:

``` bash
tar -czvf voicepack.tar.gz -C out .
```

Check contents:

``` bash
tar -tzf voicepack.tar.gz | head
```

### Compute `md5` and `size` (Ubuntu)

MD5:

``` bash
md5sum voicepack.tar.gz
```

Only hash:

``` bash
md5sum voicepack.tar.gz | awk '{print $1}'
```

File size:

``` bash
stat -c%s voicepack.tar.gz
```

Alternative:

``` bash
wc -c < voicepack.tar.gz
```

### Host on local HTTP server

``` bash
python3 -m http.server 8000 --bind 0.0.0.0
```

URL example:

    http://YOUR-LAN-IP:8000/voicepack.tar.gz

Find LAN IP:

``` bash
ip -4 addr show
```

------------------------------------------------------------------------

## 3) Get robot IP and token

Option A:

``` bash
miiocli discover
```

Option B:

``` bash
miiocli cloud list
```

------------------------------------------------------------------------

## 4) Check current voice/status

``` bash
python3 set_voice_d110ch.py --ip 192.168.1.50 --token YOURTOKEN status
```

------------------------------------------------------------------------

## 5) Install voice pack

Using known md5 and size:

``` bash
python3 set_voice_d110ch.py --ip 192.168.1.50 --token YOURTOKEN install \
  --lang-id RU \
  --url "http://YOUR-SERVER/voicepack.tar.gz" \
  --md5 "0123456789abcdef0123456789abcdef" \
  --size 4325024 \
  --wait 120
```

Auto compute md5/size:

``` bash
python3 set_voice_d110ch.py --ip 192.168.1.50 --token YOURTOKEN install \
  --lang-id RU \
  --url "http://YOUR-SERVER/voicepack.tar.gz" \
  --file ./voicepack.tar.gz \
  --wait 120
```

------------------------------------------------------------------------

## Troubleshooting

-   Robot can't download:
    -   Check URL from another device
    -   Ensure correct LAN IP
    -   Disable firewall
-   Install doesn't start:
    -   Verify token (32 hex)
    -   Check robot IP
-   Audio rejected:
    -   Must be OGG Vorbis mono 24kHz
