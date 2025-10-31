# 🎬 SoraStitcher

**SoraStitcher** is a lightweight Python tool for combining multiple `.mp4` clips into one seamless video. You choose a starting clip, and the rest are automatically shuffled into a random sequence for creative or batch compilation purposes.

---

## ✨ Features

* 🧩 Automatically combines all `.mp4` files in a folder
* 🎲 Randomizes clip order after your chosen starting file
* ⚙️ Normalizes video size, codec, FPS, and audio to avoid mismatches
* 🧠 Optional random seed for consistent shuffle results
* ⚡ `--fast` mode to skip re-encoding (when clips already match)
* 🖥️ Uses `ffmpeg` directly — no third-party Python libraries required

---

## 🧰 Requirements

* Python 3.8 or higher
* [FFmpeg](https://ffmpeg.org/) installed and added to your system PATH

To confirm FFmpeg is available:

```bash
ffmpeg -version
```

---

## 🚀 Usage Examples

### Basic Example

```bash
python SoraStitcher.py --folder ./videos --start intro.mp4
```

### Custom Output Example

```bash
python SoraStitcher.py --folder ./project_videos --start scene1.mp4 -o FinalEdit.mp4
```

### Set Resolution, FPS, and Shuffle Seed

```bash
python SoraStitcher.py \
  --folder ./clips \
  --start opening.mp4 \
  -o Sora_Reel.mp4 \
  --fps 30 \
  --width 1920 \
  --height 1080 \
  --seed 42
```

### Fast Concatenation Mode

If your clips already share identical encoding settings, you can skip normalization:

```bash
python SoraStitcher.py --folder ./videos --start take1.mp4 --fast
```

---

## ⚙️ Command Line Options

| Option                | Description                                                             |
| --------------------- | ----------------------------------------------------------------------- |
| `--folder`            | Directory containing `.mp4` files (non-recursive)                       |
| `--start`             | Name of the first clip (must be inside the folder)                      |
| `-o, --output`        | Output file name (default: `Sora_Reel.mp4`)                             |
| `--fps`               | Output frames per second (default: 30)                                  |
| `--width`, `--height` | Output resolution (defaults to first clip’s size)                       |
| `--crf`               | x264 quality (lower = higher quality; default: 20)                      |
| `--preset`            | x264 speed/quality preset (`ultrafast` → `veryslow`; default: `medium`) |
| `--audio-bitrate`     | Audio bitrate (default: `192k`)                                         |
| `--seed`              | Random seed for reproducible shuffle                                    |
| `--fast`              | Skips re-encoding; faster but requires matching formats                 |

---

## 🧠 How It Works

1. Gathers all `.mp4` files in the target folder.
2. Sets the `--start` clip as the first in sequence.
3. Randomizes the remaining clips (optionally using a seed).
4. Optionally re-encodes and normalizes each clip (for consistency).
5. Concatenates them into a single continuous output file.

---

## ⚠️ Notes

* Normalization ensures compatibility but can take time.
* Fast mode (`--fast`) skips normalization — use only if all clips share identical encoding.
* The app uses `ffmpeg` and `ffprobe` under the hood for reliability.

---

## 📦 Example Output

```
Found 10 clips. Starting with: intro.mp4
Target size: 1920x1080 @ 30fps
Normalizing clips (this may take a while)...
[1/10] intro.mp4 → part_0000.mp4
[2/10] clip1.mp4 → part_0001.mp4
...
Concatenating...
Done → /output/Sora_Reel.mp4
```

---

## 📜 License

Released under the MIT License — free for personal and commercial use.

---

## 👨‍💻 Author

Created by **Joseph Reynolds (@darklodus)**

> “A simple way to stitch your story together.”