name: Kivy Android Build (Docker Action)

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build_android:
    # Bu safar biz Ubuntu emas, Docker konteynerini ishlatamiz
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    # --- ENG MUHIM QADAM ---
    # Maxsus Buildozer Action ishlatiladi. Bu, barcha SDK/NDK/p4a/Python muammolarini hal qiladi.
    - name: Run Buildozer Build
      uses: ArtemSBulgakov/buildozer-action-v1@v1.2 # Kivy/Buildozer uchun maxsus action
      with:
        # Buildozer.spec faylidagi barcha sozlamalarni ishlatadi
        command: buildozer android debug 
        # API litsenziyalarini avtomatik qabul qilish uchun
        build-flags: --skip-update

    # 2. Natijani yuklash
    - name: Upload APK artifact
      uses: actions/upload-artifact@v4
      with:
        name: ari-assistant-apk
        path: bin/*.apk