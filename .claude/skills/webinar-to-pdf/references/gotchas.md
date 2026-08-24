# Common Problems and Solutions

## Playwright Issues

| Problem | Solution |
|---------|----------|
| Page's own `fetch`/ES-module fails under `file://` | Not Playwright — browser CORS policy. Serve over `http://127.0.0.1`. Plain markup, inline CSS and `<img>` load fine from `file://` (see `export-pdf`/`export-png`) |
| `localhost` not resolved | Use `127.0.0.1` instead of `localhost` |
| Two Playwright sessions crash | Run sequentially, never in parallel with `asyncio.gather()` |
| `browserType.launchPersistentContext` fails | Chrome profile locked. Use `p.chromium.launch(headless=True)` without persistent context |
| Connection refused after server restart | Update `BASE_URL` port in scripts. Kill old server process first |

## PDF Generation

| Problem | Solution |
|---------|----------|
| **Slides appear empty/transparent** | CSS animations (`slideIn`, fade) don't complete before screenshot. **Must inject CSS to disable all animations and force opacity.** See fix below |
| Slide content cut off at bottom | Content exceeds 1080px viewport. Reduce fonts, paddings, image sizes |
| `page.pdf()` merges all slides | Do NOT use `page.pdf()` for slide presentations. Use screenshot approach |
| PDF too large (>10MB) | Convert PNG to JPEG (quality=85-90) before `img2pdf` |
| Page count != slide count | Check JS navigation logic. Verify all slides have `.slide` class |
| Page breaks split content | Add `page-break-inside: avoid` to blocks, `page-break-after: avoid` to headers |

## Animation/Opacity Fix (CRITICAL)

Slides with CSS animations (`animation: slideIn 0.6s`) or `opacity: 0` + `transition` will render
as empty or semi-transparent in screenshots. The animation doesn't complete in the 0.3s wait time.

**Fix: Inject this CSS + JS before taking any screenshots:**

```javascript
// Inject ONCE after page load, before screenshot loop
await page.evaluate(`
    const style = document.createElement('style');
    style.textContent = \`
        *, *::before, *::after {
            animation: none !important;
            animation-delay: 0s !important;
            animation-duration: 0s !important;
            transition: none !important;
            transition-delay: 0s !important;
            transition-duration: 0s !important;
        }
        .slide.active,
        .slide.active * {
            opacity: 1 !important;
            visibility: visible !important;
            transform: none !important;
        }
    \`;
    document.head.appendChild(style);

    // Hide UI elements
    document.querySelectorAll('#fullscreenBtn, #avatarBtn, #progressBar, canvas').forEach(el => {
        el.style.display = 'none';
    });
`);

// Then in each slide activation, also force child opacity:
target.querySelectorAll('*').forEach(child => {
    const cs = getComputedStyle(child);
    if (parseFloat(cs.opacity) < 0.5) {
        child.style.opacity = '1';
    }
});
```

**Root cause:** `animation: slideIn 0.6s forwards` overrides inline `style.opacity = '1'` because
`animation-fill-mode: forwards` applies the animation's final state AFTER the animation completes.
Since we kill the animation before it starts, it never reaches `opacity: 1`. The injected CSS
forces `opacity: 1 !important` to override everything.

## Windows-Specific

| Problem | Solution |
|---------|----------|
| File locked (can't overwrite PDF) | Close PDF viewer. Or save with different name (`_FINAL.pdf`) |
| `timeout` command fails in Git Bash | Use `powershell -c "Start-Sleep -Seconds 3"` instead |
| Path separators | Use forward slashes `/` in Python. `os.chdir('C:/path')` works on Windows |
| Encoding issues in HTML | Always use `encoding='utf-8'` when reading/writing files |

## Fonts and Rendering

| Problem | Solution |
|---------|----------|
| Custom fonts not rendering | Use system fonts: `'Segoe UI', -apple-system, sans-serif` |
| Emoji broken in PDF | Wrap emoji in `<span>` with `-webkit-text-fill-color: initial; background: none;` |
| Cyrillic characters garbled | Ensure `<meta charset="UTF-8">` in HTML `<head>` |

## HTTP Server

| Problem | Solution |
|---------|----------|
| Port already in use | Kill existing process: `netstat -ano | findstr :8889` then `taskkill /PID <pid> /F` |
| Server dies silently | Start in background with `run_in_background=true`. Check with `curl http://127.0.0.1:8889/` |
| CSS/images not loading | Ensure `os.chdir()` points to the directory containing HTML files |

## Google Drive Upload

| Problem | Solution |
|---------|----------|
| Token expired | Re-authenticate. Токен лежит в `~/.claude/google_oauth_token.json` |
| File not visible in folder | Check `parents` parameter in upload. Verify folder ID |
| Permission denied | Ensure `drive.permissions().create()` with `type: 'anyone', role: 'reader'` |
| Updating existing file | Use `drive.files().update(fileId=id, media_body=media)` instead of creating new |

## Bash/Script Issues

| Problem | Solution |
|---------|----------|
| Long Python in `bash -c` fails | Write to `.py` file first, then run `python file.py` |
| Heredoc EOF errors | Avoid heredocs for complex scripts. Write to file instead |
| `asyncio.run()` already running | Don't nest `asyncio.run()`. Use `await` in existing event loop |
