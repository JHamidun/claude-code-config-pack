# Higgsfield GrowthBook — РАСШИФРОВАНО (80 feature flags, 2026-06-07)

Был помечен «заблокировано навсегда (AES-шифр)» → **взломан**. Метод:
1. `clientKey` + `decryptionKey` из JS-бандла (чанк `59116-*.js`): `new GrowthBook({apiHost:"https://cdn.growthbook.io", clientKey:"sdk-xvw0BRhZqdyIJWy", decryptionKey:"ZowSD058cjcD8tyBJ1qWIA=="})`.
2. Блоб `encryptedFeatures` (формат `<iv_b64>.<ct_b64>`) с `https://cdn.growthbook.io/api/features/sdk-xvw0BRhZqdyIJWy` (публичный).
3. AES-128-CBC расшифровка (`crypto.subtle`, key = base64-decode decryptionKey).
→ воспроизводимо в любой момент тем же ключом.

## Флаги по категориям (default + кол-во rules)
**Доступ к моделям/фичам (gated rollout):** access-model-veo3.1 · access-nano-banana-2 · access-kling-2.5-turbo · kling-o1-image · early-access-minimax · early-access-seedance · seedance_fast_720 · wan26-audio-access · keyframe-access · soul-reference-access · soul-canvas · workflow-studio-allowed · on-demand-enabled · use-seedream(no) · access-image-style-category-dump.
**Генерация/продукт:** image-chatgpt(true) · iconic-scenes(true) · video-start-end-frame(true) · flow-vfx(true) · free-video-test · free-gen-selector(+extended) · gen-count-ab · **character-train**(gated-аллоулист ~200 user-id) · **orchestrator-model-ab**(control — A/B оркестратор-LLM Supercomputer!) · soul-feed-empty-state · welcome-quiz-id.
**Прайсинг/монетизация (масса A/B):** pricing-ab-test(pricing_v2) · pricing-abc-(plus_49)/enabled(OFF) · pricing-reverse-order · pricing-adjustable-credits · pricing-pro-hide · pricing-mobile-selling-test · pricing-business-design · credit-top-up-ab-test · credit-history-shown · creator-monthly-upsell-v4 · ultimate-to-creator-bundle-monthly/annual(v2) · plan-set-max-v1/v2 · plan-set-ps-a1/a2/a3 · new-team-plan · ww-basic-starter(BASIC) · mobile-ab-pricing-v4 · custom/multi-step-mobile-checkout.
**Промо/онбординг/ретеншн:** promotion-banner(METAL MELTING) · promotion-link(Ads/Speak) · generation-upsell(Generate faster) · personal-promotion(+60-70, 2026-05-17) · winback-offer · upsell-birthday-discount · cashback-challenge-100 · chase-promotion · kling-exclusive-promotion · kling-3-here-show · upgrade-flow-ab-test · user-quiz-onboarding-ab · ai-onboarding-karma(ON) · tour-v1 · no-activity-ab · new-auth-modal · success-url(/viral-boards) · header-recommended-card · free-plan-banners.
**Платежи/прочее:** stripe-tax · subscription-payment-failed-email-ab · adobe-plugin-edit-video-enabled(true) · adobe-plugin-draw-to-video-enabled(true) · media-upload-user-agreement · old-explore-page · mobile-basic-discount-offer(50/50).

## Инсайты (что это даёт)
- **Дорожная карта/гейтинг:** видно какие модели за фиче-флагом (veo3.1, nano-banana-2, kling-o1, minimax, seedance-fast, wan26-audio) → что у них в раскатке.
- **`orchestrator-model-ab`** подтверждает A/B оркестратор-LLM в Supercomputer (мы это вытащили из /claudesfield/models).
- **`character-train`** — обучение Soul-персонажа в gated-аллоулисте (~200 конкретных user-id; не сохраняю — PII).
- **Прайсинг:** десятки A/B на ценах/планах/чекауте — их монетизация целиком на экспериментах (pricing_v2 текущий, plus_49 дефолт).
- **adobe-plugin** флаги → у них есть Adobe-плагин (edit-video + draw-to-video).
→ Это не критично для нашего скилла, но полная карта их продукт-стратегии. Для нас: подтверждает порядок раскатки моделей + что Soul-train/workflow-studio — gated.
