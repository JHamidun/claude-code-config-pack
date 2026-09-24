# Editor runtime contract

Use the installed `higgsedit` and shipped `types/fable.d.ts` as authority. Do not hardcode paths or versions.

```bash
command -v higgsedit
higgsedit --help
higgsedit do <project> --list
```

## Native behavior

- Project size and fps are fixed at creation.
- Script build replaces the timeline; `do` and `ops` mutate existing state.
- `rect` and text use top-left boxes. `positionX/Y` replace placement; `offsetX/Y` offset it.
- Persistent frames support column, row, equal-column grid, and none layouts. Frame children use local time and cannot outlive the frame.
- Frame `width`/`height` animation reflows layout. `reveal` changes visibility without reflow.
- Frame media slots center `contain` and `cover`; `fill` stretches.
- Composed media is picture-only. Use a cut or separate audio source for sound.
- Components evaluate their node tree at local zero; timeline placement applies only to the component root.
- Rendering has no per-frame callback API.

`effectParam` tracks are supported on media nodes in automatically sized frame slots. Effects are evaluated at each motion-blur sample, so animated effect parameters participate in sampled motion blur.

## Inspection

```bash
higgsedit inspect PROJECT --id CLIP_ID --at 6.5
```

`--at` requires `--id` or `--name` and uses concatenated timeline seconds. Results include timeline, scene, clip-local time, active state, and center-time evaluated effects. `execution.verified=false` means inspection did not prove effect execution. Inspect output is not world-space geometry or rendered-pixel proof.

## Supported limits

Duplicate replacement tracks are refused; raw offsets add and uniform scales multiply. Keyframes must strictly increase and stay within the node lifetime. Paths support `M/L/H/V/C/Q/Z`, not arcs. Shaped typography is opt-in with limited multilingual fallback. Shader-bearing graphics may differ from browser preview; use native output. Render cost depends on media, resolution, effects, and concurrency.

`check` validates supported document inputs. `sweep` reports flat frames. Neither is a visual or audio verdict.
