# NYX iOS Installation
1. Use Xcode to run on simulator or device.
2. For an installable iPhone IPA, set a Team ID and run: 'bash scripts/build_ios_ipa.sh'.
3. Example:
   - export NYX_IOS_TEAM_ID=YOUR_TEAM_ID
   - export NYX_IOS_EXPORT_METHOD=development
   - bash scripts/build_ios_ipa.sh
4. Install IPA via Xcode Devices & Simulators, Apple Configurator, or ideviceinstaller.
