# SparkTube 1.4.2 — নতুন আপডেট

এই আপডেটটি সম্পন্ন হয়েছে এবং এই repo-তে পুশ করা হয়েছে।

## নতুন আপডেটে যা যা পরিবর্তন করা হয়েছে

1. **Home feed দ্রুত** — আগের video cards cache থেকে আগে আসে; নতুন feed পেছনে refresh হয়। প্রথমবারের network load অবশ্য connection-এর ওপর নির্ভর করে।

2. **Video cards** — title-এর পাশে ৩-dot menu-তে Play, Favorite, Share ও Download। Playlist/Library item হলে সরানোর option-ও থাকে। Download চাপলে quality picker ও আগের progress/Downloads flow খোলে।

3. **Player controls** — Previous, বড় Play/Pause, Next; কালো গোল background ছোট, controls-এর সঙ্গে top arrow hide/show হয়। Portrait seek bar video-র নিচে cleanভাবে থাকে; landscape layout আগের মতো।

4. **Seek gestures** — নিচের bar-এর visible track/thumb থেকে drag করলে seek হয়; accidental touch/nearby area থেকে নয়। Intentional horizontal swipe seek ও double-tap ±১০ সেকেন্ড চালু আছে। Brightness/volume swipe শুধু landscape-এ; portrait-এ hardware volume button কাজ করে।

5. **Quality ও audio** — উৎসে যত quality/track পাওয়া যায়, player সেগুলো বেছে চালায়; আলাদা high-quality video+audio stream একই timeline-এ sync থাকে। সব ভিডিওতে 2K/4K বা নির্দিষ্ট quality নিশ্চিত নয় — source, internet ও device-এর ওপর নির্ভর করে।

6. **Video/Audio switch** — একই playback রেখে দ্রুত view বদলায়। Audio player-এ Download-এর পাশে Timer; video page-এ Background play-এর জায়গায় Timer। Countdown শেষে audio/video থামে।

7. **Downloads ও Library** — progress, percentage, মোট MB, speed/ETA যেখানে পাওয়া যায়; pause/resume, share, completed audio file সরাসরি খোলা, album-art library ও item actions আছে।

8. **Notification ও PiP** — Previous/Play-Pause/Next controls আছে; notification tap delay কমানোর code fix হয়েছে। অন্য video চালালে আগের PiP বন্ধ হয়, black floating window আটকে থাকার fix-ও আছে।
