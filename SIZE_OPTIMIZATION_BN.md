# SparkTube 1.4.1 — ছোট টেস্ট APK

এই বিল্ডে অ্যাপের ভার্সন বাড়ানো হয়নি: `versionName 1.4.1`, `versionCode 10`, প্যাকেজ `com.sparktube.app`। আগের টেস্ট APK-এর একই signing certificate ব্যবহার করা হয়েছে।

## সাইজ

| ফাইল | প্রকৃত সাইজ |
| --- | ---: |
| আগের `SparkTube-1.4.1-test-debug.apk` | 14,995,725 bytes — 15.00 MB |
| নতুন `SparkTube-1.4.1-optimized-test.apk` | 10,287,944 bytes — 10.29 MB |
| কমেছে | 4,707,781 bytes — 31.39% |

এখানে MB = 1,000,000 bytes; এগুলো ডাউনলোডযোগ্য APK-এর সাইজ, ফোনে ইনস্টল হওয়ার পরের স্টোরেজ নয়।

## নতুন কন্ট্রোল

লকস্ক্রিন/মিডিয়া নোটিফিকেশনের দৃশ্যমান হার্ট অ্যাকশন সরিয়ে native Previous, Play/Pause ও Next ব্যবহার করা হয়েছে। MediaSession এখন PlayerView-এর মতো একই স্থিতিশীল, অ্যাপ-কিউ-সচেতন প্লেয়ার ব্যবহার করে। Next বর্তমান গানের ১০ সেকেন্ড এগোয় না; পরের queued গান/ভিডিও চালায়। ভিডিওতে অ্যাপের কিউ এবং অডিওতে ExoPlayer-এর প্রকৃত playlist অনুযায়ী কমান্ডের অবস্থা আপডেট হয়। পরের আইটেম না থাকলে Next নিষ্ক্রিয় থাকে। Previous আগের আইটেমে যায়; প্রথম ভিডিওতে বর্তমান ভিডিও শুরু থেকে চালানোর আগের আচরণ থাকে। অ্যাপের ভেতরের Favorite বাটন ও Favorites তালিকা অক্ষুণ্ণ।

ভিডিও কন্ট্রোলে দুই পাশে পৃথক গোলাকার Previous/Next এবং মাঝখানে বড় Play/Pause আছে। দৃশ্যমান ১০-সেকেন্ড rewind/forward বাটন নেই; ফাঁকা ভিডিও অংশে ডাবল-ট্যাপ সিক আগের মতো থাকে।

ভিডিও ও অডিও দুই ভিউয়ের ওপরের Audio/Video সুইচ একই ছোট গাঢ় rounded pill: সক্রিয় মোড সবুজ বৃত্তে, অন্য মোড পাশাপাশি ধূসর আইকনে। আগের switch action, position/queue সংরক্ষণ ও gesture exclusion রাখা হয়েছে। আগের volume/brightness gestures, swipeable Library এবং download pause/resume, progress, speed ও sharing কোড বাদ দেওয়া হয়নি। আগের download সীমাবদ্ধতাগুলো `BUILD_NOTES_BN.md`-এ আছে।

## নিরাপদে কীভাবে ছোট করা হয়েছে

আলাদা `compactTest` build type যোগ করা হয়েছে। সাধারণ `debug` ও `release` build type-এর আচরণ বদলানো হয়নি। `compactTest`-এ non-debug D8/L8 compilation ও Android resource packaging optimization ব্যবহার হয়; অ্যাপের R8 minification/obfuscation এবং resource shrinking বন্ধ। কোনো feature, dependency, ABI বা ভাষার তালিকা কেটে ছোট করা হয়নি। সব 6,070টি আগের Android resource name আছে; নতুন ছোট XML drawable তিনটি যোগ হয়েছে। AAPT2 কিছু resource file path ছোট/একত্র করেছে—এটি resource name বা ফিচার মুছে ফেলা নয়। Toolchain-এর স্বাভাবিক L8 প্রক্রিয়া অব্যবহৃত desugared runtime helper বাদ দিতে এবং D8 synthetic class বদলাতে পারে। মূল third-party library-র সাধারণ ক্লাস বাদ যায়নি; vendored JAR অপরিবর্তিত।

এই APK `android:debuggable=false`, অর্থাৎ debugger attach করার জন্য নয়। কিন্তু `BuildConfig.DEBUG=true` রাখা হয়েছে, যাতে আগের টেস্ট বিল্ডের update-check ও crash-log আচরণ একই থাকে। এটি এখনও debug-key-signed টেস্ট APK; প্রকাশনার production signing key নয়।

## যাচাই

- `assembleCompactTest` ও `testCompactTestUnitTest` সফল। ১৫টি JVM টেস্ট পাস: আগের gesture গণনার ৭টি এবং queue boundary-এর নতুন ৮টি; failures/errors/skipped শূন্য।
- ১৩৩টি XML parse হয়েছে। APK signature এবং zip alignment যাচাই সফল। APK-এর ভেতরের version, package, permissions ও manifest component list যাচাই হয়েছে; permissions/components অপরিবর্তিত।
- Certificate SHA-256: `40f61a2530f18ff692b47b627fa45eae3fd66ff95c076a4b461086128a5db766` — আগের টেস্ট APK-এর সঙ্গে একই।
- APK SHA-256: `9c4d5bec11dc003237859a7ee10cb1378fd9bb8bb2f778e66a15133d2b7671f1`।

কোনো Android ফোন/emulator যুক্ত ছিল না। তাই ফোনে install/update, বাস্তব লকস্ক্রিনের button rendering, native MediaController interaction, touch dispatch, playback ও download-এর end-to-end পরীক্ষা হয়নি। Queue-policy টেস্ট ও static/compile checks-কে সেই পরীক্ষার বিকল্প বলা হচ্ছে না। `lint-gradle:31.6.1` অফলাইন ক্যাশে অনুপস্থিত থাকায় lint সম্পন্ন হয়নি; সফল অফলাইন build-এ তিনটি lintVital task স্পষ্টভাবে বাদ দেওয়া হয়েছে। বিদ্যমান Kotlin/D8 metadata warning-ও রয়েছে; toolchain বদলানো হয়নি।

## আবার বিল্ড

JDK 21, Android SDK 35 ও build-tools 34.0.0 ব্যবহার করা হয়েছে। নিজের SDK path দিয়ে `local.properties` তৈরি করুন অথবা `ANDROID_HOME` সেট করুন। স্বাভাবিক অনলাইন বিল্ড:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এই পরিবেশে ব্যবহৃত অফলাইন কমান্ড, lint-এর উল্লিখিত সীমাবদ্ধতাসহ:

```sh
./gradlew --offline --no-daemon \
  :app:assembleCompactTest :app:testCompactTestUnitTest \
  -x :app:lintVitalAnalyzeCompactTest \
  -x :app:lintVitalReportCompactTest \
  -x :app:lintVitalCompactTest
```

আউটপুট: `app/build/outputs/apk/compactTest/app-compactTest.apk`। বিতরণের জন্য এর নাম `SparkTube-1.4.1-optimized-test.apk` করা হয়েছে। একই কম্পিউটারের বিদ্যমান debug key পুনঃব্যবহার করা হয়েছে; ZIP-এ signing key নেই। অন্য কম্পিউটারে আলাদা debug key থাকলে সই একই হবে না। আগের অ্যাপের ওপর update করতে signature মিলতে হবে; এই বিতরণকৃত APK-এর ক্ষেত্রে তা যাচাই হয়েছে।

`tools/apk-size-audit.py` দিয়ে দুটি APK-এর ZIP payload এবং DEX class তুলনা করা যায়। `verification/size-optimization/`-এ সফল বিল্ডের `build-controls-final.log`, দুই test suite-এর XML, APK comparison, source hash baseline, resource dump, manifest এবং signature verification আছে। আগের কয়েকটি অসম্পূর্ণ build attempt-এর log-ও রাখা হয়েছে; চূড়ান্ত ফল `verification-summary.json`-এ। Editable source ZIP-এ project source, Gradle wrapper, libraries, tests ও verification আছে; local SDK path, build/cache directory ও signing key নেই। APK ও ZIP-এর SHA-256 আলাদা manifest-এ দেওয়া হয়েছে।
