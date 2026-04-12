# Reel Generator Commands

Here are all the available commands to generate and publish your reels. 

## Batch / Script Commands

### 1. Single Reel Generation
Generate a reel for a specific sign. Prompts for input if the sign is not provided.
```cmd
generate_single.bat
generate_single.bat Aries
```

### 2. All Signs Generation
Generate reels for all 12 signs at once. Defaults to `horoscope` category. Generates in parallel.
```cmd
generate_all.bat
generate_all.bat relationships
generate_all.bat career
generate_all.bat current_events
generate_all.bat emotional_healing
generate_all.bat manifestation
generate_all.bat all
```

### 3. Viral Reels Generation
Generate viral reels for a specific sign and category.
```cmd
generate_viral.bat
generate_viral.bat Leo relationships
generate_viral.bat Scorpio manifestation
generate_viral.bat Aries emotional_healing
generate_viral.bat all career
generate_viral.bat all all
```

### 4. Publish Queue Workflow
Generate reels for all signs and create same-name JSON queue files for auto-posting.
```cmd
generate_publish_queue.bat
generate_publish_queue.bat horoscope
generate_publish_queue.bat relationships
```

---

## Direct Python Usage

### Generate Reels (`Generate.py`)
```cmd
python Generate.py --sign Pisces --category current_events
python Generate.py --sign all --category all --parallel
python Generate.py --sign Leo --soundtrack "soundtrack/song.mp3"
python Generate.py --sign all --category horoscope --parallel
```

### Generate Publish Queue (`generate_publish_queue.py`)
```cmd
python generate_publish_queue.py --sign all --category horoscope --parallel
python generate_publish_queue.py --sign Aries --category relationships
```

### Post Scheduled Reels (`post_scheduled_reels.py`)
Post due reels from the publish queue (typically used in automated environments like GitHub Actions).
```cmd
python post_scheduled_reels.py
python post_scheduled_reels.py --queue-dir publish_queue
```
