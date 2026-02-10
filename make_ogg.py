import asyncio
import os
import subprocess

VOICE = "ru-RU-SvetlanaNeural"  # можно заменить, например: ru-RU-DmitryNeural
RATE = "+0%"                   # скорость: "-10%" медленнее, "+10%" быстрее
VOLUME = "+0%"                 # громкость

IN_TSV = "ru.tsv"
OUT_DIR = "out"


async def synth_to_wav(text: str, wav_path: str):
    import edge_tts

    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=RATE, volume=VOLUME)
    await communicate.save(wav_path)


def wav_to_ogg_vorbis(wav_path: str, ogg_path: str):
    # OGG Vorbis (часто подходит для прошивок роботов)
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-ac", "1", "-ar", "24000", "-c:a", "libvorbis", "-q:a", "4", ogg_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tasks = []

    with open(IN_TSV, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fname, text = line.split("\t", 1)
            wav_path = os.path.join(OUT_DIR, fname.replace(".ogg", ".wav"))
            ogg_path = os.path.join(OUT_DIR, fname)

            async def job(text=text, wav_path=wav_path, ogg_path=ogg_path):
                await synth_to_wav(text, wav_path)
                wav_to_ogg_vorbis(wav_path, ogg_path)
                try:
                    os.remove(wav_path)
                except OSError:
                    pass

            tasks.append(job())

    # последовательно (надёжнее). Если хотите параллельно — скажите, дам версию с семафором.
    for t in tasks:
        await t


if __name__ == "__main__":
    asyncio.run(main())
