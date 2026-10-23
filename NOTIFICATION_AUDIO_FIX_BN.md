# SparkTube 1.4.1 — নোটিফিকেশন ও অডিও ফাইল খোলা

## এই আপডেটে
নোটিফিকেশন থেকে আসা Play/Pause key-down এখন MediaSession callback-এ সরাসরি session player-কে দেওয়া হয় এবং handled হিসেবে ফেরত যায়। এতে ওই ট্যাপ Media3-এর সাধারণ media-key fallback/command-queue পথে যায় না। Media3 1.3.1-এর bytecode-এ কিছু legacy play/pause key-এর জন্য double-tap timeout এবং দ্বিতীয় ট্যাপকে Next হিসেবে নেওয়ার পথ আছে; নোটিফিকেশনের পৃথক ট্যাপে সেই gesture recognizer প্রযোজ্য নয়। এই পরিবর্তন শুধু notification controller-এর toggle key-এ সীমিত; headset, Bluetooth-এর native transport, Previous/Next ও অন্য commands আগের পথে থাকে। নির্দিষ্ট ফোনে আগের ব্যর্থতার একমাত্র কারণ এটি—এমন runtime প্রমাণ নেই।

বাফারিংয়ে `isPlaying` নয়, `playWhenReady` অনুযায়ী Play/Pause বদলায়। একই ট্যাপ দ্বিতীয়বার default handler-এ যায় না, held-key repeat উপেক্ষা করা হয়। Idle source-এ prepare এবং ended source-এ restart-এর আচরণ রাখা হয়েছে। আগে করা pending-video pause, queue ও player fixes অপরিবর্তিত।

Library → Downloads-এ সম্পন্ন AUDIO আইটেমে ট্যাপ করলে তার বিদ্যমান নির্দিষ্ট `file://` ফাইলের এক-আইটেম music queue চালু হয় এবং Now Playing খোলে। অনলাইনে আবার resolve করা হয় না। Audio Downloads তালিকার বিদ্যমান নির্দিষ্ট ফাইল বেছে চালানোর আচরণ রাখা হয়েছে। ফাইল মুছে গেলে missing-file বার্তা আসে; ভিডিও/AV downloads আগের আচরণেই থাকে।

## যাচাই
বিল্ড সফল। 77 JVM unit tests ও 52 source/XML checks পাস; এগুলো Android runtime test নয়। নতুন transport tests-এ প্রথম ট্যাপ, দ্রুত আলাদা ট্যাপ, buffering, key-up/repeat, headset fallback, command availability এবং idle/ended source আছে। Latest fast-home source-এর সঙ্গে app files তুলনায় কেবল PlaybackService.kt ও LibraryFragment.kt বদলেছে; নতুন handler ও তার unit test যোগ হয়েছে। Version **1.4.1 / code 10**, package ও আগের test APK-এর signing certificate এক। Dependencies, resources ও build configuration অপরিবর্তিত। ZIP alignment এবং signing verification পাস।

কোনো Android ফোন বা emulator সংযুক্ত নেই। Notification tap latency, install/update ও লোকাল অডিও playback-এর device test করা হয়নি; তাৎক্ষণিক audible playback-এর নিশ্চয়তা দেওয়া হচ্ছে না। Network buffering চললে Play চাপার পরে মিডিয়া শুরু হতে সময় লাগতে পারে। Offline lint dependency সীমার কারণে lintVital বাদ ছিল, lint পাস দাবি করা হচ্ছে না।

## ফোনে সংক্ষিপ্ত পরীক্ষা
১. চলমান অডিও ও ভিডিওতে notification Pause একবার চাপুন; তারপর Play একবার। দ্রুত পরপর পৃথক ট্যাপেও কিউ যেন Next না হয়।
২. Buffering ও নতুন ভিডিও resolving অবস্থায় Pause দিয়ে অপেক্ষা করুন; স্ট্রিম তৈরি হলে নিজে থেকে বাজা উচিত নয়। Headset single/double-tap, Previous/Next ও screen-off controls-ও দেখুন।
৩. Downloads এবং Audio Downloads-এ একাধিক সম্পন্ন অডিওর আলাদা আলাদা আইটেম চাপুন; প্রতিবার ট্যাপ করা লোকাল ফাইলই যেন চালু হয়। Offline অবস্থায়ও দেখুন। Missing file, paused/incomplete download ও video/AV download যাচাই করুন।
৪. PiP, home feed, swipe seek ও downloads-এর আগের আচরণ দেখুন।

## সোর্স থেকে বিল্ড
JDK 21 ও Android SDK দিয়ে নিজের local.properties তৈরি করুন।

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এখানে ব্যবহৃত command:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest --rerun-tasks -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
```

ZIP-এ editable source, Gradle wrapper, vendored libraries, unit tests এবং `verification/notification-first-tap/`-এ যাচাইয়ের প্রমাণ আছে। Signing key, APK, machine-local SDK path ও build caches নেই। সোর্স থেকে নিজের build-এর signing key আলাদা হতে পারে। Historical scope comparison-এর জন্য আগের source ZIP লাগে, APK build বা JVM tests-এর জন্য নয়।
