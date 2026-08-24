# Yandex API Endpoints Reference

Complete endpoint reference for all 20 Yandex services.

## Authentication

All endpoints use the same OAuth header:

```
Authorization: OAuth {YANDEX_OAUTH_TOKEN}
```

Exception: Yandex Direct API v5 uses `Bearer` instead of `OAuth`:

```
Authorization: Bearer {YANDEX_OAUTH_TOKEN}
```

## 1. Metrika API

Base: `https://api-metrika.yandex.net`

### Reports

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /stat/v1/data | Table report |
| GET | /stat/v1/data/drilldown | Drill-down report |
| GET | /stat/v1/data/bytime | Time-series report |
| GET | /stat/v1/data/comparison | Comparison report |

**Common params:** `ids` (counter), `metrics`, `dimensions`, `date1`, `date2`, `filters`, `sort`, `limit`, `offset`, `accuracy`

### Metrics Reference

| Metric | Description |
| ------ | ----------- |
| ym:s:visits | Sessions |
| ym:s:pageviews | Page views |
| ym:s:users | Unique users |
| ym:s:newUsers | New users |
| ym:s:bounceRate | Bounce rate |
| ym:s:avgVisitDurationSeconds | Avg session duration |
| ym:s:goal{N}reaches | Goal N completions |
| ym:s:goal{N}revenue | Goal N revenue |
| ym:s:ecommercePurchases | E-commerce purchases |
| ym:s:ecommerceRevenue | E-commerce revenue |

### Dimensions Reference

| Dimension | Description |
| --------- | ----------- |
| ym:s:date | Date |
| ym:s:datePeriodday | Daily period |
| ym:s:lastTrafficSource | Traffic source |
| ym:s:lastSourceEngine | Search engine |
| ym:s:lastAdvEngine | Ad system |
| ym:s:UTMSource | UTM source |
| ym:s:UTMMedium | UTM medium |
| ym:s:UTMCampaign | UTM campaign |
| ym:s:browser | Browser |
| ym:s:operatingSystem | OS |
| ym:s:deviceCategory | Device type |
| ym:s:regionCountry | Country |
| ym:s:regionCity | City |
| ym:s:startURL | Landing page |

### Management

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /management/v1/counters | List counters |
| GET | /management/v1/counter/{id} | Get counter |
| POST | /management/v1/counters | Create counter |
| PUT | /management/v1/counter/{id} | Update counter |
| DELETE | /management/v1/counter/{id} | Delete counter |
| GET | /management/v1/counter/{id}/goals | List goals |
| POST | /management/v1/counter/{id}/goals | Create goal |
| PUT | /management/v1/counter/{id}/goal/{goal_id} | Update goal |
| DELETE | /management/v1/counter/{id}/goal/{goal_id} | Delete goal |
| GET | /management/v1/counter/{id}/filters | List filters |
| GET | /management/v1/counter/{id}/operations | List operations |

### Offline & Expenses

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | /management/v1/counter/{id}/offline_conversions/upload | Upload offline conversions (CSV) |
| POST | /management/v1/counter/{id}/offline_conversions/extended_threshold | Increase offline window |
| GET | /management/v1/counter/{id}/offline_conversions/uploadings | List uploads |
| POST | /management/v1/counter/{id}/expense/upload | Upload expenses (CSV) |
| GET | /management/v1/counter/{id}/expense/uploadings | List expense uploads |
| POST | /management/v1/counter/{id}/user_params/upload | Upload user params |
| POST | /management/v1/counter/{id}/user_params/uploadings | List user param uploads |

### Segments

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /management/v1/counter/{id}/apisegment/segments | List segments |
| POST | /management/v1/counter/{id}/apisegment/segments | Create segment |
| PUT | /management/v1/counter/{id}/apisegment/segment/{seg_id} | Update segment |
| DELETE | /management/v1/counter/{id}/apisegment/segment/{seg_id} | Delete segment |

---

## 2. Direct API v5

Base: `https://api.direct.yandex.com/json/v5/`

All requests are POST with JSON body containing `method` and `params`.

### Services

| Endpoint | Operations | Key Fields |
| -------- | ---------- | ---------- |
| /campaigns | get, add, update, delete, suspend, resume, archive, unarchive | Id, Name, Status, State, Type |
| /adgroups | get, add, update, delete | Id, Name, CampaignId, Status |
| /ads | get, add, update, delete, moderate, suspend, resume, archive | Id, State, Type, TextAd, DynamicTextAd |
| /keywords | get, add, update, delete, suspend, resume | Id, Keyword, Bid, AdGroupId |
| /bids | get, set, setAuto | KeywordId, Bid, ContextBid |
| /reports | get (POST with report params) | Various report types |
| /sitelinks | get, add, delete | Id, Title, Href |
| /vcards | get, add | Id, CompanyName, Phone, Address |
| /audiences | get | various targeting |
| /changes | check, checkCampaigns, checkDictionaries | Timestamp-based |

### Report Types

- ACCOUNT_PERFORMANCE_REPORT
- CAMPAIGN_PERFORMANCE_REPORT
- ADGROUP_PERFORMANCE_REPORT
- AD_PERFORMANCE_REPORT
- CRITERIA_PERFORMANCE_REPORT
- CUSTOM_REPORT
- SEARCH_QUERY_PERFORMANCE_REPORT

---

## 3. Mail (IMAP/SMTP)

### IMAP

- Server: `imap.yandex.ru`
- Port: 993 (SSL)
- Auth: XOAUTH2 with OAuth token

### SMTP

- Server: `smtp.yandex.ru`
- Port: 465 (SSL) or 587 (STARTTLS)
- Auth: Login with app password or OAuth token

### IMAP Commands

```
SELECT INBOX          - Open inbox
SEARCH UNSEEN         - Find unread
SEARCH FROM "user@"   - Search by sender
FETCH n (RFC822)      - Get full message
STORE n +FLAGS (\Seen) - Mark as read
COPY n "FolderName"   - Copy to folder
STORE n +FLAGS (\Deleted) - Mark for delete
EXPUNGE               - Remove deleted
CREATE "FolderName"   - Create folder
LIST "" "*"           - List folders
```

---

## 4. Disk API

Base: `https://cloud-api.yandex.net/v1/disk`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | / | Disk info (total/used space) |
| GET | /resources | Get resource meta |
| PUT | /resources | Create folder |
| DELETE | /resources | Delete resource |
| POST | /resources/copy | Copy resource |
| POST | /resources/move | Move resource |
| GET | /resources/upload | Get upload URL |
| GET | /resources/download | Get download URL |
| PUT | /resources/publish | Publish resource (get public link) |
| PUT | /resources/unpublish | Unpublish resource |
| GET | /resources/files | Flat file list (sortable) |
| GET | /resources/last-uploaded | Recently uploaded |
| GET | /resources/public | List published resources |
| GET | /public/resources | Access public resource by key |
| DELETE | /trash/resources | Empty trash |
| GET | /trash/resources | List trash contents |
| PUT | /trash/resources/restore | Restore from trash |

**Common params:** `path`, `limit`, `offset`, `sort` (`name`, `path`, `created`, `modified`, `size`; prefix with `-` for descending)

---

## 5. Webmaster API v4

Base: `https://api.webmaster.yandex.net/v4`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /user | Get user ID |
| GET | /user/{uid}/hosts | List sites |
| GET | /user/{uid}/hosts/{hid}/summary | Site summary |
| GET | /user/{uid}/hosts/{hid}/indexing/history | Indexing history |
| GET | /user/{uid}/hosts/{hid}/search-queries/all | Search queries |
| GET | /user/{uid}/hosts/{hid}/links/external/samples | Backlinks |
| GET | /user/{uid}/hosts/{hid}/links/external/history | Backlinks history |
| POST | /user/{uid}/hosts/{hid}/recrawl/queue | Submit URL for reindex |
| GET | /user/{uid}/hosts/{hid}/sitemaps | List sitemaps |
| POST | /user/{uid}/hosts/{hid}/sitemaps | Add sitemap |

---

## 6. Audience API

Base: `https://api-audience.yandex.ru/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /management/segments | List segments |
| GET | /management/segment/{id} | Get segment |
| POST | /management/segment/uploading?type=crm | Upload CRM segment |
| POST | /management/segment/lookalike | Create lookalike |
| PUT | /management/segment/{id} | Update segment |
| DELETE | /management/segment/{id} | Delete segment |
| POST | /management/segment/{id}/confirm | Confirm segment |

Segment types: `crm`, `uploading`, `pixel`, `metrika`, `appmetrica`, `lookalike`, `geo`, `geo_circle`

---

## 7. Calendar (CalDAV)

Base: `https://caldav.yandex.ru`

CalDAV protocol (RFC 4791). Use `caldav` Python library.

Key operations:
- `principal.calendars()` - list calendars
- `calendar.date_search(start, end)` - find events
- `calendar.save_event(ical_string)` - create event
- `event.delete()` - delete event
- `calendar.add_todo(ical_string)` - create todo

---

## 8. Tracker API v2

Base: `https://api.tracker.yandex.net/v2`

Required headers: `X-Org-ID` or `X-Cloud-Org-ID`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | /issues/_search | Search issues |
| POST | /issues | Create issue |
| PATCH | /issues/{key} | Update issue |
| GET | /issues/{key} | Get issue |
| POST | /issues/{key}/comments | Add comment |
| GET | /issues/{key}/comments | List comments |
| GET | /issues/{key}/transitions | Available transitions |
| POST | /issues/{key}/transitions/{id}/_execute | Execute transition |
| GET | /queues | List queues |
| GET | /boards | List boards |
| POST | /issues/{key}/links | Link issues |

---

## 9. Forms API

Base: `https://api.forms.yandex.net/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /surveys/ | List forms |
| GET | /surveys/{id}/ | Get form |
| GET | /surveys/{id}/responses/ | Get responses |

---

## 10. IoT API (Smart Home)

Base: `https://api.iot.yandex.net/v1.0`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /user/info | All devices, groups, scenarios |
| GET | /devices/{id} | Device state |
| POST | /devices/actions | Send commands to devices |
| POST | /groups/{id}/actions | Send commands to group |
| GET | /scenarios | List scenarios |
| POST | /scenarios/{id}/actions | Run scenario |

### Capabilities

| Type | Instances | Values |
| ---- | --------- | ------ |
| devices.capabilities.on_off | on | true/false |
| devices.capabilities.color_setting | hsv, temperature_k, rgb | varies |
| devices.capabilities.range | brightness, volume, temperature, channel | 0-100 etc. |
| devices.capabilities.mode | thermostat, fan_speed, work_speed | auto, low, medium, high |
| devices.capabilities.toggle | mute, pause, backlight | true/false |

---

## 11. Telemost API

Base: `https://cloud-api.yandex.net/v1/telemost`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | /conferences | Create meeting |
| GET | /conferences | List meetings |
| GET | /conferences/{id} | Get meeting |
| PATCH | /conferences/{id} | Update meeting |
| DELETE | /conferences/{id} | Delete meeting |

---

## 12. Sprav (Business Listings)

Base: `https://api.sprav.yandex.net/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /companies | List companies |
| GET | /companies/{id} | Get company |
| PUT | /companies/{id} | Update company |
| GET | /companies/{id}/reviews | Get reviews |

---

## 13. Wordstat (via Direct API v4)

Base: `https://api.direct.yandex.com/v4/json/`

| Method | Description |
| ------ | ----------- |
| CreateNewWordstatReport | Start keyword report |
| GetWordstatReportList | List reports |
| GetWordstatReport | Get report data |
| DeleteWordstatReport | Delete report |

---

## 14. PromoPages API

Base: `https://api.promopages.yandex.ru/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /publications | List publications |
| GET | /publications/{id}/stats | Publication stats |

---

## 15. AdFox API v2

Base: `https://adfox.yandex.ru/api/v2`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /campaigns | List campaigns |
| GET | /banners | List banners |
| GET | /sites | List sites |
| GET | /statistics | Get statistics |

---

## 16. MediaMetrika API

Base: `https://api-mediametrika.yandex.net/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /advertisers | List advertisers |
| GET | /campaigns | List campaigns |
| GET | /campaigns/{id}/stats | Campaign stats |

---

## 17. AppMetrica API

Base: `https://api.appmetrica.yandex.net`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /management/v1/applications | List apps |
| GET | /management/v1/application/{id} | Get app |
| GET | /stat/v1/data | Analytics report |

Uses same metrics/dimensions pattern as Metrika but with `ym:ge:` prefix for general, `ym:u:` for users.

---

## 18. Yandex Pay

Base: `https://pay.yandex.ru/api/merchant/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | /orders | Create order |
| GET | /orders/{id} | Get order |
| POST | /orders/{id}/capture | Capture payment |
| POST | /orders/{id}/cancel | Cancel payment |
| POST | /orders/{id}/refund | Refund payment |

---

## 19. Banner Storage (BSAPI)

Base: `https://api.bsapi.yandex.net/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /banners | List banners |
| POST | /banners | Create banner |
| PUT | /banners/{id} | Update banner |
| DELETE | /banners/{id} | Delete banner |

---

## 20. Partner Office

Base: `https://partner.yandex.ru/api/v1`

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | /statistics | Revenue statistics |
| GET | /sites | List partner sites |
| POST | /advmarkup | Ad markup registration (law compliance) |

---

## Rate Limits

| Service | Limit |
| ------- | ----- |
| Metrika | 20 requests/second |
| Direct | 5 units/second, daily limits vary |
| Disk | 50 requests/second |
| Webmaster | 10 requests/second |
| IoT | 10 requests/second |
| Audience | 5 requests/second |
| Others | Typically 10-20 req/sec |

## Error Codes

| Code | Description |
| ---- | ----------- |
| 400 | Bad request (invalid params) |
| 401 | Unauthorized (invalid/expired token) |
| 403 | Forbidden (insufficient scopes) |
| 404 | Not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable |
