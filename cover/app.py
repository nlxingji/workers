from flask import Flask, request, Response
import requests

app = Flask(__name__)

def query_itunes_cover(artist=None, album=None, title=None):
    if not artist:
        return None

    term = f"{artist} {album or ''} {title or ''}".strip().replace(" ", "+")
    url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=1"
    r = requests.get(url)
    if r.status_code != 200:
        return None

    data = r.json()
    if data.get("resultCount", 0) > 0:
        artwork = data["results"][0].get("artworkUrl100")
        if artwork:
            return artwork.replace("100x100", "600x600")
    return None

@app.route('/covers', methods=['GET'])
def get_cover():
    artist = request.args.get("artist")
    album = request.args.get("album")
    title = request.args.get("title")

    if not artist:
        return Response("Missing artist", status=400)

    cover_url = query_itunes_cover(artist, album, title)
    if not cover_url:
        cover_url = query_itunes_cover(artist, None, None)
        if not cover_url:
            return Response("Not found", status=404)


    # 请求封面图
    img_resp = requests.get(cover_url, stream=True)
    if img_resp.status_code != 200:
        return Response("Failed to fetch cover", status=502)

    # 返回图片流
    return Response(
        img_resp.content,
        content_type=img_resp.headers.get("Content-Type", "image/jpeg")
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5678)