# SparkTube 1.4.1 — টেস্ট বিল্ড

> এই ZIP-এর সর্বশেষ ছোট APK, লকস্ক্রিন Next ও Audio/Video পিলের পরিবর্তন এবং বিল্ড নির্দেশনা `SIZE_OPTIMIZATION_BN.md`-এ আছে। নিচের নোটগুলো আগের বড় debug টেস্ট বিল্ডের ইতিহাস; `assembleDebug` এখনও সেই ডিবাগ ধরনের বিল্ড তৈরি করে।

মূল Kotlin Android প্রজেক্টেই পরিবর্তন করা হয়েছে। প্যাকেজ `com.sparktube.app`, `versionName = 1.4.1` ও `versionCode = 10` অপরিবর্তিত। এটি debug-signed টেস্ট APK, প্রকাশনার release APK নয়। আগের original-debug APK-এর সঙ্গে signing certificate একই।

## পরিবর্তন

- সার্চ রাখা হয়েছে; পাশের crash-test/bug বাটন সরানো হয়েছে।
- Library-র তালিকায় ডানে/বামে সোয়াইপ করলে পাশের ক্যাটাগরি নির্বাচিত হয়। Downloads-এ অডিও ও ভিডিও উভয় ট্রান্সফার দেখা যায়।
- ডাউনলোডে pause/resume, শতাংশ, প্রতি সেকেন্ডে আপডেট হওয়া Mbps এবং সম্পন্ন ফাইল অন্য অ্যাপে শেয়ার করার কন্ট্রোল আছে। রেঞ্জ ডাউনলোডে পুনঃচেষ্টার সময় লেখা বাইটের পর থেকে ডাউনলোড হয়।
- ভিডিওর প্রকাশ্য ১০-সেকেন্ড rewind/forward বাটন লুকানো হয়েছে। ভিডিওর ফাঁকা ডান/বাম অংশে ডাবল-ট্যাপ করলে ১০ সেকেন্ড সামনে/পিছনে যায়। Play/pause, previous/next, seekbar ও settings রাখা হয়েছে; মাঝের play/pause বাটন গোলাকার।
- ভিডিওর উপরের কোণায় Audio এবং অডিও পেজে Video সুইচ আছে। অনলাইন অডিও থেকে ভিডিওতে গেলে অবস্থান ও অবশিষ্ট কিউ সংরক্ষণের ব্যবস্থা আছে।
- ভিডিওর ডান দিকে উল্লম্ব সোয়াইপে media volume, বামে বর্তমান window-র brightness বদলায়। শতাংশের feedback দেখায়। মাঝখানে নিচে সোয়াইপে আগের মতো minimize হয়। বাস্তব বাটন ও seekbar জেসচার থেকে বাদ রাখা হয়েছে।

## যাচাই

`assembleDebug` ও `testDebugUnitTest` সফল। জেসচার গণনার ৭টি JVM টেস্ট পাস: দুই দিকের ১০-সেকেন্ড সিক, শুরু/শেষের সীমা, অজানা duration, overflow, volume ও brightness সীমা। এটি touch dispatch বা আসল playback/download-এর end-to-end পরীক্ষা নয়। সব ১৩০টি XML parse হয়েছে। APK-এর স্বাক্ষর এবং ভেতরের package/version যাচাই করা হয়েছে।

কোনো Android ফোন বা emulator সংযুক্ত ছিল না; ফোনে install, playback, pause/resume, share এবং gesture-এর ব্যবহারিক পরীক্ষা হয়নি। Android lint চালানোর চেষ্টা হয়েছে, কিন্তু প্রয়োজনীয় `lint-gradle:31.6.1` অফলাইন ক্যাশে না থাকায় সম্পন্ন হয়নি। বিদ্যমান Kotlin/D8 metadata warning আছে; তা সত্ত্বেও APK বিল্ড সফল।

## সীমাবদ্ধতা

Pause/resume এই অ্যাপের চলমান প্রসেসের মধ্যে কাজ করে। প্রসেস মেরে ফেলা বা ফোন restart-এর পর আংশিক ডাউনলোড পুনরারম্ভ হয় না; নতুন করে ডাউনলোড প্রয়োজন। Pause চাপার সময় চলমান একটি blocking read শেষ হতে পারে। রেঞ্জ সমর্থন না করা সার্ভারের সংযোগ pause-এর পরে বিচ্ছিন্ন হলে ট্রান্সফার ব্যর্থ হতে পারে।

AV pair ডাউনলোড আগের মতো পৃথক video ও audio track; শেয়ারের সময় দুটি ফাইল যায়, একত্রিত MP4 নয়। শুধু স্থানীয় অডিও ফাইলে ভিডিও ট্র্যাক না থাকলে Video সুইচ সতর্কবার্তা দেখায়।

## আবার বিল্ড

Android Studio-তে ফোল্ডার খুলুন। Android SDK 35, build-tools 34.0.0 ও উপযুক্ত JDK (এই বিল্ডে JDK 21) ব্যবহার করুন। নিজের SDK path দিয়ে `local.properties` তৈরি করুন অথবা `ANDROID_HOME` সেট করুন।

```sh
./gradlew :app:assembleDebug :app:testDebugUnitTest
```

প্রথমবার Gradle/plugin/Android লাইব্রেরি ডাউনলোডের জন্য ইন্টারনেট প্রয়োজন। পরবর্তীতে ক্যাশ সম্পূর্ণ থাকলে `--offline` ব্যবহার করা যায়। টেস্টের JUnit ও Hamcrest jar `app/libs/test/`-এ রাখা আছে; এগুলো production APK dependency নয়। `verification/` ফোল্ডারে বিল্ড লগ ও টেস্ট ফল দেওয়া হয়েছে। স্থানীয় SDK path, build cache ও signing key সোর্স ZIP-এ নেই।
