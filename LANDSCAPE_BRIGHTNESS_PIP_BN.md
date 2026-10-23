# SparkTube 1.4.1 — Landscape brightness ও PiP cleanup

## পরিবর্তন

Portrait অবস্থায় বাম পাশের vertical swipe দিয়ে brightness পরিবর্তন হবে না; brightness gesture শুধু landscape-এ কাজ করবে। Landscape থেকে portrait-এ ফিরলে অ্যাপের brightness override বাদ দিয়ে সিস্টেমের brightness ব্যবহার হবে। Volume, double-tap seek, horizontal seek এবং মাঝখানে নিচে swipe করে mini player খোলার আচরণ রাখা হয়েছে।

নতুন ভিডিও/ভিডিও প্লেলিস্ট/অডিও নির্বাচন করলে আগের PiP session-এর floating Activity বন্ধ করা হয়; শুধু player surface সরিয়ে কালো window ফেলে রাখা হয় না। নতুন watch page খুললেও পুরোনো PiP বন্ধ হয়। বন্ধ হতে থাকা Activity-র দেরিতে আসা callback নতুন player surface নিতে বা নতুন PiP-এর state মুছতে পারবে না। একই PiP-এর ভেতর স্বয়ংক্রিয় queue advance-এ PiP বন্ধ করা হয় না।

VersionName 1.4.1, versionCode 10 এবং পূর্বের compact test APK-এর signing certificate অপরিবর্তিত। Controller layout, seek bar, downloads, audio, sleep timer এবং অন্য app source অপরিবর্তিত রাখা হয়েছে; সুনির্দিষ্ট file-scope যাচাই `tools/verify-landscape-brightness-pip.py`-তে আছে।

## বিল্ড ও যাচাই

JDK 21 এবং Android SDK path দিয়ে `local.properties` তৈরি করে:

```sh
./gradlew --offline --no-daemon :app:testCompactTestUnitTest :app:assembleCompactTest \
  -x lintVitalAnalyzeCompactTest -x lintVitalReportCompactTest -x lintVitalCompactTest
python3 tools/verify-landscape-brightness-pip.py
python3 tools/package-landscape-brightness-pip.py
```

প্যাকেজিং স্ক্রিপ্টের baseline APK/source এবং SDK build-tools path একই workspace-এ থাকা প্রয়োজন। APK Gradle-এর existing debug signing config ব্যবহার করে; আগের APK-র সঙ্গে update compatibility রাখতে সেই একই signing keystore প্রয়োজন। ZIP-এ keystore বা secret দেওয়া হয়নি। নতুন কম্পিউটারে প্রথম build-এ dependency download করার জন্য `--offline` বাদ দিতে হতে পারে।

`verification/landscape-brightness-pip/`-তে build log, unit test XML, source regression ফল, certificate/zipalign যাচাই এবং summary আছে। Lint চালানো হয়নি; baseline-এর offline lint dependency অনুপস্থিত থাকায় lint-vital task বাদ দেওয়া হয়েছে।

## ফোনে পরীক্ষা বাকি

Android ফোন বা emulator সংযুক্ত নেই; PiP window বন্ধ হওয়া ও gesture-এর বাস্তব আচরণ এখানে চালিয়ে পরীক্ষা করা হয়নি। ফোনে পরীক্ষা করুন:

1. Portrait-এ বাম দিকে উপরে/নিচে swipe করলে brightness বা brightness feedback বদলায় না।
2. Landscape-এ একই swipe brightness বদলায়; portrait-এ ফিরলে সিস্টেম brightness ফিরে আসে।
3. ভিডিও A থেকে PiP খুলে অ্যাপে ফিরে ভিডিও B চালালে A-এর floating window বন্ধ হয়, B মূল player-এ চলে। দ্রুত B/C নির্বাচন করেও পরীক্ষা করুন।
4. নতুন ভিডিও playlist বা audio চালালেও পুরোনো PiP থাকে না।
5. PiP থেকে পূর্ণ পর্দায় ফিরে আসা, আবার PiP খোলা, PiP বন্ধ করা এবং স্বয়ংক্রিয় next-video পরীক্ষা করুন।
6. Volume/seek, mini player, downloads, notification, audio এবং sleep timer আগের মতো কাজ করে কি না দেখুন।
