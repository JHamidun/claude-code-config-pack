---
name: apple-developer
description: Подпись (Developer ID) и нотаризация macOS-приложений/dmg БЕЗ Mac — весь цикл на Windows/Linux + браузере + CI. Использовать когда: «подпиши dmg», «нотаризуй приложение», «приложение повреждено на маке», «Gatekeeper блокирует», «Developer ID сертификат», «App Store Connect API ключ», «notarytool», «продлить Apple Developer». Реквизиты аккаунта храни в своём секрет-хранилище (env / GitHub Secrets).
metadata:
  type: reference
---

# Apple Developer — подпись и нотаризация macOS без Mac

Полный цикл для установщика на electron-builder. **Mac не нужен** — сертификат делается через openssl+браузер, сборка+нотаризация выполняются в GitHub Actions (реальный macOS-раннер).

## Реквизиты аккаунта (плейсхолдеры)

Держи все значения в своём секрет-хранилище (`.env` / менеджер секретов), а .p12/.p8 — в защищённой локальной папке (например `~/apple-signing/`). Ниже — какие поля нужны:

| Что | Плейсхолдер / где взять |
|-----|-------------------------|
| Apple ID | `YOUR_APPLE_ID` (email аккаунта Apple Developer) |
| Team ID | `YOUR_TEAM_ID` (10 символов, в developer.apple.com → Membership) |
| Developer ID Identity | `Developer ID Application: YOUR_LEGAL_NAME (YOUR_TEAM_ID)` |
| Cert ID | `YOUR_CERT_ID` (у сертификата в портале) |
| .p12 | `~/apple-signing/devid.p12` (leaf+ключ+G2 intermediate), пароль в `APPLE_P12_PASSWORD` |
| API Key ID | `YOUR_API_KEY_ID` (роль Developer достаточно) |
| Issuer ID | `YOUR_ISSUER_ID` (UUID вверху страницы API-ключей) |
| .p8 | `~/apple-signing/AuthKey_YOUR_API_KEY_ID.p8` |
| Членство | active (Apple Developer Program, $99/год) |

GitHub Secrets репозитория сборки: `APPLE_CSC_LINK` (base64 p12), `APPLE_CSC_KEY_PASSWORD`, `APPLE_API_KEY_P8` (base64 p8), `APPLE_API_KEY_ID`, `APPLE_API_ISSUER`, `APPLE_TEAM_ID`.

## Зачем это нужно

Неподписанный dmg → macOS Gatekeeper показывает «приложение повреждено и не может быть открыто». Developer ID подпись + нотаризация Apple = открывается обычным двойным кликом. Для распространения ВНЕ App Store нужен именно **Developer ID Application** сертификат (не Distribution) + notarytool.

## Шаг 1. Developer ID Application сертификат (openssl, без Mac)

CSR традиционно делают из Keychain на Mac. На Windows/Linux — openssl:

```bash
WORK=~/apple-signing; mkdir -p "$WORK"; cd "$WORK"
# ГОЧА: системный OPENSSL_CONF может указывать на битый путь — пишем свой мини-конфиг
cat > mini.cnf <<'CNF'
[ req ]
distinguished_name = dn
prompt = no
[ dn ]
emailAddress = YOUR_APPLE_ID
CN = YOUR_LEGAL_NAME
C = YOUR_COUNTRY_CODE
CNF
WINCNF=$(cygpath -w "$WORK/mini.cnf")   # openssl — нативный Win-бинарь, хочет Windows-путь
unset OPENSSL_CONF
MSYS_NO_PATHCONV=1 openssl req -new -newkey rsa:2048 -nodes -keyout devid.key -out devid.csr -config "$WINCNF"
```

**Гочи openssl на git-bash:** (1) `OPENSSL_CONF` из профиля может быть битым → `unset` + свой `-config`; (2) MSYS конвертит пути в `-subj`/`-config` → `MSYS_NO_PATHCONV=1` + `cygpath -w` для Windows-пути; (3) для .p12, читаемого Keychain'ом macOS, нужен `-legacy`.

Загрузка CSR в портал: `developer.apple.com/account/resources/certificates/add` (браузер, developer-сессия) → выбрать **Developer ID Application** → **G2 Sub-CA** (не Previous — истекает) → Choose File → CSR → Continue → Download.

**.cer скачиваем через браузерный fetch с куками** (надёжнее файл-диалога):
```js
// browser_evaluate на странице download:
const r = await fetch(DOWNLOAD_HREF, {credentials:'include'});
const b = new Uint8Array(await r.arrayBuffer());
let s=''; for(const x of b) s+=String.fromCharCode(x); return btoa(s);  // → base64, сохранить как .cer
```

Собрать .p12 (leaf + приватный ключ + промежуточный G2):
```bash
base64 -d cer.b64 > devid.cer
openssl x509 -inform DER -in devid.cer -out devid.pem
curl -fsSL https://www.apple.com/certificateauthority/DeveloperIDG2CA.cer -o g2.cer
openssl x509 -inform DER -in g2.cer -out g2.pem
PASS=$(openssl rand -hex 16)
openssl pkcs12 -export -legacy -inkey devid.key -in devid.pem -certfile g2.pem \
  -name "Developer ID Application: YOUR_LEGAL_NAME (YOUR_TEAM_ID)" -out devid.p12 -passout "pass:$PASS"
```

## Шаг 2. App Store Connect API-ключ (нотаризация)

`appstoreconnect.apple.com/access/integrations/api` — сессия переносится с developer.apple.com (отдельного 2FA НЕ просит). «Ключи команды» → «+» → имя + роль **Разработчик** (Developer хватает для notarytool) → Создать → **Загрузить** (.p8 качается ТОЛЬКО ОДИН РАЗ). Записать **Key ID** (в строке ключа) и **Issuer ID** (вверху страницы).

## Шаг 3. electron-builder: подпись + нотаризация в CI

`package.json` → `build.mac`:
```json
"hardenedRuntime": true,
"gatekeeperAssess": false,
"entitlements": "build/entitlements.mac.plist",
"entitlementsInherit": "build/entitlements.mac.plist",
"notarize": { "teamId": "YOUR_TEAM_ID" }
```
entitlements (hardened runtime для Electron): allow-jit, allow-unsigned-executable-memory, disable-library-validation, allow-dyld-environment-variables.

`build-mac.yml` (GitHub Actions, macos-latest):
```yaml
- name: Prepare notarization API key
  run: |
    mkdir -p "$RUNNER_TEMP/asc"
    echo "${{ secrets.APPLE_API_KEY_P8 }}" | base64 --decode > "$RUNNER_TEMP/asc/AuthKey.p8"
    echo "APPLE_API_KEY=$RUNNER_TEMP/asc/AuthKey.p8" >> "$GITHUB_ENV"
- name: Build signed+notarized
  env:
    CSC_LINK: ${{ secrets.APPLE_CSC_LINK }}          # base64 .p12
    CSC_KEY_PASSWORD: ${{ secrets.APPLE_CSC_KEY_PASSWORD }}
    APPLE_API_KEY_ID: ${{ secrets.APPLE_API_KEY_ID }}
    APPLE_API_ISSUER: ${{ secrets.APPLE_API_ISSUER }}
    APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
  run: npx electron-builder --mac --arm64 --publish never
```

**ГОЧА afterPack:** если есть ad-hoc-подпись в afterPack — пропускать её при реальной подписи (`if (process.env.CSC_LINK) return;`), иначе конфликт. Убрать `CSC_IDENTITY_AUTO_DISCOVERY: false`. Нотаризация добавляет ~10-20 мин к сборке (Apple notary service).

Установка secrets: `base64 -w0 devid.p12 | gh secret set APPLE_CSC_LINK -R <repo>` и т.д.

## ГОЧА→РЕШЕНО: нотаризация с вшитым vendor (архивы с нативным кодом)

**Проблема:** если .app бандлит сторонний нативный код в **архивах** (`vendor/pywheels/*.whl`, `*.tar.gz` и т.п.), нотаризация падает: `status:Invalid, "Archive contains critical validation errors"` → `"The binary is not signed"` для `.so`/бинарников **внутри** архивов. Apple notary РАСПАКОВЫВАЕТ zip/tar и требует Developer ID + secure timestamp у КАЖДОГО Mach-O. Подписать `.so` внутри `.whl` нельзя — переподпись ломает `RECORD` колеса, pip потом откажется ставить.

**РЕШЕНИЕ (проверено): нотаризуем ЧИСТЫЙ app, vendor кладём в dmg рядом, финальный dmg собираем сами.**

1. **vendor ВОН из .app.** `package.json`: убрать vendor из общего `extraResources`; на Windows вернуть через `win.extraResources` (там нотаризации нет). electron-builder **мержит** общий + `win.extraResources` (подтверждено по исходнику `getFileMatchers`), так что Windows не теряет scripts/agent.
2. **main.js `vendorRoot()`**: на mac ищет vendor рядом с .app (`path.resolve(process.resourcesPath,'..','..','..','vendor')` — корень dmg-тома), иначе внутри Resources (Windows/dev). Плюс `bootstrap.vendorAvailable` + UI-предупреждение «запусти из dmg» (если .app перетащили в /Applications без dmg).
3. **package.json** mac: `notarize: true` (+ hardenedRuntime + entitlements). electron-builder нотаризует ЧИСТЫЙ .app (vendor внутри нет → notary доволен) и **staple**-ит тикет.
4. **НЕ класть vendor в `dmg.contents`** — electron-builder сайзит том dmg только под .app (`createStageDmg` из appPath, `computeAssetSize`=stat(dmg)+10%), 1ГБ vendor → **ENOSPC**. Убрать vendor из dmg.contents.
5. **Финальный dmg — свой шаг hdiutil** (после electron-builder): стейджим нотаризованный `release/mac-arm64/*.app` + `vendor/` + txt + `ln -s /Applications`; `hdiutil create -srcfolder <stage> -fs HFS+ -format UDZO` (сам считает размер); подписываем dmg Developer ID (создать временный keychain, `security import` p12, `codesign --sign`). **dmg НЕ нотаризуем** (vendor завалил бы) — но .app застейплен, поэтому запускается **чисто, ноль окон Gatekeeper** (тикет проверяется офлайн из бандла). Проверка: `xcrun stapler validate <app>` → «The validate action worked!».

Итог: нотаризованный+stapled app + подписанный dmg. Приложение открывается двойным кликом без предупреждений.

## 2FA / доверенные номера — ГЛАВНАЯ ГОЧА

- Код 2FA идёт **push-уведомлением на устройства Apple** (iPhone/iPad/Mac) ИЛИ SMS на доверенный номер — **НЕ на email**. Если устройств Apple нет — планируй доступ к доверенному SMS-номеру заранее.
- **developer.apple.com** — сессия могла сохраниться от прошлого входа (заходит без свежего 2FA). **account.apple.com** (смена номеров/пароля) — ВСЕГДА требует свежий 2FA.
- Смена доверенного номера требует код на **текущий** доверенный номер. Если доступа к нему нет — сменить нельзя нормальным путём, только **восстановление аккаунта** (iforgot.apple.com, дни). Это by design.

## Продление членства

`developer.apple.com/account` → «Renew membership» (веб-путь, если устройств Apple нет) → Agree (Developer Program License Agreement) → карта (US$99, списывается в USD). Обработка **до 2 рабочих дней**, потом статус active + письмо-чек на почту.

## Быстрая проверка результата

Нотаризованный dmg: на маке `spctl -a -t open --context context:primary-signature -v YourApp-Setup-*.dmg` → «accepted, source=Notarized Developer ID». Или просто двойной клик — открывается без «повреждено».
