# NYX iOS Installation
Status: simulator build skipped.
1. Use Xcode to run on simulator or device.
2. For an installable iPhone IPA, set a Team ID and run: 'bash scripts/build_ios_ipa.sh'.
3. Example:
   - export NYX_IOS_TEAM_ID=YOUR_TEAM_ID
   - export NYX_IOS_EXPORT_METHOD=development
   - bash scripts/build_ios_ipa.sh
4. If Team ID is unknown, sign in to Xcode (Settings → Accounts) and re-run; the script will try auto-detect.
5. Install IPA via Xcode Devices & Simulators, Apple Configurator, or ideviceinstaller.
