# SparkTube — পপআপ/PiP ভিডিও সংশোধন

## কী ঠিক করা হয়েছে
আগের কোডে `onPause()`-এর সময় PiP flag এখনো false থাকলে ভিডিওর TextureView থেকে player বিচ্ছিন্ন হতো। PiP callback শুধু layout বদলাত; player ফের জোড়া দিত না। ফলে সিস্টেমের পপআপ controls থাকলেও ভিডিওর আউটপুট হারানোর পথ ছিল। এটি কোডভিত্তিক diagnosis; ফোনে সমস্যাটি reproduce করা হয়নি। অ্যাপে আলাদা floating-overlay service নেই: Android PiP একই PlayerActivity/TextureView ব্যবহার করে।

এখন pause-এর সময় আউটপুট রাখা হয়; activity সত্যিই অদৃশ্য হলে `onStop()`-এ detach হয়। `onStart()`, `onResume()` ও PiP-entry callback আউটপুট নিশ্চিত করে। PiP চলাকালে orientation/configuration callback আর সাধারণ watch-page layout বসাতে পারে না; ভিডিও পুরো ছোট উইন্ডোতে Fit হিসেবে থাকে। পপআপে app-এর controller বন্ধ, সিস্টেমের PiP/media-session controls অক্ষত; বের হলে স্বাভাবিক controller ও portrait/landscape layout ফেরে। Stop-এ PiP flag পরিষ্কার হয়; destroy-এ অতিরিক্ত detach নিরাপত্তা আছে। আগের surface-owner identity guard mini-player-এর নতুন surface ভুল করে বিচ্ছিন্ন হওয়া আটকায়।

## যা অপরিবর্তিত
versionName **1.4.1**, versionCode **10**, package `com.sparktube.app` এবং আগের test APK-এর signing certificate একই। আগের audio-downloads source ZIP-এর সঙ্গে সব app source, resource, library ও Gradle file তুলনায় কেবল `PlayerActivity.kt` বদলেছে। Player engine, TextureView configuration, gestures ও controls-এর bindings, notification service, compact Audio/Video switch, Library এবং audio/video download UI অপরিবর্তিত। কোনো dependency বা বড় asset যোগ হয়নি।

APK **10,303,732 bytes**, প্রায় **10.30 MB**; আগের APK থেকে **-100 bytes**। এটি আগের মতো debug-certificate-এ signed compact test build; production release নয়।

## যাচাই ও সীমা
Build সফল, **46 JVM unit tests** এবং **22 source/XML regression checks** পাস। Package/version, আগের certificate-এর সঙ্গে মিল, APK signature এবং ZIP alignment যাচাই হয়েছে। `verification/pip-fix/`-এ log, diff ও summary আছে। এই source checks Android lifecycle বা ভিডিও rendering-এর runtime test নয়। আগের audio verifier-এর পুরোনো two-file-only historical diff এই নতুন পরিবর্তনের জন্য প্রযোজ্য নয়; তার চারটি feature check চালানো হয়েছে, আর নতুন verifier সর্বশেষ audio-downloads ZIP-এর সঙ্গে সম্পূর্ণ app-file comparison করেছে।

কোনো physical Android device বা emulator সংযুক্ত নেই। ফোনে install, PiP-তে সত্যিকারের চলমান ছবি, pause/play, ফিরে আসা, resize, notification বা gestures-এর end-to-end test হয়নি। তাই ফোনে সমস্যাটি নিশ্চিতভাবে সেরেছে বলা যাচ্ছে না। Offline cache-এ lint dependency না থাকায় lintVital tasks বাদ দেওয়া হয়েছে; lint পাস দাবি করা হচ্ছে না।

## ফোনে ছোট পরীক্ষা
ভিডিওতে চলমান ছবি দেখা গেলে Home চাপুন এবং PiP button দিয়েও আলাদাভাবে পরীক্ষা করুন। পপআপে ছবি চলতে থাকা, pause/play, ছোট-বড় করা, পূর্ণ প্লেয়ারে ফেরা, portrait/landscape এবং close করে app খুললে mini-player দেখা যাচাই করুন। এরপর Audio/Video switch, notification controls ও Library/download pages দেখুন। সমস্যা থাকলে ফোনের model/Android version এবং সমস্যার সময়ের SparkTube crash/logcat output প্রয়োজন হবে।

## সোর্স থেকে বিল্ড
JDK 21 ও Android SDK প্রয়োজন। নিজের SDK path দিয়ে `local.properties` তৈরি করুন; version অপরিবর্তিত রাখুন। সাধারণ build:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
python3 tools/verify-pip-fix.py
```

এখানে ব্যবহৃত offline build:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
```

APK build/JVM tests-এর জন্য পুরোনো ZIP লাগে না। Historical byte-comparison verifier-এর জন্য parent directory-তে আগের audio-downloads ও player-fixed source ZIP প্রয়োজন। Source ZIP-এ editable source, wrapper, dependencies-এর vendored JAR, tests ও verification আছে; local SDK path, cache, build output, APK ও signing key নেই। APK ও ZIP-এর SHA-256 আলাদা manifest-এ দেওয়া হয়েছে।
