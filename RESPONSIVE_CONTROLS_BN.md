# SparkTube — দ্রুত হোম ফিড, মিডিয়া কন্ট্রোল ও সোয়াইপ সিক

## নতুন আচরণ
অ্যাপ খোলার সময় আগের সফল হোম ফিডের সীমিত, দেশভিত্তিক cache থেকে ভিডিও কার্ড আগে দেখানো হয়; নতুন ফিড পেছনে refresh হয়। Cache-এ শুধু ভিডিওর তালিকার তথ্য ও thumbnail URL থাকে, playable stream URL নয়। Fresh install বা cache না থাকলে তিনটি feed source একসঙ্গে লোড হয় এবং প্রথম সফল source-এর ফল বাকি source ও পূর্ণ recommendation ranking শেষ হওয়ার আগেই দেখানো হয়। Refresh ব্যর্থ হলে ব্যবহারযোগ্য পুরোনো তালিকা মুছে ফেলা হয় না। প্রথমবারের network request বা uncached thumbnail-কে offline/তাৎক্ষণিক বলে দাবি করা হচ্ছে না।

নোটিফিকেশনের Previous / Play-Pause / Next রাখা হয়েছে। বাফারিং চলাকালে play/pause এখন `isPlaying` নয়, ব্যবহারকারীর `playWhenReady` intent ধরে কাজ করে। নতুন ভিডিওতে Next/Previous চাপলে আগের ভিডিওর অডিও থামে এবং session-এ নতুন শিরোনাম ও সত্যিকারের loading/buffering অবস্থা স্ট্রিম URL পাওয়ার আগেই পাঠানো হয়। লোডিংয়ের মধ্যে Pause দিলে নতুন source তৈরি হওয়ার পর সেটি নিজে থেকে আর বাজবে না। দ্রুত পরপর Next/Previous চাপলে বাতিল পুরোনো কাজ নতুন নির্বাচনের state মুছতে পারে না। প্রকৃত ভিডিও/অডিও শুরু হতে নেটওয়ার্ক সময় লাগতে পারে; READY বা playing-এর মিথ্যা অবস্থা দেখানো হয় না।

ভিডিও পেজের সক্রিয় “Downloading · …%” বাটনে চাপলে Library → Downloads খুলবে এবং বিদ্যমান live progress refresh চলবে। ডাউনলোড না চললে আগের quality/audio-video download sheet এবং সম্পূর্ণ ডাউনলোডের delete confirmation থাকে।

ডানে অনুভূমিক সোয়াইপে ধীরে সামনে, বামে পিছনে seek preview হয়; আঙুল ছাড়লে সেই অবস্থানে যাওয়া হয়। ছোট নড়াচড়া ও দিক নির্বাচন আলাদা করা হয়েছে, যাতে ওপর-নিচের brightness/volume gesture-এর সঙ্গে না মেশে। আগের double-tap ±১০ সেকেন্ডও থাকে। Cancel হলে seek হয় না।

## যা সংরক্ষিত
সংস্করণ **1.4.1**, versionCode **10**, package `com.sparktube.app` এবং আগের test APK-এর signing certificate অপরিবর্তিত। Compact test build; production release নয়। PiP lifecycle/rendering fix, audio/video downloads, কিউ transport, বিদ্যমান controls ও resources রাখা হয়েছে। নতুন dependency বা বড় asset নেই। APK **10,316,436 bytes** (প্রায় **10.32 MB**); আগের PiP test APK থেকে **+12,704 bytes**।

## যাচাই ও সীমা
Build সফল; **66 JVM unit tests** এবং **48 source/XML regression checks** পাস। Source checks Android runtime test নয়। সর্বশেষ PiP source ZIP-এর সঙ্গে app files তুলনা করে শুধু অনুমোদিত playback, navigation ও gesture files বদলানোর যাচাই আছে। পুরোনো আপডেটগুলোর historical “অন্য কোনো ফাইল বদলাবে না” assertion বর্তমান scope-এর জন্য বাদ দিয়ে নতুন latest-source scope audit চালানো হয়েছে; feature checks রাখা হয়েছে। Signature/certificate match, version/package এবং ZIP alignment যাচাই হয়েছে।

কোনো physical Android device বা emulator সংযুক্ত নেই; ফোনে install, notification latency, swipe feel, PiP rendering বা download navigation-এর end-to-end পরীক্ষা করা হয়নি। তাই ফোনে নিশ্চিত তাৎক্ষণিক প্রতিক্রিয়া দাবি করা হচ্ছে না। Offline lint dependency না থাকায় lintVital tasks বাদ; lint পাস দাবি নেই। Logs, diffs, test XML ও summary `verification/notification-response/`-এ আছে।

## ফোনে সংক্ষিপ্ত পরীক্ষা
০. একবার Home লোড করে অ্যাপ সম্পূর্ণ বন্ধ করে ফের খুলুন; আগের কার্ড আগে দেখা এবং পেছনে refresh পরীক্ষা করুন। Slow/offline network, fresh install, country change ও pull-to-refresh-ও দেখুন; অন্য দেশের cache যেন না আসে।
১. চলমান ও buffering ভিডিও/গানে notification Play/Pause দ্রুত চাপুন; পজ দিলে নেটওয়ার্ক ফেরার পর নিজে থেকে বাজে কি না দেখুন।
২. ভিডিও কিউতে Next/Previous দ্রুত চাপুন; নতুন শিরোনাম/loading, সঠিক শেষ নির্বাচন এবং আগের অডিও বন্ধ হওয়া দেখুন। কিউয়ের শুরু/শেষও পরীক্ষা করুন।
৩. “Downloading · …%” চাপুন; Downloads-এ বর্তমান অগ্রগতি এবং pause/resume/cancel দেখুন। Idle download button-এর sheet ও completed download delete অপরিবর্তিত আছে কি না দেখুন।
৪. ডানে/বামে ধীরে সোয়াইপ, seek preview/release, শুরু/শেষ সীমা, double-tap ±১০ সেকেন্ড, brightness/volume এবং portrait/landscape পরীক্ষা করুন।
৫. Home/PiP, full-player-এ ফেরা এবং audio/video download পরীক্ষা করুন।

## সোর্স থেকে বিল্ড
JDK 21 ও Android SDK দিয়ে নিজের `local.properties` বানিয়ে চালান:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এখানে ব্যবহৃত offline command:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
```

ZIP-এ editable source, Gradle wrapper, vendored libraries, unit tests ও verification আছে; build output/cache, local SDK path, APK ও signing key নেই। APK ও ZIP-এর SHA-256 আলাদা manifest-এ আছে। ঐতিহাসিক diff verifier চালাতে আগের source ZIP parent folder-এ লাগে; APK build বা JVM tests-এর জন্য লাগে না।
