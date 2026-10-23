# SparkTube 1.4.1 — ভিডিও রেন্ডারিং ও কন্ট্রোল সংশোধন

এই নোটটি আগের PLAYER_CORRECTION_BN.md-এর পরবর্তী সংশোধনের বিবরণ। versionName **1.4.1**, versionCode **10** অপরিবর্তিত। এটি আগের পরীক্ষামূলক APK-এর একই debug certificate দিয়ে সই করা compact test build; production/release signing দাবি করা হচ্ছে না।

## কালো ভিডিওর জন্য পাওয়া সরাসরি কোডের ত্রুটি

আগের QueueForwardingPlayer-এ `object : Player.Listener by listener` ব্যবহার করা হয়েছিল। এই প্রজেক্টের Kotlin compiler Java interface-এর default callback-গুলোকে ওই delegation দিয়ে ফরওয়ার্ড করেনি। কম্পাইলড bridge class-এ শুধু `onAvailableCommandsChanged` ও `onEvents` ছিল; `onRenderedFirstFrame`, `onVideoSizeChanged`, `onTracksChanged` ছিল না।

Media3 PlayerView প্রথম ফ্রেমের callback পেলে তার কালো shutter সরায়। আগের bridge callback গিলে ফেললে, ডিকোডার ভিডিও তৈরি করলেও shutter কালো থেকে যেতে পারে। তাই কেবল SurfaceView handoff বদলানো যথেষ্ট ছিল না। নতুন JVM regression test পুরোনো delegation-এ first-frame callback হারানো এবং নতুন bridge-এ পৌঁছানো পুনরুৎপাদন করে।

সংশোধনে PlayerView সরাসরি raw ExoPlayer-এ যুক্ত হয়েছে; কিউ-সচেতন media session আলাদা facade ব্যবহার করে। সেই facade-এর জন্য PlayerListenerBridge.java Media3 1.3.1-এর ৩৭টি callback স্পষ্টভাবে ফরওয়ার্ড করে। API-coverage test প্রতিটি callback যাচাই করে।

এটি কোড/bytecode-এ নিশ্চিত ত্রুটি এবং সংশোধন; মালিকের ফোনে কালো স্ক্রিন সেরে গেছে—এমন দাবি নয়।

## কন্ট্রোল ও রেন্ডারিং

Previous / বড় Play-Pause / Next এখন activity_player.xml-এর সরাসরি sibling overlay: 52dp / 76dp / 52dp। Media3-এর center/minimal-mode container বা optional findViewById-এর ওপর এই বাটনগুলো নির্ভর করে না। একই সময়ে দুটো Play/Pause দেখানো এড়াতে Media3 template থেকে center transport সরানো হয়েছে; seekbar, সময় ও settings রাখা হয়েছে। Next পরের queued item চালায়; দশ সেকেন্ড seek করে না। প্রথম আইটেমে Previous বর্তমান ভিডিও শুরু থেকে চালায়।

Main ও mini player-এ TextureView ব্যবহৃত হয়েছে; output owner ও stale detach guard রাখা হয়েছে। Decoder fallback চালু। শুধু READY/isPlaying-কে ভিডিও সফল বলা হয় না: দৃশ্যমান, READY, play-requested অবস্থায় বাস্তব first-frame না এলে একবার output rebind, তারপর progressive source fallback, শেষে স্পষ্ট Retry error। ব্যাকগ্রাউন্ডে/পজ অবস্থায় এই recovery হয় না। source rebuild position ও play/pause intent ধরে রাখে। Retry কিউ মুছে ফেলে না এবং local download-কে online URL হিসেবে resolve করে না।

## যেসব ফিচার রাখা হয়েছে

Compact dark/green Audio–Video switch, বাম/ডানে double-tap-এ ১০ সেকেন্ড seek, ডানে vertical volume ও বামে brightness gesture রাখা হয়েছে; standalone দশ সেকেন্ডের বাটন নেই। Lock-screen/notification-এর Previous–Play/Pause–Next queue facade-এ আছে। Swipeable Library, download-এর downloaded/total MB, MB/s, আনুমানিক ETA এবং তিন-ডট Play/Share/Delete-এর source আগের build-এর সঙ্গে byte-for-byte তুলনা করা হয়েছে। Production dependency, সংস্করণ, resource/feature shrinking policy বদলানো হয়নি।

## পরীক্ষা ও পুনরায় বিল্ড

JVM test results, structural-test log, compiled APK XML, signature, zipalign এবং version metadata `verification/render-controls/`-এ আছে। এগুলো ফোনে চালানো rendering/touch/instrumentation test নয়। ADB-তে কোনো Android device যুক্ত নেই; emulator-এও চালানো হয়নি। তাই আসল ফোনে video frames, rotation, mini-player, PiP, gesture এবং lock-screen controls যাচাই এখনও প্রয়োজন। Lint-এর অবস্থা verification-summary.json-এ আলাদা দেওয়া আছে।

JDK 17 ও Android SDK 35 দিয়ে, SDK location স্থানীয়ভাবে সেট করে:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest \
  -x lintVitalAnalyzeCompactTest -x lintVitalReportCompactTest -x lintVitalCompactTest
python3 tools/verify-player-correction.py
```

পুরোনো source ZIP পাশে না থাকলে byte-for-byte baseline comparison test skip হবে; অন্য পরীক্ষা চলবে। সোর্স ZIP-এ local.properties, build cache বা signing keystore নেই। একই versionCode রাখা হয়েছে, তাই পরীক্ষা করার সময় ফোনে সঠিক নতুন APK install হয়েছে কি না নিশ্চিত করা দরকার। স্বাক্ষর না মেললে এই test APK দিয়ে অন্য certificate-এর app-এর ওপর update হবে না; ডেটা হারানোর ঝুঁকি থাকায় যাচাই ছাড়া uninstall করা উচিত নয়।
