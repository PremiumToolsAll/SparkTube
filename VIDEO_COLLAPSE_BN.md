# SparkTube 1.4.1 — ভিডিও প্লেয়ার ছোট করার বাটন

ভিডিও প্লেয়ারের উপরের বাঁ কোণে অডিও প্লেয়ারের মতো নিচমুখী শেভরন বাটন যোগ হয়েছে। একই `finish()` অ্যাকশন ভিডিও পেজ বন্ধ করে আগের স্ক্রিনের মিনি প্লেয়ারে ফেরায়; বাটনটি প্লেব্যাক বন্ধ, কিউ পরিবর্তন, অডিও মোডে রূপান্তর বা PiP চালু করে না। বিদ্যমান slide-down transition ও shared-player lifecycle ব্যবহৃত হয়।

বাটনের টাচ এরিয়া 48×48dp। এটি ভিডিওর ভেতরে থাকে, transport controls লুকালেও দেখা যায়, PiP-এ লুকায় এবং PiP থেকে ফিরলে আবার আসে। Portrait-এ status-bar inset দুবার যোগ করা হয় না; fullscreen-এ cutout/system-bar inset মানা হয়। বাটনটি অডিওর একই down-chevron আইকন ব্যবহার করে; ভিডিওতে contrast-এর জন্য বিদ্যমান dark scrim রাখা হয়েছে।

## যাচাই

`verification/video-collapse/`-এ বিল্ড লগ, source/XML checks, JVM test results, APK metadata, signing ও alignment verification এবং পরিবর্তনের diff আছে। Source/XML checks Android UI execution নয়। Package, versionName 1.4.1, versionCode 10, dependencies ও compact-test build configuration অপরিবর্তিত। আগের notification-audio test APK-এর signing certificate-এর সঙ্গে মিল পরীক্ষা করা হয়েছে। অ্যাপের আগের সোর্সের তুলনায় শুধু PlayerActivity.kt, activity_player.xml ও strings_player_controls.xml বদলেছে; playback service, notification, downloads, audio ও queue implementation অপরিবর্তিত।

কোনো Android ডিভাইস বা emulator সংযুক্ত নেই। Install/update, বাটনে বাস্তব ট্যাপ, seamless playback, orientation, cutout, accessibility ও PiP ফেরার device test করা হয়নি। অফলাইন lint dependency সীমাবদ্ধতার কারণে lintVital tasks বাদ দিয়ে build করা হয়েছে; lint পাস দাবি করা হচ্ছে না।

## ফোনে পরীক্ষা

1. ভিডিও চালিয়ে বাঁ দিকের নিচমুখী বাটন চাপুন: আগের স্ক্রিন ও মিনি প্লেয়ার আসবে; একই ভিডিও ও কিউ চলবে। মিনি প্লেয়ার খুলে অবস্থান মিলিয়ে দেখুন।
2. Pause করে এবং buffering-এর সময় বাটন চাপুন: paused/play intent অপরিবর্তিত থাকবে।
3. Controls auto-hide হওয়ার পরেও বাটন পরীক্ষা করুন। Fullscreen, rotation ও notch/cutout-এ দৃশ্যমানতা ও touch target দেখুন।
4. PiP-এ বাটন থাকবে না; PiP থেকে ফিরে বাটন আসবে। অডিও/ভিডিও switch, notification Play/Pause, seek, queue ও downloads-এর আগের আচরণও দেখুন।

## সোর্স থেকে বিল্ড

JDK 21 ও Android SDK দিয়ে নিজের local.properties তৈরি করে চালান:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
python3 tools/verify-current-update.py
```

এই পরিবেশে `--offline --rerun-tasks -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest` দিয়ে Gradle চালানো হয়েছে। ZIP-এ editable source, Gradle wrapper, vendored libraries, JVM tests ও বর্তমান verification evidence আছে; machine-local SDK path, build caches, APK ও signing key নেই। নিজের সোর্স বিল্ডের signing key আলাদা হতে পারে। ঐতিহাসিক source-scope check-এর জন্য আগের notification-audio source ZIP প্রয়োজন, APK build বা JVM tests-এর জন্য নয়।
