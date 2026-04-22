import feedparser

USERNAME = "TheWallHouse"
FEED_URL = f"https://letterboxd.com/{USERNAME}/rss/"

feed = feedparser.parse(FEED_URL)

films = []
for entry in feed.entries[:10]:
    title = entry.title
    link = entry.link
    films.append(f"- [{title}]({link})")

block = "\n".join(films)

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

new_content = content.split("<!-- LETTERBOXD:START -->")[0]
new_content += "<!-- LETTERBOXD:START -->\n"
new_content += block + "\n"
new_content += "<!-- LETTERBOXD:END -->"
new_content += content.split("<!-- LETTERBOXD:END -->")[1]

with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)

print("README actualizado correctamente")
