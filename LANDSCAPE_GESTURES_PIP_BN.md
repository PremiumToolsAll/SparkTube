# SparkTube 1.4.1 — Landscape-only brightness ও volume gesture

## কী বদলেছে

Portrait-এ বাম পাশের brightness এবং ডান পাশের sound-volume vertical swipe—দুটিই বন্ধ। Landscape-এ দুটি gesture আগের মতো থাকে। Hardware volume button বা system volume control বন্ধ করা হয়নি। Landscape থেকে portrait-এ ফিরলে আগের মতো system brightness ফিরে আসে।

Horizontal seek, double-tap seek এবং মাঝখানে নিচে swipe করে minimize করার কোড অপরিবর্তিত। সর্বশেষ PiP cleanup fix, audio, downloads, sleep timer, notification, controls এবং অন্য সব app source অপরিবর্তিত। আগের `landscape-brightness-pip` সোর্সের তুলনায় app source-এ শুধু `PlayerActivity.kt`-এর brightness-only guard দুই side gesture-এর আগের যৌথ জায়গায় সরানো হয়েছে।

VersionName **1.4.1**, versionCode **10**, compactTest configuration এবং আগের test APK-এর signing certificate বজায় রাখা হয়েছে। `LANDSCAPE_BRIGHTNESS_PIP_BN.md` আগের পরিবর্তনের ঐতিহাসিক নোট; portrait volume সম্পর্কে এই নতুন নোট প্রযোজ্য।

## পুনরায় বিল্ড

JDK 21 এবং Android SDK ব্যবহার করুন। নিজের SDK path দিয়ে `local.properties` বানিয়ে চালান:

```sh
./gradlew --offline --no-daemon :app:testCompactTestUnitTest :app:assembleCompactTest \
  -x lintVitalAnalyzeCompactTest -x lintVitalReportCompactTest -x lintVitalCompactTest
```

নতুন কম্পিউটারে dependency download করতে `--offline` বাদ দিতে হতে পারে। APK পাওয়া যাবে `app/build/outputs/apk/compactTest/app-compactTest.apk`-এ। আগের APK-এর update-compatible signing পেতে একই বিদ্যমান debug keystore প্রয়োজন; ZIP-এ keystore বা secret নেই।

সোর্স রিগ্রেশন ও প্যাকেজিং পুনরায় চালাতে:

```sh
mkdir -p verification/landscape-gestures-pip
python3 tools/verify-landscape-gestures-pip.py > verification/landscape-gestures-pip/source-checks.log 2>&1
python3 tools/package-landscape-gestures-pip.py
```

এই workspace-কেন্দ্রিক যাচাই স্ক্রিপ্টে আগের source ZIP/APK, পুরোনো compact-controls source ZIP এবং Android SDK build-tools path লাগে। প্যাকেজিং স্ক্রিপ্টে বর্তমান সফল build log থাকতে হবে। অন্য পরিবেশে সংশ্লিষ্ট path সামঞ্জস্য করুন।

`verification/landscape-gestures-pip/`-এ build log, unit-test XML, source-check log, APK version/signature/zipalign evidence এবং summary রয়েছে। পুরোনো offline lint dependency সীমাবদ্ধতার কারণে lint-vital বাদ দেওয়া হয়েছে; lint pass দাবি করা হচ্ছে না।

## ফোনে পরীক্ষা বাকি

কোনো Android device বা emulator সংযুক্ত নেই। তাই APK build, JVM unit test ও static checks করা হলেও বাস্তব gesture/PiP runtime পরীক্ষা হয়নি। ফোনে নিশ্চিত করুন:

1. Portrait-এ বাম ও ডান side swipe করলে brightness/volume বা সংশ্লিষ্ট feedback বদলায় না। Hardware volume button কাজ করে।
2. Landscape-এ বাম brightness এবং ডান volume swipe কাজ করে; portrait-এ ফিরলে system brightness ফিরে আসে।
3. দুই orientation-এ horizontal seek, double-tap seek, center swipe-down ও player controls কাজ করে।
4. ভিডিও A-এর PiP খোলা রেখে নতুন ভিডিও B, playlist বা audio চালালে পুরোনো floating window বন্ধ হয়। দ্রুত একাধিক ভিডিও নির্বাচন করেও পরীক্ষা করুন।
5. PiP expand/close/reopen ও automatic next-video আগের মতো চলে। Downloads, audio, notification ও sleep timer-ও পরীক্ষা করুন।
