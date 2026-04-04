import os
import re
import shutil

def sanitize_folder_name(name):
    # Remove characters that aren't letters, numbers, spaces, or underscores
    # First, handle some specific cases like "..." or "🤯"
    name = name.replace("...", "")
    # Remove any non-ASCII characters (emojis, etc)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Replace anything that isn't alphanumeric or space with an underscore
    name = re.sub(r'[^a-zA-Z0-9\s]', '_', name)
    # Replace spaces with underscores and remove duplicates
    name = name.replace(" ", "_")
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores and lowercase
    return name.strip("_").lower()

def main():
    html_path = r"c:\Users\hasee\Desktop\yt-video-generation\custom\50 days.html"
    templates_root = r"c:\Users\hasee\Desktop\yt-video-generation\templates"

    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find the shorts array items
    # Looking for: { id: 1, day: 1, s: 1, ... topic: "...", prompt: "..." }
    # We'll extract only day, s, and topic.
    # Note: Using re.DOTALL and a non-greedy match to handle the prompt which can be multi-line.
    # However, for simplicity and robustness in identifying the day, s, and topic:
    pattern = r'day:\s*(\d+),\s*s:\s*(\d+),.*?topic:\s*"(.*?)"'
    matches = re.finditer(pattern, content, re.DOTALL)

    created_count = 0
    for match in matches:
        day_num = match.group(1)
        short_num = match.group(2)
        topic = match.group(3)

        # We stop at Day 43 as requested (though the file has them, the user specified 43)
        if int(day_num) > 43:
            continue

        day_folder = os.path.join(templates_root, f"day{day_num}")
        os.makedirs(day_folder, exist_ok=True)

        sanitized_topic = sanitize_folder_name(topic)
        # Combine short number and topic to keep them ordered and unique
        short_folder_name = f"short{short_num}_{sanitized_topic}"
        short_path = os.path.join(day_folder, short_folder_name)

        if not os.path.exists(short_path):
            os.makedirs(short_path)
            created_count += 1
            print(f"Created: {short_path}")

    print(f"Total folders created: {created_count}")

if __name__ == "__main__":
    main()
