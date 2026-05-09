---
name: video-dubbing
description: |
  视频多语言配音工具链。将英文视频/音频转换为中文字幕并完成AI语音克隆配音。
  当用户提到"视频配音"、"配音clone"、"中文配音"、"语音克隆"、"video dubbing"、"多语言配音"时触发此skill。
  适用于视频国际化、多语言内容发布、播客配音等场景。
tags: [video, dubbing, voice-clone, subtitle, translation, ai-voice, i18n]
---

# 视频多语言配音工具链

将英文视频/音频自动转换为中文字幕并完成AI语音克隆配音的完整工作流。

## 何时使用

- 用户要求将英文视频转为中文字幕
- 需要为视频生成中文配音（语音克隆）
- 多语言视频内容制作
- 播客/课程/教程的国际配音
- 已有音频文件需要转录+翻译+配音

## 前置条件

确保以下CLI工具已全局安装：

```bash
# 1. 字幕提取（火山引擎语音识别）
pip install volcengine  # 或全局安装 volc-srt

# 2. 音频切片
cd cutaudio && npm install -g

# 3. AI语音克隆（VoxCPM2）
cd voxclone && npm install -g

# 4. 视频下载（YouTube）
pip install yt-dlp  # 或全局安装 yt-dlp

# 5. 音频提取
pip install yt-dlp  # getaudio依赖ffmpeg

# 6. 视频处理工具（removeaudio, align-video, subburn）
# 这些工具依赖ffmpeg，请确保ffmpeg已安装并加入PATH
```

**系统要求**：
- Python 3.10+
- ffmpeg（音频处理）
- yt-dlp（视频下载）
- CUDA GPU（推荐，用于语音克隆）
- 火山引擎API Key（语音识别）

## 工作流程

### 概览

```
YouTube URL → [yt-dlp] → 视频文件
                              ↓
                        [getaudio] → 音频文件
                              ↓
英文音频 → [volc-srt] → 英文字幕（带说话人）
                              ↓
                        [翻译+合句] → 配音优化版字幕（时间轴已合并）
                              ↓                ↓
                        [cutaudio] ← ─────────┘ 按合并时间轴切片
                              ↓
                              [voxclone] → 中文配音克隆（完整句子+数字转文字）
                              ↓
                        [removeaudio] → 无声视频
                              ↓
                        [align-video] → 配音视频（fade + 24kHz）
                              ↓
                        [getaudio] → 对齐后音频
                              ↓
                        [volc-srt] → 最终字幕
                              ↓
                        [subburn] → 字幕视频
```

### 步骤 1：下载 YouTube 视频

使用 `yt-dlp` 下载 YouTube 视频：

```bash
yt-dlp <YouTube URL> -o <输出视频路径>
```

**示例**：
```bash
yt-dlp "https://www.youtube.com/watch?v=K8Ros5RhJW4" -o test/video.mp4
```

**参数说明**：
- `-o`: 输出文件路径模板
- `-f best`: 下载最佳质量（默认）
- `--no-playlist`: 仅下载单个视频，不下载播放列表

**常见问题**：
- 如果下载失败，尝试更新 yt-dlp：`pip install -U yt-dlp`
- YouTube 需要 Cookie：添加 `--cookies cookies.txt` 参数
  - Cookie 文件可通过浏览器扩展（如 "Get cookies.txt LOCALLY"）导出
  - 或使用 `--cookies-from-browser chrome` 自动从 Chrome 获取
- 某些地区可能需要代理：`--proxy http://proxy:port`
- **JavaScript 运行时警告**：如果提示 `No supported JavaScript runtime`，安装 Node.js：
  ```bash
  # Windows（使用 winget）
  winget install OpenJS.NodeJS
  
  # 或下载安装：https://nodejs.org/
  ```

---

### 步骤 2：提取音频（含人声/背景音分离）

使用 `getaudio` 从视频中提取音频，推荐开启人声分离：

```bash
getaudio <视频文件路径> [-o <输出音频路径>] [--separate]
```

**示例**：
```bash
# 推荐：提取并分离人声/背景音
getaudio test/video.mp4 -o test/video.mp3 --separate

# 输出三个文件：
#   video.mp3        — 全频音频
#   video_vocals.mp3 — 纯净人声（给 volc-srt 和 cutaudio 用）
#   video_bgm.mp3    — 背景音乐（最终混音用）
```

**参数说明**：
- `input`: 输入视频文件路径（位置参数，不需要 `-i`）
- `-o, --output`: 输出音频文件路径
- `--separate`: 启用 Demucs 人声/背景音分离（默认关闭，配音推荐开启）
- `--model <name>`: Demucs 模型（默认 htdemucs_ft）

---

### 步骤 3：提取英文字幕

使用 `volc-srt` 将音频转为SRT字幕文件：

```bash
volc-srt <音频文件路径> -o <输出字幕路径> -f srt
```

**示例**：
```bash
# 使用纯净人声（video_vocals.mp3），而非全频音频，提升识别准确度
volc-srt test/video_vocals.mp3 -o test/video_en.srt --max-chars 100
```

**参数说明**：
- `audio`: 音频文件路径（mp3/wav/flac等）
- `-o, --output`: 输出字幕路径（默认与音频同名）
- `-f, --format`: 输出格式（srt/vtt/txt，默认srt）
- `--speaker`: 说话人分离（默认开启，自动识别多人对话，10人以内效果好）
- `--no-speaker`: 禁用说话人分离（单说话人场景可用，略快）
- `--no-punc`: 禁用自动标点（不建议）

**环境变量**（可选）：
```bash
set VOLC_API_KEY=your_api_key  # 优先使用环境变量配置API Key
```

**预期输出**：
- 有效SRT文件，包含连续序号、时间轴和文本
- 时间格式：`HH:MM:SS,mmm --> HH:MM:SS,mmm`
- 常见时长：10分钟音频约100-150条字幕

**常见问题**：
- API超时：增加 `--timeout 300` 参数
- 识别质量差：检查音频是否清晰，避免背景音乐过大

---

### 步骤 4：翻译为中文字幕

使用 **srt-translator skill** 进行翻译：

```bash
# 自动触发skill模式
/srt-translator test/video_en.srt --target-lang zh
```

**或手动执行**：
1. 读取SRT文件并解析
2. 提取专业术语，生成术语表
3. 用 merge_srt.py 预处理：计算合并组 + 数字批量转换
4. 分批次翻译合并后的条目（每批40-60条，可并行）
5. 输出最终配音优化版 `video_zh_dub.srt`

**翻译要求**：
- 保持时间轴格式完全不变
- 口语化、自然流畅
- 单行不超过40个中文字符
- 技术术语统一（参考术语表）
- ⚠️ 数字必须转文字（2%→百分之二，防止TTS念错）
- ⚠️ 语义不截断（半截句子合并）
- ⚠️ 同人不截断（间隙<300ms的连续语句合并）

**预期输出**：
- `video_zh_dub.srt`: 配音优化版（已合句+数字转文字，供 voxclone 使用）
- `video_glossary_zh.md`: 术语对照表

> ⚠️ 不在此步输出原版字幕，因为后续 align-video 会导致时间戳漂移。
> 烧字幕用的字幕在步骤11由 volc-srt 重新生成。

---

### 步骤 5：音频切片（获取参考音频）

使用 `cutaudio` 按**配音优化版字幕**（已合句）的时间轴将原音频切片：

> ⚠️ 不能按原版英文字幕切！翻译时会合并字幕条目（460→186），时间轴已变化。
> 必须用合并后的时间轴切，保证切片数量和顺序与 voxclone 字幕一一对应。

```bash
cutaudio -s <配音优化版字幕文件> -a <原音频文件> -o <输出目录> [--no-separate]
```

**示例**：
```bash
# 用配音优化版字幕（已合句）的时间轴来切，使用纯净人声作为参考音频
# cutaudio 会自动给每个切片加 80ms 前/160ms 后 padding，给 VoxCPM2 更多上下文
cutaudio -s test/video_zh_dub.srt -a test/video_vocals.mp3 -o test/audio_clips --no-separate
```

**参数说明**：
- `-s, --srt`: 配音优化版字幕路径（`video_zh_dub.srt`，不要用 `video_en.srt`）
- `-a, --audio`: 音频文件路径（mp3/wav/flac，必需）
- `-o, --out`: 输出目录（默认：`./output`）
- `--no-separate`: 跳过人声分离（如果音频已是纯净人声）

**重要提示**：
- 切片数量应与 `video_zh_dub.srt` 条目数一致
- **默认输出格式为 .mp3**，但 `voxclone` 要求 **.wav 格式**

**预期输出**：
```
audio_clips/
├── 0001.mp3
├── 0002.mp3
├── ...
└── 0321.mp3
```

---

### 步骤 6：格式转换（MP3 → WAV）

**关键步骤**：voxclone 只接受 `.wav` 格式参考音频

使用 ffmpeg 批量转换：

```bash
# Windows PowerShell
$clips = Get-ChildItem audio_clips/*.mp3
foreach ($clip in $clips) {
    $wavPath = $clip.FullName -replace '\.mp3$', '.wav'
    ffmpeg -i $clip.FullName -ar 16000 -ac 1 $wavPath -y 2>$null
}

# Linux/macOS
for f in audio_clips/*.mp3; do
    ffmpeg -i "$f" -ar 16000 -ac 1 "${f%.mp3}.wav" -y
done
```

**参数说明**：
- `-ar 16000`: 采样率16kHz（VoxCPM2推荐）
- `-ac 1`: 单声道
- `-y`: 覆盖已存在文件

**验证**：确保 `.wav` 文件数量与字幕条数完全一致。

---

### 步骤 7：中文配音克隆

使用 `voxclone` 生成中文配音（注意使用配音优化版字幕）：

```bash
voxclone dub -s <配音优化版字幕文件> [-a <参考音频目录>] -o <输出目录> [options]
```

**示例**：
```bash
# 语音克隆模式（提供参考音频）
voxclone dub -s test/video_zh_dub.srt -a test/audio_clips -o test/dubbed_output --device cuda --steps 10

# Voice Design 模式（无参考音频，纯文本合成）
voxclone dub -s test/video_zh_dub.srt -o test/dubbed_output --voice-style "沉稳男性声音"
```

**参数说明**：
- `-s, --subtitles`: 配音优化版字幕路径（`video_zh_dub.srt`）
- `-a, --audio-dir`: 参考音频切片目录（包含 `.wav` 文件，语音克隆模式需要）
- `--voice-style`: Voice Design 风格描述（与 `-a` 互斥，如 "沉稳男声"）
- `-o, --output`: 输出目录（默认：`output_dubbed`）
- `--device`: 计算设备（`cuda`/`cpu`，默认cuda）
- `--steps`: 推理步数（默认10，越高越好但越慢）
- `--guidance-scale`: 引导强度（默认2.0）
- `--python-env`: Python 解释器路径（默认自动检测，VoxCPM2 需要特定环境）
- `--model`: VoxCPM2 模型 ID（默认 `openbmb/VoxCPM2`）
- `--denoise`: 对参考音频降噪
- `--normalize`: 文本归一化

**Voice Design 模式**（无需参考音频）：
```bash
voxclone dub -s test/video_zh_dub.srt -o test/dubbed_output --voice-style "沉稳男性声音" --steps 10
```

**重要提示**：
- 必须使用 `video_zh_dub.srt`（配音优化版），不要用原版
- VoxCPM2 输出 48kHz 高品质音频，内置 fade + RMS 归一化
- VoxCPM2 比 OmniVoice 音质更好，tokenizer-free 连续表示

**预期输出**：
```
dubbed_output/
├── 0001.wav
├── 0002.wav
├── ...
└── 0321.wav
```

---

### 步骤 7：去除原视频音频

使用 `removeaudio` 获取无声视频：

```bash
removeaudio <视频文件路径> [-o <输出视频路径>]
```

**示例**：
```bash
removeaudio test/video.mp4 -o test/video_no_audio.mp4
```

**参数说明**：
- `input`: 输入视频文件路径（位置参数，不需要 `-i`）
- `-o, --output`: 输出无声视频文件路径（默认：`input_no_audio.<ext>`）
- `-y`: 覆盖已存在文件

---

### 步骤 8：对齐音频和视频

使用 `align-video` 将配音后的音频与无声视频对齐：

```bash
align-video <中文字幕路径> <视频路径> <配音音频目录> <输出视频路径>
```

**示例**：
```bash
# 两级变速对齐默认开启（全局+局部双调，防止极端变速导致音质劣化）
# 如需关闭：--no-adaptive-speed
align-video test/video_zh_dub.srt test/video_no_audio.mp4 test/dubbed_output test/aligned.mp4
```

**参数说明**（位置参数）：
1. `srt`: 配音优化版字幕（`video_zh_dub.srt`）
2. `video`: 无声视频路径
3. `dubbed_dir`: 配音音频切片目录
4. `output`: 输出对齐后的视频路径

**可选参数**：
- `--workers`: 并发线程数（默认4）
- `--resume`: 断点续传
- `--rife`: 使用 RIFE GPU 插帧
- `--adaptive-speed`: 启用两级变速对齐（默认关闭）
- `--audio-stretch`: 旧版音频拉伸模式
- `--scene-snap`: 智能场景边界对齐

**可选参数**：
- `--workers`: 并发处理线程数（默认4）
- `--resume`: 断点续传（从上次中断处继续）
- `--no-audio-stretch`: 禁用音频拉伸
- `--scene-snap`: 智能场景边界对齐
- `--rife`: 使用 RIFE GPU 插帧（默认关闭）

**重要提示**：
- 确保字幕时间轴与视频画面匹配
- 对齐后的视频会自动匹配原始视频时长
- 处理时间较长，支持断点续传（`--resume`）

---

### 步骤 9：混入背景音乐

将保留的背景音以 30% 音量混入配音视频，掩盖片段衔接痕迹：

```bash
ffmpeg -i test/aligned.mp4 -i test/video_bgm.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.30[a1];[a0][a1]amix=inputs=2:duration=longest:normalize=0[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k test/aligned_with_bgm.mp4 -y
```

> 背景音来自步骤2的 `--separate` 输出 (`video_bgm.mp3`)。
> 如果步骤2未开启 `--separate`，跳过此步。

---

### 步骤 10：提取对齐后的音频

align-video 处理后配音位置和时间戳已变化，必须重新提取音频：

```bash
getaudio <对齐后的视频路径> -o <输出音频路径>
```

**示例**：
```bash
getaudio test/aligned.mp4 -o test/aligned_dubbed.wav
```

---

### 步骤 10：提取最终字幕

从对齐后的音频重新获取字幕（时间戳已变化）：

```bash
# --max-chars 20: 适合字幕显示，避免单行过长
# --no-speaker: 不输出说话人标记（最终字幕是给人看的，不需要 [说话人1]）
volc-srt <对齐后的音频路径> -o <输出字幕路径> --max-chars 20 --no-speaker
```

**示例**：
```bash
volc-srt test/aligned_dubbed.wav -o test/final.srt --max-chars 20 --no-speaker
```

> ⚠️ 这里的参数与步骤3不同：
> - `--max-chars 20`（步骤3是100）：最终字幕要分行显示，字符数越少越好
> - `--no-speaker`（步骤3是默认开启）：最终字幕不需要 [说话人X] 标记

---

### 步骤 11：烧制字幕到视频

使用 `subburn` 将翻译后的字幕烧制到视频上：

```bash
subburn <视频路径> <字幕路径> [输出路径]
```

**示例**：
```bash
subburn test/dubbed_video.mp4 test/video_zh.srt test/final_dubbed_video.mp4
```

**参数说明**（位置参数）：
1. `video`: 输入视频文件路径
2. `srt`: 字幕SRT文件路径
3. `output`: 输出带字幕的视频路径（默认自动生成）

---

### 步骤 6（可选）：合并配音片段

如果需要合并为完整音频：

```bash
# 使用ffmpeg合并（按文件名排序）
ffmpeg -f concat -safe 0 -i <(for f in dubbed_output/*.wav; do echo "file '$PWD/$f'"; done) -c copy final_dubbed.wav
```

---

## 完整工作流示例

```bash
# 1. 下载YouTube视频
yt-dlp "https://www.youtube.com/watch?v=K8Ros5RhJW4" -o test/video.mp4 --cookies G:\cookies\youtube_converted.txt

# 2. 提取音频 + 人声/背景音分离（推荐开启 --separate）
getaudio test/video.mp4 -o test/video.mp3 --separate
# 输出: video.mp3 + video_vocals.mp3（纯净人声）+ video_bgm.mp3（背景音）

# 3. 提取英文字幕（用纯净人声，识别更准，说话人默认开启）
volc-srt test/video_vocals.mp3 -o test/video_en.srt --max-chars 100

# 4. 翻译为配音优化版字幕（含合句+数字转文字+口语化）
/srt-translator test/video_en.srt --target-lang zh
# 输出: video_zh_dub.srt（已合句，给 voxclone 用）

# 5. 按配音优化版时间轴切片（自动加 80ms/160ms padding）
cutaudio -s test/video_zh_dub.srt -a test/video_vocals.mp3 -o test/audio_clips --no-separate

# 6. MP3转WAV
$clips = Get-ChildItem test/audio_clips/*.mp3
foreach ($clip in $clips) {
    $wavPath = $clip.FullName -replace '\.mp3$', '.wav'
    ffmpeg -i $clip.FullName -ar 16000 -ac 1 $wavPath -y 2>$null
}

# 7. 中文配音克隆（fade + 完整句子 + 数字转文字）
voxclone dub -s test/video_zh_dub.srt -a test/audio_clips -o test/dubbed_output --device cuda --steps 10

# 8. 去除原视频音频
removeaudio test/video.mp4 -o test/video_no_audio.mp4

# 9. 对齐音频和视频（afade + 24kHz，可选 --adaptive-speed 两级变速）
align-video test/video_zh_dub.srt test/video_no_audio.mp4 test/dubbed_output test/aligned.mp4

# 10. 混入背景音乐（掩盖片段衔接痕迹，BGM 30%音量）
ffmpeg -i test/aligned.mp4 -i test/video_bgm.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.30[a1];[a0][a1]amix=inputs=2:duration=longest:normalize=0[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k test/aligned_with_bgm.mp4 -y

# 11. 提取对齐后音频 → 重新获取字幕 → 烧录
getaudio test/aligned_with_bgm.mp4 -o test/aligned_dubbed.wav
volc-srt test/aligned_dubbed.wav -o test/final.srt --max-chars 20 --no-speaker
subburn test/aligned_with_bgm.mp4 test/final.srt test/video_final.mp4
```
```

---

## 关键经验总结

### 1. 工具依赖关系

| 工具 | 输入 | 输出 | 依赖 |
|------|------|------|------|
| yt-dlp | YouTube URL | 视频文件 | yt-dlp |
| getaudio | 视频文件 | 音频文件 | ffmpeg |
| volc-srt | 音频文件 | SRT字幕 | 火山API Key |
| srt-translator | 英文字幕 | 中文字幕 | LLM翻译能力 |
| cutaudio | 音频+SRT | 音频切片 | ffmpeg |
| voxclone | 字幕+WAV切片 | 配音片段 | VoxCPM2模型、CUDA |
| removeaudio | 视频文件 | 无声视频 | ffmpeg |
| align-video | 视频+字幕+音频 | 对齐后的音频 | ffmpeg |
| subburn | 视频+字幕 | 带字幕视频 | ffmpeg |

### 2. 格式兼容性陷阱

**最大坑点**：`cutaudio` 输出 `.mp3`，但 `voxclone` 只接受 `.wav`
- 必须手动进行格式转换
- 推荐使用 16kHz 单声道 WAV

### 3. 文件命名约定

- 字幕切片与参考音频必须按序号一一对应
- `0001.wav` 对应字幕第1条
- 文件名前导零必须一致（0001, 0002... 而非 1, 2...）

### 4. 质量优化建议

**语音识别**：
- 原音频尽量纯净（少背景音乐）
- 说话清晰、语速适中
- 说话人分离默认开启（`--no-speaker` 可关闭，用于单说话人场景）

**翻译质量**：
- 先生成术语表，确保专业术语统一
- 分批次翻译避免上下文丢失
- 口语化处理，适合字幕阅读

**配音质量**：
- `--steps 32` 为基础，64质量更好
- `--speed` 可调节语速匹配画面
- 参考音频切片时长与字幕时长应匹配

### 5. 性能优化

- **GPU加速**：voxclone使用CUDA，速度提升10倍以上
- **批量处理**：长视频（>30分钟）建议分段处理
- **内存管理**：321条字幕约需8GB显存

---

## 故障排除

### 问题：yt-dlp 提示 "No supported JavaScript runtime"

**解决**：安装 Node.js 作为 JavaScript 运行时：
```bash
# Windows（使用 winget）
winget install OpenJS.NodeJS

# 或下载安装：https://nodejs.org/
```

### 问题：yt-dlp 提示 "Sign in to confirm you're not a bot"

**解决**：提供 YouTube Cookie（推荐使用 `youtube_converted.txt`）：
```bash
# 方法1：使用 cookies 文件（推荐，无需浏览器）
yt-dlp "URL" --cookies G:\cookies\youtube_converted.txt

# 方法2：从浏览器自动获取（需要关闭浏览器）
yt-dlp "URL" --cookies-from-browser chrome

# 方法3：先导出再转换格式
yt-dlp "URL" --cookies-from-browser chrome --cookies G:\cookies\youtube.txt --skip-download
# 然后用转换后的 cookie 下载
yt-dlp "URL" -o output.mp4 --cookies G:\cookies\youtube_converted.txt
```

### 问题：volc-srt 返回API错误

**解决**：
```bash
# 检查API Key
set VOLC_API_KEY=your_key

# 增加超时
volc-srt audio.mp3 --timeout 600
```

### 问题：cutaudio 切片数量与字幕不匹配

**原因**：SRT格式错误或时间轴重叠
**解决**：
```bash
# 验证SRT格式
ffmpeg -i subtitle.srt  # 检查是否有解析错误
```

### 问题：voxclone 提示缺少WAV文件

**原因**：参考音频是MP3格式
**解决**：执行步骤6的格式转换

### 问题：配音效果不佳/有杂音

**原因**：
1. 参考音频包含背景音乐
2. 切片音频过短（<0.5秒）
3. 模型未正确加载

**解决**：
- 去掉 `--no-separate`，让人声分离
- 检查短音频切片并合并
- 验证模型路径：`--model-path /path/to/VoxCPM2-bf16`

### 问题：CUDA out of memory

**解决**：
```bash
# 降低batch size或使用CPU
voxclone dub ... --device cpu
```

### 问题：align-video 处理中断

**解决**：使用断点续传功能：
```bash
# 从中断处继续
align-video test/video_zh.srt test/video.mp4 test/dubbed_output test/aligned.mp4 --resume
```

### 问题：removeaudio 提示 "Unknown option: -i"

**原因**：removeaudio 使用位置参数而非 `-i` 选项
**解决**：
```bash
# 正确用法
removeaudio video.mp4 -o output.mp4

# 错误用法（不要加 -i）
removeaudio -i video.mp4 -o output.mp4
```

---

## 输出文件结构

```
project/
├── video.mp4                    # 原始视频（步骤1）
├── video.mp3                    # 提取的音频（步骤2）
├── video_en.srt                 # 英文字幕（步骤3）
├── video_zh.srt                 # 中文字幕（步骤4）
├── video_glossary_zh.md         # 术语表（步骤4）
├── audio_clips/                 # 音频切片（步骤5）
│   ├── 0001.mp3                 # 原始切片（MP3）
│   ├── 0001.wav                 # 转换后（WAV）
│   ├── 0002.mp3
│   ├── 0002.wav
│   └── ...
├── dubbed_output/               # 中文配音（步骤7）
│   ├── 0001.wav
│   ├── 0002.wav
│   └── ...
├── video_no_audio.mp4           # 无声视频（步骤8）
├── aligned_dubbed.wav           # 对齐后的音频（步骤9）
├── dubbed_video.mp4             # 配音视频（步骤10）
└── final_dubbed_video.mp4       # 最终带字幕视频（步骤12）
```

---

## 高级用法

### 批量处理多个视频

```bash
# 遍历目录下所有mp3
for file in *.mp3; do
    base=$(basename "$file" .mp3)
    volc-srt "$file" -o "${base}_en.srt"
    /srt-translator "${base}_en.srt" --target-lang zh
    cutaudio -s "${base}_en.srt" -a "$file" -o "${base}_clips"
    # ... 转换格式并配音
done
```

### 自定义模型路径

```bash
voxclone dub -s subs.srt -a clips/ -o out/ \
  --model "openbmb/VoxCPM2" \
  --steps 10
  --steps 64 \
  --speed 1.1
```

---

## 注意事项

1. **API费用**：volc-srt使用火山引擎API，注意用量和费用
2. **版权问题**：AI克隆语音仅供个人学习，商业使用需注意授权
3. **备份原文件**：处理前备份原始音频/视频
4. **长视频处理**：超过30分钟的视频建议分段处理，避免内存溢出
5. **术语一致性**：翻译前先确认专业术语，避免前后不一致

---

## 相关链接

- **VoxCPM2**: https://github.com/k2-fsa/VoxCPM2
- **火山引擎语音识别**: https://www.volcengine.com/product/speech
- **srt-translator skill**: 字幕翻译专用skill

---

**版本**: v1.0
**最后更新**: 2026-05-04
**维护者**: Claude Code
**基于实践**: 成功处理28分钟英文视频（321条字幕）的完整经验
