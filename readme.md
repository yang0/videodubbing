# 能够使用的cli工具
- [audioclone](https://github.com/yang0/audioclone): 根据字幕和原音频切片进行声音克隆
- [getaudio](https://github.com/yang0/getaudio): 从视频中剥离出音频，支持人声/背景音分离
- [cutaudio](https://github.com/yang0/cutaudio): 根据字幕文件将一个大音频切成多个音频切片
- [volc-srt](https://github.com/yang0/volasr): 根据音频获取字幕文件，支持说话人分离
- [removeaudio](https://github.com/yang0/removeaudio): 把音频从视频中去除
- [align-video](https://github.com/yang0/alignaudio): 把音频和视频对齐。输入：无声的视频，翻译后的字幕，对应字幕的音频切片, 输出：配好音的音频
- [subburn](https://github.com/yang0/subburn): 把字幕烧制到视频上

# Skills
- [srt-translator](https://github.com/yang0/srt-trans): 字幕翻译skill，支持口语化翻译、合句、数字转文字、字数控时
- [video-dubbing](https://github.com/yang0/videodubbing): 视频配音完整流程skill

# 典型的youtube视频配音流程
用户输入：youtube url， 目标语言
处理流程：
1. yt-dlp 下载视频
2. volc-srt --max-chars 100  获取视频的字幕
3. 用srt-trans这个skill 翻译字幕
4. 用getaudio获取原语音音频
5. 用cutaudio把原语音音频切片
6. 把所有切片mp3转wav
7. 声音clone的时候数字，百分数之类的经常念不对，请出一份用于声音克隆用的字幕，把数字改成能够用目标语言准确念出来的文字。
8. 用audioclone以克隆的方式，把原语音音频切片转换成目标语言音频切片
9. 用removeaudio 获取原视频的无声版本
10. 用align-video，把配音后的切片和无声视频对齐。
11. 用getaudio获取对齐后的配音音频
12. 用volc-srt获取字幕
13. 用subburn把翻译后的字幕烧制到配好音的视频上

# yt-dlp
- 需要启动bgutil-start.cmd
- youtube cookie： G:\cookies\youtube_converted.txt
- example: yt-dlp https://www.youtube.com/watch?v=DoW2AnXFzoo -o test.mp4 --no-playlist --cookies G:\cookies\youtube_converted.txt