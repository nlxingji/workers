import os
import re
import subprocess
import requests
from mutagen.flac import FLAC, Picture

def safe_decode(b):
    if isinstance(b, str):
        return b
    for enc in ['utf-8', 'gbk', 'big5', 'shift_jis']:
        try:
            return b.decode(enc)
        except:
            continue
    return b.decode('utf-8', errors='replace')

def fallback_title_artist(filename):
    base = os.path.splitext(os.path.basename(filename))[0]

    # 支持多种分隔符：半角 - 、全角－、中文—
    match = re.split(r'\s*[-－—–]\s*', base, maxsplit=1)
    if len(match) == 2:
        artist, title = match
    else:
        artist, title = "", base

    return artist.strip(), title.strip()

def convert_to_flac(wav_path, flac_path):
    subprocess.run([
        'ffmpeg', '-y', '-i', wav_path,
        '-compression_level', '5', flac_path
    ], check=True)

def embed_tags(flac_path, artist, title):
    audio = FLAC(flac_path)
    audio['artist'] = artist
    audio['title'] = title
    audio.save()

def get_lyrics_from_netease(artist, title):
    headers = {
        'Referer': 'https://music.163.com/',
        'User-Agent': 'Mozilla/5.0'
    }
    search_url = "https://music.163.com/api/search/pc"
    search_data = {
        "s": f"{artist} {title}",
        "offset": 0,
        "limit": 1,
        "type": 1
    }
    try:
        search_resp = requests.post(search_url, data=search_data, headers=headers)
        result = search_resp.json()
        if result['result']['songCount'] == 0:
            print(f"[!] 未找到歌词: {artist} - {title}")
            return None
        song_id = result['result']['songs'][0]['id']
        lyric_url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1"
        lyric_resp = requests.get(lyric_url, headers=headers)
        lyric_data = lyric_resp.json()
        if 'lrc' in lyric_data and 'lyric' in lyric_data['lrc']:
            return lyric_data['lrc']['lyric']
        else:
            return None
    except Exception as e:
        print(f"[X] 抓取歌词异常: {e}")
        return None

def embed_lyrics(flac_path, artist, title):
    audio = FLAC(flac_path)
    for ext in ['.lrc', '.txt']:
        local_lyric = f"{artist} - {title}{ext}"
        if os.path.exists(local_lyric):
            with open(local_lyric, 'r', encoding='utf-8', errors='ignore') as f:
                lyrics = f.read()
                audio["LYRICS"] = lyrics
                audio.save()
                print(f"[✓] 本地歌词已嵌入: {local_lyric}")
                return
    lyrics = get_lyrics_from_netease(artist, title)
    if lyrics:
        audio["LYRICS"] = lyrics
        audio.save()
        print(f"[✓] 网易云歌词已嵌入: {artist} - {title}")

def embed_cover(flac_path, artist, title):
    for ext in ['.jpg', '.png', '.webp']:
        cover_file = f"cover{ext}"
        if os.path.exists(cover_file):
            _embed_picture(flac_path, cover_file)
            return
    query = f"{artist} {title}"
    url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&media=music&limit=1"
    try:
        r = requests.get(url)
        data = r.json()
        if data['resultCount']:
            img_url = data['results'][0]['artworkUrl100'].replace('100x100', '600x600')
            img_data = requests.get(img_url).content
            with open("temp_cover.jpg", 'wb') as f:
                f.write(img_data)
            _embed_picture(flac_path, "temp_cover.jpg")
            os.remove("temp_cover.jpg")
    except Exception as e:
        print(f"[!] 封面抓取失败: {e}")

def _embed_picture(flac_path, img_path):
    pic = Picture()
    pic.type = 3
    pic.mime = "image/jpeg" if img_path.endswith(".jpg") else "image/png"
    with open(img_path, 'rb') as f:
        pic.data = f.read()
    audio = FLAC(flac_path)
    audio.clear_pictures()
    audio.add_picture(pic)
    audio.save()
    print(f"[✓] 封面已嵌入: {img_path}")

def process_audio(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".wav":
        artist, title = fallback_title_artist(filepath)
        flac_name = f"{artist} - {title}.flac"
        flac_path = os.path.join(".", flac_name)
        convert_to_flac(filepath, flac_path)
        embed_tags(flac_path, artist, title)
        embed_lyrics(flac_path, artist, title)
        embed_cover(flac_path, artist, title)
        # os.remove(filepath)
        print(f"[✓] WAV 转换完成并删除: {filepath}")
    elif ext == ".flac":
        flac_path = filepath
        audio = FLAC(flac_path)
        guess_artist, guess_title = fallback_title_artist(flac_path)
        artist = guess_artist
        title = guess_title
        embed_tags(flac_path, artist, title)
        print(f"[~] 标签已补全: {artist} - {title}")

def main():
    # 你可以在这里指定一个额外的目录列表
    dirs_to_scan = ["./","/vol2/1000/download"]  # 这里替换成你需要的目录
    for dir_path in dirs_to_scan:
        for root, _, files in os.walk(dir_path):
            for name in files:
                if name.lower().endswith((".wav", ".flac")):
                    filepath = os.path.join(root, name)
                    print(f"[~] 正在处理: {filepath}")
                    process_audio(filepath)

if __name__ == "__main__":
    main()
