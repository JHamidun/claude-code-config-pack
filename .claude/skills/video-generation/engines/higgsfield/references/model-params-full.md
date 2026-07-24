# Higgsfield — ПОЛНЫЙ справочник параметров ВСЕХ 51 модели (`hf model get --json`, 2026-06-07)

Полные схемы (enum/default/required) в `model-params-full.json`. Ниже — параметры по каждой + выделены проприетарные.

## Полная таблица (job_set_type → type → params)
| jst | type | params |
|---|---|---|
| cinematic_studio_2_5 | image | aspect_ratio, medias, prompt, resolution |
| **cinematic_studio_image** | image | aspect_ratio, batch_size, **camera_aperture_id, camera_focal_length_id, camera_lens_id, camera_model_id**, medias, prompt, resolution(1k/2k/4k) |
| flux_2 | image | aspect_ratio, input_images, model, prompt, resolution |
| flux_kontext | image | aspect_ratio, input_images, prompt |
| gpt_image_2 | image | aspect_ratio, batch_size, medias, prompt, quality, resolution |
| grok_image | image | aspect_ratio, medias, mode, prompt |
| **text2image_soul_v2** (Soul V2) | image | aspect_ratio, **custom_reference_id**(Soul), medias, prompt, quality(1.5k/2k) |
| image_auto | image | aspect_ratio, medias, prompt |
| image_background_remover | image | medias |
| kling_omni_image | image | aspect_ratio, input_images, prompt, resolution |
| **ms_image** | image | aspect_ratio, avatars, batch_size, brand_kit_id, folder_id, medias, product_ids, prompt, quality, resolution, **style_id** |
| marketing_studio_image | image | aspect_ratio, input_images, prompt, resolution |
| nano_banana | image | aspect_ratio, input_images, prompt |
| nano_banana_flash (NB2) | image | aspect_ratio, medias, prompt, resolution |
| nano_banana_2 (NB Pro) | image | aspect_ratio, folder_id, input_images, prompt, resolution |
| **nano_banana_2_ai_stylist** | image | background_preset_id, folder_id, input_image REQ, **outfit_preset_ids, pose_preset_id, user_outfit_ids** |
| **nano_banana_2_skin_enhancer** | image | folder_id, height, input_image, preset_id, width |
| nano_banana_2_shots | image | aspect_ratio, folder_id, height, input_images, width |
| openai_hazel | image | aspect_ratio, input_images, prompt, quality |
| **recraft_v4_1** | image | aspect_ratio, background_color, batch_size, colors, **model_type(standard/vector/utility/utility_vector)**, prompt, resolution |
| seedream_v4_5 | image | aspect_ratio, input_images, prompt, quality |
| seedream_v5_lite | image | aspect_ratio, medias, prompt, quality |
| **soul_cinematic** | image | aspect_ratio(+21:9), **custom_reference_id**, medias, prompt, quality(1.5k/2k) |
| **soul_location** | image | aspect_ratio, prompt |
| **soul_cinema_studio** | image | aspect_ratio, custom_reference_id, **enhance_prompt**, medias, prompt, quality, **style_id** |
| **topaz_image** | image | denoise, **face_enhancement**(+creativity/strength), **model(Standard V2/Low Resolution V2/CGI/High Fidelity V2/Text Refine)**, sharpen, input_image, width/height, output_width/height |
| z_image | image | aspect_ratio, prompt |
| **brain_activity** (Virality) | text | folder_id, medias |
| **sam_3_3d** | video | detection_threshold, **export_textured_glb**, medias REQ, prompt, seed |
| cinematic_studio_3_0 | video | aspect_ratio, duration, medias, prompt |
| cinematic_studio_video | video | aspect_ratio, duration, medias, prompt, slow_motion, sound |
| **cinematic_studio_video_v2** | video | aspect_ratio, duration, **genre(auto/action/horror/comedy/western/suspense/intimate/spectacle)**, medias, **mode(pro/std)**, prompt |
| **draw_to_video** | video | aspect_ratio, duration, enhancer, generate_audio, prompt, **ref_image, sketch REQ, video REQ**, resolution |
| veo3 | video | aspect_ratio, input_image, model, prompt |
| veo3_1 | video | aspect_ratio, duration, input_image, model, prompt, quality |
| veo3_1_lite | video | aspect_ratio, duration, generate_audio, medias, prompt |
| grok_video | video | aspect_ratio, duration, medias, prompt |
| grok_video_v15 | video | duration, medias, prompt, resolution |
| kling2_6 | video | aspect_ratio, duration, input_image, prompt, sound |
| kling3_0 | video | aspect_ratio, duration, medias, mode, prompt, sound |
| **llm_text** | video | input_images, model, reasoning_effort, system_prompt, user_prompt |
| **marketing_studio_video** | video | ad_reference_id, aspect_ratio, avatars, duration, generate_audio, hook_id, medias, **mode(ugc/…/tv_spot/try_on)**, product_ids, resolution, setting_id, web_product_ids |
| minimax_hailuo | video | duration, input_images, model, prompt, resolution |
| reframe | video | aspect_ratio, duration, folder_id, medias, resolution |
| sam_3_video | video | apply_mask, folder_id, frames_count, medias, prompt |
| seedance1_5 | video | aspect_ratio, duration, medias, prompt, resolution |
| **seedance_2_0** | video | aspect_ratio(+auto/21:9), duration, **genre(auto/action/horror/comedy/noir/drama/epic)**, medias, **mode(std/fast)**, prompt, resolution(480/720/1080) |
| **soul_cast** | video | aspect_ratio, budget, prompt |
| **topaz_video** | video | aspect_ratio, duration, enhancement, **frame_interpolation, frame_rate**, frames_count, input_video, resolution(1080p/2160p) |
| wan2_6 | video | aspect_ratio, duration, medias, prompt, quality |
| wan2_7 | video | aspect_ratio, duration, medias, prompt, resolution |

## Проприетарные «фишки» Higgsfield (нет у апстрима — ради них hf.exe)
- **Soul family (`custom_reference_id`)** — Soul V2/Cinematic/Cinema-Studio привязывают обученный Soul через `custom_reference_id` (= обученный `hf soul-id`). Это их система консистентности лиц. quality 1.5k/2k.
- **Cinematic Studio Image — эмуляция физической камеры:** `camera_model_id` + `camera_lens_id` + `camera_focal_length_id` + `camera_aperture_id` (выбор реальной камеры/объектива/ФР/диафрагмы из их базы) → фото-точная оптика. Уникальная фича.
- **genre/mode на видео:** Seedance 2.0 (`genre` action/horror/comedy/noir/drama/epic, `mode` std/fast) + Cinematic Studio V2 (genre +western/suspense/intimate/spectacle, mode pro/std) — жанровая режиссура поверх Seedance.
- **AI Stylist** — виртуальная примерка: `pose_preset_id` + `background_preset_id` + `outfit_preset_ids` + `user_outfit_ids` (база поз/фонов/одежды).
- **Recraft V4.1 `model_type`** — vector/utility (векторная графика, иконки, мокапы).
- **Topaz** — `model` (Standard V2/Low Resolution V2/CGI/High Fidelity V2/Text Refine) + `face_enhancement` (creativity/strength) для image; `frame_interpolation`+`frame_rate` для video.
- **draw_to_video** — `sketch`(REQ)+`video`(REQ)+`ref_image` (motion-аннотации стрелками).
- **sam_3_3d** — `export_textured_glb` (3D-меш с текстурой из фото!).
- **ms_image/marketing_studio_video** — `style_id`/`brand_kit_id`/`avatars`/`product_ids`/`hook_id`/`setting_id`/`web_product_ids` (DTC-движок).
- **llm_text** — встроенный LLM (system_prompt/user_prompt/reasoning_effort/model) для текст-задач внутри пайплайна.

→ Полный JSON со всеми enum/default → `model-params-full.json`. Для прямого вызова через `hf generate create <jst> --param value` или POST /jobs. Связано: [[model-provider-map.md]] (что бить напрямую), [[exclusive-models-soul-ms-virality.md]].
