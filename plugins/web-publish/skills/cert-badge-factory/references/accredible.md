# Accredible — выдача цифровых бейджей по шагам

Пошаговая инструкция «с нуля»: от аккаунта Accredible до бейджа в LinkedIn у
каждого выпускника группы (в примерах — группа из 24 человек). Аккаунт нужен
свой: заводится на `accredible.com`, бесплатный пробный план — до 20 получателей.
Всё, что взято из документации, помечено ссылкой и датой статьи; чего в
документации нет — написано «не подтверждено».

Проверено 12.09.2026 по help.accredible.com (новый центр помощи на
`help.accredible.com/s/article/…`; старые ссылки вида `/hc/en-us/articles/…`
теперь требуют входа и в поиске всплывают зря) и docs.api.accredible.com.

## 0. Сколько это стоит и что даёт бесплатный аккаунт

- **Free Trial:** «Any new Accredible account can create certificates and badges
  for up to 20 people». Бейджи, сертификаты или то и другое вместе — без
  ограничений по типу; выданное не удаляется, если потом перейти на платный план.
  — [Can I Try Before I Sign-Up For a Plan?, 26.06.2025](https://help.accredible.com/s/article/can-i-try-before-i-sign-up-for-a-plan)
- **Считают людей, а не бейджи:** тариф ограничивает число уникальных получателей
  в год, каждому можно выдать сколько угодно credentials.
  — [accredible.com/pricing](https://www.accredible.com/pricing)
- **Launch** — «Starts at $45/month» при годовом контракте, 50 получателей;
  Connect и Growth — по запросу. — там же.

**Вывод для группы из 24 человек:** в бесплатный лимит (20) вся группа не помещается.
Либо 20 в триале и 4 после апгрейда, либо сразу Launch (50 человек — хватит
и на следующие потоки). Триал безопасен: всё, что выдано в нём, останется.

## 1. Подготовить картинку бейджа

Требования Accredible к своей картинке (для загрузки готового дизайна):

> The file must be a PNG · The image must be square · at least 256 × 256 pixels
> · The optimal dimension for a badge is 400 × 400 pixels · Recommended: the
> background of the image is transparent · don't make the image too large
> — [How Do I Design a Digital Badge?, 29.05.2024](https://help.accredible.com/s/article/how-to-design-a-badge)

Наш генератор делает ровно это — 400×400 PNG, круг на прозрачном фоне:

```bash
S=~/.claude/skills/cert-badge-factory/scripts
python $S/make_badges.py --theme company --title "Искусственный интеллект в работе" --level "Практикум" --year 2026 --out badge_company_ai.png
python $S/make_badges.py --theme vibe    --title "Вайбкодинг: старт" --level "Уровень 1" --year 2026 \
    --brand-name Your --brand-tag School --brand-by "by Your Name" --out badge_vibe_start.png
```

Название — до ~35 знаков, три строки максимум; скрипт сам ужимает кегль и
предупредит в консоли, если упёрся в минимум. Один бейдж — одно достижение
(один курс/поток), картинка **общая для всех получателей**.

### Почему на картинке нет фамилии

Так устроен сам Accredible, и это подтверждается тремя местами документации:

1. Картинка бейджа — это *Badge Design*, он привязывается к группе целиком
   (`badge_design_id` у группы), а «Designs can be used across multiple Groups»
   — [API: Groups / Designs](https://docs.api.accredible.com/).
2. «If you want specific details to appear on your credentials, like names and
   issue dates, use a certificate» — бейдж для широкого шаринга, сертификат для
   деталей — [What is a Digital Open Badge?, 02.06.2024](https://help.accredible.com/s/article/what-is-a-digital-open-badge).
3. «You don't need to cram loads of text onto your badge… a viewer can click on
   the badge and be taken to the relevant credential view webpage» с именем,
   датой и издателем — [How Do I Design a Digital Badge?, 29.05.2024](https://help.accredible.com/s/article/how-to-design-a-badge).

Оговорка: в собственном редакторе Accredible (Badge Builder Studio) можно
поставить на бейдж «attributes» — тогда система сама впечатает, например, имя
при публикации. Но это работает только для дизайна, собранного в их редакторе,
а не для загруженного PNG. Нам это не нужно: имя, почта и дата живут в записи
credential и на странице проверки.

## 2. Загрузить дизайн бейджа в кабинет

1. В шапке кабинета нажать **Designs** → справа сверху **Create Badge Design**
   — откроется Badge Builder Studio.
2. Слева вкладка **Images** → загрузить наш PNG. Проследить, чтобы картинка
   стояла по центру и заполняла холст («make sure that it is centered and fills
   the badge canvas»).
3. **Save Badge Design.** Дать дизайну понятное имя, например
   `Badge — ИИ в работе — поток 2026`.

Источник: [How Do I Design a Digital Badge?, 29.05.2024](https://help.accredible.com/s/article/how-to-design-a-badge).

## 3. Завести группу (Group)

Группа — «контейнер» одного достижения: **на каждый курс/поток своя группа**
(«You will need to create an individual group for each achievement»). Дизайн
при этом можно переиспользовать между группами.

1. В шапке **Groups** → справа сверху **Create Group**. Открывается страница
   Credential Information.
2. Заполнить:
   - **Display Name** — название достижения, которое увидит получатель
     (подставляется в атрибут `[group.course_name]`). Например
     «Искусственный интеллект в работе».
   - **Identifier** — внутренний код для поиска в списке, получателю не виден:
     `CERT-2026-AI`.
   - **Course Website** — ссылка на страницу программы (кнопка «Course Website»
     на странице бейджа, если включить её во вкладке Visibility).
   - **Description** — 2–4 предложения о том, что человек прошёл и умеет: этот
     текст попадает на страницу проверки и в LinkedIn.
   - **Skills** — 3–6 навыков через тег (Accredible подсказывает свои).
3. **Group Appearance** → значок карандаша → **Select Badge** → выбрать
   загруженный дизайн. Если сертификата у группы нет — бейдж и есть единственный
   дизайн; если есть оба, отметить, какой **Primary**: он грузится первым на
   странице и уходит в соцсети.
4. **Save.**
5. Проверить глазами: на странице группы кнопка **Preview** покажет макет
   с выдуманным именем; **Email a Preview** пришлёт тестовое письмо себе
   (лимит получателей не тратится).

Источники: [How Do I Create a Group?, 12.03.2025](https://help.accredible.com/s/article/how-do-i-create-a-group),
[How Do I Add a Badge to a Group?, 29.05.2024](https://help.accredible.com/s/article/adding-a-badge-to-a-group).

### Настройки группы, на которые стоит взглянуть (левое меню в группе)

- **Achievement type** — тип достижения, попадает в файлы Open Badge 3.0 / W3C VC.
- **Language** — язык писем получателям (в кабинете 36 языков). Есть ли среди
  них русский — **не подтверждено**: в списке языков API (`language` у группы)
  русского нет (en, es, pt, de, fr, ja, zh, tr, ar, he, …). Проверить в
  выпадашке; если нет — письма уйдут на английском, сам бейдж от этого не страдает.
- **Allow Duplicates** — дубли ловятся **по почте**, не по имени.
- **Emails On/Off** — можно выключить письма группы и разослать ссылки самому.
- **Expiration Period** — для наших бейджей не нужен.

Источник: [Group Settings — General Settings, 13.01.2026](https://help.accredible.com/s/article/group-settings-general-settings).

## 4. Выдать 24 бейджа одним файлом (Spreadsheet Upload)

Это основной путь. Что говорит документация:

> Be sure to include the three required columns and corresponding records:
> **Recipient Name, Recipient Email and Issue Date.** If you do not provide an
> Issue Date, Accredible will automatically set the Issue Date to the date the
> credential was created.
>
> The format of the dates you upload must be either 'MM/DD/YYYY', 'DD/MM/YYYY',
> or 'YYYY/MM/DD.' You must also ensure you assign the corresponding format
> after importing your spreadsheet.
>
> When creating credentials for multiple groups, you must include a **Group ID**
> along with the Recipient Name and Recipient Email.
> — [How to Issue a Batch Of Credentials — Spreadsheet Upload, 29.05.2024](https://help.accredible.com/s/article/how-to-issue-a-batch-of-credentials-spreadsheet-upload)

Принимаются CSV, XLS, XLSX. Колонки Accredible распознаёт по названию сам
(«Student_name» он поймёт как `recipient.name`), нераспознанные предложит
сопоставить вручную или пропустить (**Skip**).

### 4.1 Собрать файл

Список людей — текстовый файл «ФИО;почта» по строке:

```
Иванова Мария Сергеевна;m.ivanova@example.com
Петров Алексей Игоревич;a.petrov@example.com
```

```bash
python make_badges.py --roster roster.txt --csv --issue-date 2026-09-12 --out roster_accredible.csv
```

Получается:

```
Recipient Name,Recipient Email,Issue Date
Иванова Мария Сергеевна,m.ivanova@example.com,2026/09/12
Петров Алексей Игоревич,a.petrov@example.com,2026/09/12
Сидорова Ольга,o.sidorova@example.com,2026/09/12
```

Дата намеренно в формате `YYYY/MM/DD` — его нельзя спутать с американским.
Если выдаёшь сразу в несколько групп, добавь `--group-id <ID>` — появится
четвёртая колонка `Group ID` (ID берётся из списка групп: **Browse Groups** на
странице загрузки для нескольких групп).

### 4.2 Загрузить

1. В шапке **Credentials** → **Create Credentials** → **For Single Group** →
   выбрать группу. (Либо на карточке группы внизу справа **Create Credentials**.)
2. **Upload Spreadsheet** → выбрать наш CSV. (Рядом есть **Download Spreadsheet
   Template** — можно сверить, что колонки совпали.)
3. **Assign Columns to Attributes** — проверить, что три колонки распознаны:
   Recipient Name, Recipient Email, Issue Date. Если над колонками алерт
   «Required attributes» — навести и посмотреть, чего не хватает. Выбрать формат
   даты **YYYY/MM/DD**. → **Next**.
4. **Validate Records** — система считает валидные записи, отдельно показывает
   *warnings* (например, дубль почты — публикуются вместе с валидными, если не
   поставить «Exclude records with warnings») и *errors* (эти надо править,
   иначе не опубликуются). Список ошибок можно скачать CSV — там те же колонки
   плюс колонка с текстом ошибки.
5. **Publish Credentials** — в первый раз выбрать **«Create, but don't
   publish»**: письма ещё не уходят.
6. После обработки → **View Unpublished Credentials** → открыть 2–3 штуки по ID,
   проверить имя, почту, дату. Опечатки правятся прямо там.
7. Отметить все галочкой → **Publish** → **Confirm**. В этот момент каждому
   уходит письмо со ссылкой на его бейдж.

Для пары человек быстрее форма: **Create Credentials via Form** → поля Recipient
Name / Email / Issue Date → **Add Another Recipient** → **Create Credentials** →
затем так же **Review Unpublished** → **Publish**.
— [Manual Upload, 03.07.2025](https://help.accredible.com/s/article/how-to-issue-a-batch-of-credentials-manual-upload).

## 5. Что получает человек и как вешает в LinkedIn

- Письмо со ссылкой на страницу бейджа вида `https://www.credential.net/<id>`
  (формат из ответов API). На странице — имя, достижение, дата, издатель,
  кнопка проверки.
- **Download** внизу страницы → PNG, JSON Open Badge 3.0 или JSON W3C VC
  — [How Do I Download a Digital Badge?, 13.01.2026](https://help.accredible.com/s/article/how-do-i-download-a-digital-badge).
- **LinkedIn:** на странице бейджа в боковой панели **Add to Profile** →
  **Get Started** — открывается форма LinkedIn «Add license or certification»,
  поля копируются кнопками «copy text». Появится в разделе «Licenses &
  Certifications». Источник — статья старого центра помощи «Add your Credential
  to Linkedin» (help.accredible.com/hc/…/206949065, сейчас за логином);
  в новом центре статья «How Do I Add My Credential to LinkedIn?» есть в списках
  «Related Articles», прямую ссылку получить не удалось — **шаги не подтверждены
  свежей версией**, но механика LinkedIn та же: Certification URL = ссылка на
  credential.net.

## 6. API — если захочется выдавать скриптом

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.
>
> Альтернатива здесь готова: разделы 1–5 (картинка, группа, CSV и загрузка в кабинете) обходятся без API-ключа.

**Где ключ.** Имя в правом верхнем углу → **Settings** → **General Settings** →
**Manage API Keys** → **Add API Key** → имя и уровень прав → **Save**.
— [API and Integration FAQs, 14.01.2026](https://help.accredible.com/s/article/api-faq),
[How Do I Find My Integration API/Consumer Key?, 10.07.2025](https://help.accredible.com/s/article/how-do-i-find-my-integration-api-key).

⚠ **Кому доступно:** «Our Connect and Growth Plans come with API Key management
access included… Our Launch plan subscription can have API Key management as a
purchased Add-on» (там же). Есть ли ключ у триала и у Launch без доплаты —
**не подтверждено**; там же сказано, что для готовых интеграций (LMS) ключ
показывается на странице **Integrations** без «API Key management». Для 24
человек API не нужен — CSV закрывает задачу.

**Как ходить** (docs.api.accredible.com, снято 12.09.2026):

- База `https://api.accredible.com`; для EU-аккаунтов `eu.api.accredible.com`;
  песочница `sandbox.api.accredible.com` — только на Connect/Growth.
- Заголовки: `Authorization: Token token=<API_KEY>`, `Content-Type: application/json`.
- Лимит: 2000 запросов за 5 минут с одного IP (429 при превышении).
- Один бейдж: `POST /v1/credentials`, обязательные `recipient.name`,
  `recipient.email`, `group_id`; дата `issued_on` в `YYYY-MM-DD`; `approve` —
  публиковать сразу (по умолчанию да, но в Settings → General Settings есть
  выключатель «Automatically publish Credentials created via the API»).
- Пачкой: `POST /v2/credentials/bulk_create` — **до 30 credentials в запросе**,
  ответ 207 Multi-Status с ошибками по каждой записи. Если кредитов не хватило,
  credentials создаются, но не публикуются — опубликуешь после оплаты.
- Группа: `POST /v1/issuer/groups`, обязательные `name` (внутреннее),
  `course_name`, `course_description`; бейдж — `badge_design_id`;
  `primary_design_id`. Дизайн загружается в кабинете, через API его ID можно
  получить из списка Designs.

Скрипт умеет собрать JSON-пачки под bulk_create:

```bash
python make_badges.py --roster roster.txt --api-json --group-id 123456 --issue-date 2026-09-12 --out bulk.json
curl -X POST https://api.accredible.com/v2/credentials/bulk_create \
  -H "Authorization: Token token=$ACCREDIBLE_API_KEY" -H "Content-Type: application/json" \
  --data @bulk.json
```

Ключ, если появится, класть в `~/.claude/.credentials.master.env` как
`ACCREDIBLE_API_KEY`.

## 7. Чек-лист перед публикацией

- [ ] Дизайн бейджа загружен и стоит по центру холста (Designs).
- [ ] Группа: Display Name, Description, Skills заполнены; бейдж выбран; Preview просмотрен.
- [ ] Язык писем проверен в выпадашке группы.
- [ ] CSV: три колонки, почты без опечаток, дата в `YYYY/MM/DD`, кодировка UTF-8 без BOM.
- [ ] Первая загрузка — «Create, but don't publish», 2–3 записи открыты глазами.
- [ ] Лимит получателей: триал — 20 человек; 24 человека = Launch или два захода.
- [ ] Publish → Confirm — письма ушли; себе можно выдать 25-й бейдж для проверки LinkedIn-флоу (лучше на триале не тратить лишнего получателя — использовать Email a Preview).

## Что не подтверждено первоисточником (12.09.2026)

- Русский язык в списке языков писем/страницы бейджа.
- Наличие API-ключа на Free Trial и на Launch без add-on.
- Точные шаги кнопки «Add to Profile» по актуальной версии статьи про LinkedIn.
- Ограничение на число строк в одном CSV (документация говорит только «от сотен до десятков тысяч — займёт от минут до часов»).
