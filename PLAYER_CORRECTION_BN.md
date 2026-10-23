# SparkTube 1.4.1 — প্লেয়ার সংশোধন

এই সংশোধনটি আগের `SparkTube-1.4.1-optimized-test.apk`-এর ওপর ভিত্তি করে। সংস্করণ অপরিবর্তিত: `versionName 1.4.1`, `versionCode 10`। নতুন আউটপুটের নাম `SparkTube-1.4.1-player-fixed-test.apk`। এটি debug-key-signed টেস্ট বিল্ড, production release নয়। আগের নোটের চেয়ে বর্তমান প্লেয়ারের আচরণের জন্য এই নোট প্রযোজ্য।

## কী বদলেছে

ভিডিও প্লেয়ারে বামে Previous, মাঝখানে বড় Play/Pause এবং ডানে Next। Media3 1.3.1-এর standard controller ছোট উচ্চতার প্লেয়ারকে minimal mode-এ নিয়ে `exo_prev` ও `exo_next` লুকায়; স্ক্রিনশটে শুধু মাঝের Pause থাকার সঙ্গে এটি মিলে যায়। এবার নিজস্ব controller layout ও queue-button ID ব্যবহার করা হয়েছে, যাতে সেই নিয়ম বাটন দুটো লুকাতে না পারে। Native Play/Pause, seekbar, সময় ও settings রাখা হয়েছে। কিউয়ের অবস্থা বদলালে বাটনের enabled state আপডেট হয়। Next সরাসরি পরের queued item চালায়—১০ সেকেন্ড seek নয়। পরের item না থাকলে Next দৃশ্যমান কিন্তু ম্লান ও নিষ্ক্রিয় থাকে। প্রথম item-এ Previous বর্তমান item শুরু থেকে চালানোর আগের আচরণ রাখে।

দুই ভিউতেই Audio/Video switch এখন দৃশ্যত 80×32dp গাঢ় pill, 19dp আইকন এবং ছোট সবুজ active segment। ট্যাপের জায়গা 92×48dp রাখা হয়েছে। বর্তমান মোড ও বদলানোর দিক accessibility description-এ উল্লেখ আছে।

কালো ভিডিওর সম্ভাব্য rendering-path সমস্যার জন্য watch-page `TextureView` বদলে native `SurfaceView` করা হয়েছে। একই ExoPlayer-এর mini-player ও watch-player সংযোগে একটিমাত্র active view রাখা হয়েছে; Media3-এর `PlayerView.switchTargetView` দিয়ে নতুন output আগে যুক্ত করে পুরোনো view ছাড়ানো হয়। একই view পুনরায় attach ও পুরোনো Activity callback-এ অপ্রয়োজনীয় output পরিবর্তন এড়ানো হয়েছে।

**কালো ভিডিওর একমাত্র মূল কারণ নিশ্চিত হয়নি।** ডিভাইসের decoder/stream/rendering লগ বা সরাসরি playback না দেখে screenshot থেকে সেই নিশ্চয়তা দেওয়া যায় না। Surface ও handoff সংশোধন বাস্তব ফোনে যাচাই প্রয়োজন; কেবল build সফল হওয়া ভিডিও দৃশ্যমান হওয়ার প্রমাণ নয়।

## ডাউনলোডের নতুন হিসাব ও মেনু

সক্রিয় download row-তে downloaded/total MB, বর্তমান MB/s এবং আনুমানিক বাকি সময় দেখানো হয়। একক decimal megabyte: 1 MB = 1,000,000 bytes; MB/s-কে Mbps হিসেবে ভুল লেবেল দেওয়া হয় না। UI refresh-এর সংখ্যা দিয়ে speed sample বদলায় না; transferred-byte updates এবং monotonic সময় থেকে rate গণনা হয়। Pause/resume-এ sample reset হয়; stall হলে পুরোনো speed শূন্য হয়। ETA বাকি bytes/current rate থেকে ঊর্ধ্বমুখী পূর্ণ সেকেন্ডে হিসাব হয় এবং `~` দিয়ে আনুমানিক বোঝানো হয়—ভবিষ্যতের নেটওয়ার্ক গতি নিশ্চিত করা যায় না।

Audio+Video জোড়ার উভয় অংশের bytes/total একসঙ্গে ধরা হয়। কোনো অংশের total অজানা থাকলে সম্পূর্ণ size ও ETA অজানা দেখানো হয়, বানানো percentage/সময় নয়। HTTP full-response Content-Length পাওয়া গেলে ব্যবহার হয়; এক-byte range probe-এর Content-Length-কে মোট size ধরা হয় না। Completed row-তে আসল ফাইলের মোট size এবং ডানদিকে 3-dot মেনু থাকে: Play, Share, Delete। Delete আগের confirmation ব্যবহার করে; AV sharing আগের মতো দুইটি আলাদা track file দেয়, নতুন muxing ফিচার যোগ হয়নি।

## কী অক্ষুণ্ণ রাখা হয়েছে

Double-tap ±10-second seek এবং volume/brightness gesture কোড আছে। Notification/lock-screen queue-aware Previous/Play-Pause/Next service, download sharing এবং swipeable Library-এর কোড আগের source ZIP-এর সঙ্গে অপরিবর্তিত থাকার পরীক্ষা করা হয়েছে। Download engine ও download-row UI কেবল নতুন অনুমোদিত metrics/menu কাজের জন্য সংশোধিত। বিদ্যমান vendored library JAR অপরিবর্তিত। অ্যাপের R8 minification ও resource shrinking বন্ধ; কোনো feature/dependency/ABI/ভাষা বাদ দেওয়া হয়নি। বাস্তবে সব feature end-to-end চালিয়ে পরীক্ষা হয়েছে—এমন দাবি করা হচ্ছে না।

## পরীক্ষা ও সীমাবদ্ধতা

বর্তমান APK 10.30 MB (10,300,268 bytes)। 31টি JVM test এবং ৯টি structural test পাস করেছে; failure/error/skipped শূন্য। APK signature ও zip alignment যাচাই সফল; manifest ও signing certificate আগের optimized APK-এর সঙ্গে একই।

`verification/player-correction/`-এ বর্তমান build log, structural test output, JVM test XML, manifest, signature ও artifact summary থাকবে। কাঠামোগত পরীক্ষা render/touch/device test নয়। পুরোনো `verification/size-optimization/` আগের বিল্ডের ঐতিহাসিক প্রমাণ, বর্তমান ফল নয়।

কোনো physical Android device সংযুক্ত নেই; `adb devices`-এ কোনো device নেই। Android emulator-ও এখানে চালু নেই। তাই ফোনে install/update, ছবিসহ playback, fullscreen/PiP, gesture touch, lock-screen rendering ও download end-to-end পরীক্ষা করা যায়নি।

অফলাইন cache-এ `lint-gradle:31.6.1` অনুপস্থিত থাকায় আগের মতো lintVital task বাদ দিয়ে বিল্ড করা হয়েছে; lint সফল হয়েছে বলা হচ্ছে না। পুরোনো Kotlin/D8 metadata ও deprecation warning থাকতে পারে।

## আবার বিল্ড

JDK 21 এবং Android SDK 35 ব্যবহার করুন। নিজের SDK path দিয়ে `local.properties` তৈরি করুন অথবা `ANDROID_HOME` সেট করুন। স্বাভাবিকভাবে:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
python3 tools/verify-player-correction.py
```

এই পরিবেশে ব্যবহৃত অফলাইন কমান্ড:

```sh
./gradlew --offline --no-daemon \
  :app:assembleCompactTest :app:testCompactTestUnitTest \
  -x :app:lintVitalAnalyzeCompactTest \
  -x :app:lintVitalReportCompactTest \
  -x :app:lintVitalCompactTest
```

APK: `app/build/outputs/apk/compactTest/app-compactTest.apk`। Editable source ZIP-এ build/cache, local SDK path বা signing key নেই। ভিন্ন কম্পিউটারে debug key আলাদা হলে তৈরি APK-এর signature-ও আলাদা হবে। বিতরণের APK ও source ZIP-এর checksum আলাদা SHA-256 manifest-এ দেওয়া হয়েছে।
