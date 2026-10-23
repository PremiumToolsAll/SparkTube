# SparkTube 1.4.1 — অডিও ডাউনলোড টেস্ট বিল্ড

## নতুন কী

Music → Downloads পেজে এখন শুধু সম্পন্ন গান নয়, চলমান, অপেক্ষমাণ, paused ও ব্যর্থ অডিও ডাউনলোডও দেখা যায়। ভিডিওর একই download adapter/engine দিয়ে pause/resume, progress bar, শতাংশ (মোট সাইজ জানা থাকলে), downloaded/total MB, MB/s এবং বাকি সময় দেখায়। অজানা মোট সাইজ বা সময়কে অনুমান করে দেখায় না।

গানের সারিতে বর্গাকার album art, শিরোনাম ও artist আছে। উপরে গানের সংখ্যা ও সবুজ Play all রাখা হয়েছে। গান গোনা ও Play all-এর কিউতে শুধু সম্পূর্ণ এবং ডিস্কে থাকা অডিও যায়; আংশিক ফাইল বাজানো হয় না। সম্পন্ন গানের তিন-ডট মেনুতে Open, Share, Delete আছে; Delete-এ confirmation দেখায়। চলমান/ব্যর্থ সারি long-press করে মুছতে পারেন। পেজ খোলা থাকলে প্রতি সেকেন্ডে অগ্রগতি আপডেট হয়; অন্য পেজে গেলে polling বন্ধ হয়।

## যা অপরিবর্তিত

`com.sparktube.app`, versionName **1.4.1**, versionCode **10** এবং আগের টেস্ট APK-এর signing certificate একই। ভিডিও download engine, Library downloads, player ও compact Audio/Video toggle-এর সোর্স অপরিবর্তিত। DownloadAdapter-এ audioStyle opt-in; পুরোনো default video view আগের পথেই চলে। নতুন dependency, native library বা বড় image asset যোগ হয়নি।

APK: **10,303,832 bytes** (10.30 MB); আগের compact-toggle APK থেকে পরিবর্তন **+2,432 bytes**। এটি debug-signed test build, store release নয়।

## যাচাই ও সীমা

বিল্ড সফল; **46 JVM tests** (অডিও লাইব্রেরির 8 নতুন test-সহ) এবং **15 source/XML structure checks** পাস। APK package/version, signature এবং ZIP alignment যাচাই করা হয়েছে। আগের editable ZIP-এর সঙ্গে মিলিয়ে পুরোনো app source-এ কেবল MusicListActivity ও DownloadAdapter বদলানোর বিষয়টি পরীক্ষা হয়েছে। এটি source-level regression evidence, runtime-এর নিশ্চয়তা নয়।

কোনো Android ফোন বা emulator সংযুক্ত নেই। তাই আসল ফোনে install, screen rendering, download, pause/resume, Play all, playback, share/delete-এর end-to-end পরীক্ষা হয়নি। Android lint offline cache-এ প্রয়োজনীয় `lint-gradle:31.6.1` না থাকায় lintVital ধাপ বাদ দেওয়া হয়েছে; full lint সম্পন্ন হয়নি। আগের deprecation warnings আছে।

আগের সীমাবদ্ধতা একই: pause/resume কেবল চলমান app process-এর মধ্যে; process kill বা restart-এর পর অসম্পূর্ণ download আবার শুরু করতে হবে। Range সমর্থন না করা server pause-এর সময় সংযোগ ছিন্ন করলে download ব্যর্থ হতে পারে। ব্যর্থ item long-press করে মুছে পুনরায় download করতে হবে; নতুন retry/restart button যোগ করা হয়নি।

## সোর্স থেকে বিল্ড

JDK 21 ও Android SDK ব্যবহার করুন; নিজের SDK path দিয়ে `local.properties` তৈরি করুন। `app/build.gradle.kts`-এ version বদলাবেন না।

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এই পরিবেশে offline build command:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
python3 tools/verify-player-correction.py
python3 tools/verify-audio-downloads.py
```

`verification/audio-downloads/`-এ বর্তমান বিল্ড ও টেস্ট ফল রয়েছে। আগের ZIP-নির্ভর byte comparison script-এর জন্য আগের compact-toggle source ZIP parent folder-এ রাখতে হয়; APK build বা JVM tests-এর জন্য তা লাগে না। সোর্স ZIP-এ local SDK path, build cache, APK ও signing key নেই। চূড়ান্ত APK ও source ZIP-এর SHA-256 আলাদা manifest-এ আছে।
