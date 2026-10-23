# SparkTube 1.4.1 — Sleep timer ও দ্রুত অডিও সুইচ

অডিও প্লেয়ারে সবুজ outlined Timer বাটন আছে। ভিডিও পেজের horizontal action row-তে Background play বাটনের জায়গায় Timer রাখা হয়েছে। দুই বাটন একই Sleep timer selector খোলে: Off, 10, 15, 20, 30, 45 minutes, 1 hour এবং End of video। নির্বাচিত অপশনে চেক চিহ্ন থাকে। ছোট স্ক্রিনে তালিকা স্ক্রল করা যায়।

টাইমার সেট করলে বাটনে মিনিট:সেকেন্ড কাউন্টডাউন দেখায়। ভিডিওতে প্রতি সেকেন্ডে এবং অডিওতে অর্ধ সেকেন্ড অন্তর লেবেল refresh হয়। একটাই app-wide monotonic deadline ব্যবহৃত হয়: pause, seek, playback speed, পেজ বদল বা অডিও/ভিডিও সুইচে নির্ধারিত সময় নতুন করে শুরু হয় না। Off বাতিল করে, অন্য সময় বাছলে নতুন countdown শুরু হয়।

সময় শেষ হলে shared player বন্ধ হয়; queue, pending stream resolution ও recovery jobs বাতিল হয় যাতে পরে নিজে থেকে আবার চালু না হয়। খোলা player page বন্ধ হয়। এটি অ্যাপের process জোর করে kill করে না এবং downloads বন্ধ করে না। End of video বর্তমান media শেষ হলে থামায়, next item autoplay করার আগে; নিজে অন্য media বাছলে শুধু End of video সেটিং বাতিল হয়। নির্দিষ্ট মিনিটের countdown queue বদলালেও থাকে।

উপরের ভিডিও→অডিও সুইচে একই ExoPlayer ও source রাখা হয়। সোর্স reload/prepare/seek করা হয় না, তাই পেজ বদলের জন্য নেটওয়ার্কের অপেক্ষা নেই। অডিও পেজ থেকে একই ভিডিওতে ফিরলেও retained source পুনরায় ব্যবহার হয়। প্রকৃত music-only stream থেকে প্রথমবার ভিডিওতে যাওয়া বা পরে নতুন audio-only source লোড হলে আগের মতো resolving প্রয়োজন হতে পারে।

## যাচাই

`verification/sleep-timer/`-এ Gradle build log, JVM tests, source/XML regression checks, APK metadata, signing certificate comparison, zip alignment ও verification summary আছে। Package `com.sparktube.app`, versionName `1.4.1`, versionCode `10`, dependencies, manifest ও compact signing configuration অপরিবর্তিত। আগের video-collapse test APK-এর certificate-এর সঙ্গে মিল পরীক্ষা করা হয়।

কোনো Android ফোন বা emulator সংযুক্ত নেই। ইনস্টল, বাস্তব ট্যাপ/কাউন্টডাউন, 10–60 মিনিটের background run, screen-off/Doze/OEM battery restriction, PiP, transition speed ও নিরবচ্ছিন্ন playback ডিভাইসে পরীক্ষা করা হয়নি। Listener-based wake alarm ও shared service ticker আছে; Android/OEM scheduling-এর বিলম্বমুক্ত কার্যকারিতা বাস্তব ফোনে যাচাই বাকি। Offline lint dependencies সীমাবদ্ধতার কারণে lintVital tasks বাদ দেওয়া হয়েছে; lint pass দাবি করা হচ্ছে না।

## ফোনে সংক্ষিপ্ত পরীক্ষা

1. অডিওতে 10 minutes দিন: 10:00 থেকে কমবে। ভিডিওতে switch করে একই বাকি সময় দেখুন।
2. ভিডিওর Timer থেকে সময় বদলান, Off দিন ও শিট পুনরায় খুলে selected চিহ্ন দেখুন।
3. pause/seek/speed পরিবর্তন ও স্ক্রিন বন্ধ রেখেও নির্বাচিত wall-clock সময় শেষে playback বন্ধ হওয়া দেখুন।
4. দুই গান/ভিডিওর queue-তে End of video দিন: পরেরটি যেন নিজে থেকে না চলে।
5. ভিডিও চলার সময় উপরের audio switch চাপুন: পেজ দ্রুত খুলবে, position/প্লেব্যাক অবস্থা থাকবে; ফিরে আসাও দেখুন।
6. Notification controls, downloads, PiP, collapse, quality selection ও queue navigation-এর পূর্বের আচরণ পরীক্ষা করুন।

## সোর্স থেকে বিল্ড

JDK 21 ও Android SDK দিয়ে নিজের `local.properties` তৈরি করুন:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
python3 tools/verify-current-update.py
```

এই পরিবেশে Gradle `--offline -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest` দিয়ে চালানো হয়েছে। ZIP-এ editable source, wrapper, vendored libraries ও tests রয়েছে; SDK path, build caches, APK ও signing key নেই। নিজের signing key দিয়ে rebuild করলে certificate আলাদা হবে। ঐতিহাসিক source-scope audit-এ আগের source ZIP লাগে; APK/JVM build-এ লাগে না।
