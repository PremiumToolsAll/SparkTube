# পোর্ট্রেট seek: intentional gesture রাখুন, accidental touch আটকান

পোর্ট্রেটে ভিডিওর ওপর intentional horizontal swipe seek এবং বাম/ডান অর্ধে double-tap করে −১০/+১০ সেকেন্ড seek ফিরিয়ে দেওয়া হয়েছে। Single tap শুধু controls দেখায়/লুকায়। Surface swipe আগের মতো ১৪dp movement ও horizontal dominance শনাক্ত হওয়ার পরে preview দেখায়; আঙুল ছাড়লে seek হয়। শুরু ও শেষের orientation আলাদা হলে surface seek commit হয় না।

## নিচের seek bar

`DeliberateSeekTimeBar` native Media3 time bar-এর subclass। শুধু portrait touch-এ প্রথম DOWN আটকে রাখে। অন্তত ১৪dp (বা system touch slop, যেটি বেশি) এবং স্পষ্ট horizontal movement হলে buffered DOWN ও MOVE native time bar-এ পাঠায়। তাই tap, ছোট jitter, vertical বা ambiguous diagonal drag thumb সরায় না বা playback seek করে না। Meaningful non-horizontal drag একবার reject হলে একই touch sequence পরে horizontal হয়ে scrub করতে পারে না। Multi-touch, CANCEL, rotation ও detach-এ pending/active portrait scrub বাতিল হয়। Native scrub listeners, preview ও release-to-seek behavior-ই ব্যবহার করা হয়; আলাদা playback seek loop নয়। Keyboard ও accessibility actions native Media3-তেই থাকে।

Touch ownership শুরুতে নির্ধারিত হয়। ভিডিওর surface থেকে bar-এ আঙুল সরানো native timebar drag শুরু করে না; সেটি intentional surface gesture হিসেবেই থাকে। আসল buttons তাদের আগের touch flow পায়। Landscape-এ timebar সরাসরি native `onTouchEvent` ব্যবহার করে; একই native style, dimensions এবং surface seek/brightness/volume আচরণ রাখা হয়েছে।

## ভিডিও কার্ডের Download

ভিডিও কার্ডের three-dot menu-তে Download যোগ করা হয়েছে। বিদ্যমান download flow, progress এবং library UI ব্যবহার করা হয়; অন্য menu actions রাখা হয়েছে।

## Build ও যাচাই

versionName **1.4.1**, versionCode **10**। Build/signing configuration এবং dependency অপরিবর্তিত। Source ZIP-এ keystore/password নেই; অন্য পরিবেশে একই signing certificate পেতে আগের signing key প্রয়োজন। SDK path নিজের `local.properties`-এ দিন।

এই পরিবেশে:

```bash
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
python3 tools/package-gestures-download.py
```

Build/test/signature/version/archive verification-এর ফল `verification/gestures-download/verification-summary.json`-এ থাকে। Local JVM tests pure gesture math/gate/policy পরীক্ষা করে; native Android touch integration পরীক্ষা করে না। Android ফোন বা emulator সংযুক্ত নেই। Runtime touch, visual overlap, download network flow, rotation ও landscape regression বাস্তব ডিভাইসে পরীক্ষা করা হয়নি। Lint এই build-এ বাদ দেওয়া হয়েছে।

ফোনে পরীক্ষা: portrait surface swipe, দুই পাশে double-tap, single tap; bar tap/jitter/vertical/diagonal drag বনাম deliberate horizontal drag; surface থেকে bar-এ drag; CANCEL/multi-touch/rotation; landscape controls/seek/volume/brightness; এবং card menu Download থেকে progress ও library flow।
