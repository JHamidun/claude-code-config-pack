# Game flow — `type: "game"`

> **Use `sandbox_exec` for all code edits.** Read `references/repo-and-sandbox.md`
> first: `website_repo_access` checks out and pushes without exposing credentials.
> Commit in the returned checkout path and push before the 15-minute lease expires.


A game is a website whose template ships **realtime multiplayer rooms**. Same
CLI, same repo layout, same deploy and publish; what differs is what you write
and where the rules live.

Games used to run on a separate engine with its own deploy/publish tools.
They don't any more — that engine is being retired, and its commands are gone.
If you find a reference telling you to publish a game any other way than
`deploy_website`, it is out of date.

## Create

```
create_website  type: "game"  category: "<genre>"  subdomain: "<name>"
```

- **`category` is REQUIRED and must be a game genre** — `arcade`, `puzzle`,
  `shooter`, `platformer`, `rpg`, `strategy`, `racing`, `simulation`,
  `adventure`, `action`, `fighting`, `survival`, `horror`, `sports`,
  `card-board`, `education`, `endless-runner`, `moba`, `music-rhythm`,
  `sandbox-building`. Fetch the live list with `list_website_categories`;
  a site category (`cinematic`, `ads-marketing`, …) is rejected.
- **Do NOT pass a template.** A game scaffolds from the one template a game
  can use; naming any other is a 422.
- `subdomain` as always — it becomes the live URL.

## Read the contract that ships with the repo

The scaffold's **`app/AGENTS.md`** is the authoritative contract, and it travels
with the code so it cannot drift from the template you actually got. Read it
before writing anything. In short:

| File | What it is | Edit? |
| --- | --- | --- |
| `app/src/logic.js` | **The game** — six pure functions | **Yes, this is the game** |
| `app/public/index.html` + `client.js` | The screen and the input | **Yes** |
| `app/src/room.ts` | Sockets, state, fan-out | Rarely |
| `app/src/worker.ts` | Routes `/ws/<room>` | Almost never |

The six exports are `meta`, `setup`, `validateAction`, `applyAction`,
`isGameOver`, `viewFor`. `bun run check:logic` enforces the mechanical rules as
part of the build — no imports, no `Date.now()`/`Math.random()`, JSON-serializable
state.

Two rules the checker cannot enforce and that decide whether the game is any
good:

- **`validateAction` is the only defence.** The client is untrusted and can send
  any action at any time. Whose turn it is, whether the move is in range,
  whether the target is legal — all of it belongs there.
- **`viewFor` is how you hide information.** What it returns is the *only* thing
  that player receives. For a card game return that player's hand and everyone
  else's card *count*, never the full state.

## Build, deploy, publish — identical to the other types

```
cd app && bun run build            # runs check:logic + tsc
deploy_website   website_id: <id>
publish_website  website_id: <id>
```

Deploy ships the live game at `<subdomain>.higgsfield.app`; publish lists it on
the community feed. As with every type, **fill `app/src/app-meta.json` before
publishing** (`og_title`, `og_description`, `og_image_url`,
`marketplace_cover_url`) — a game with an empty `og_title` is invisible on the
feed. See the cover + metadata section of this bundle's `SKILL.md`.

## Testing it

The template ships vitest against the real workerd runtime
(`app/tests/room.test.ts`), driving the room through actual WebSockets. Run
`bun run test` in `app/`. A game whose rules you changed should get a test for
the rule — the suite is the safety net for the wire protocol every game shares.

Play-test with two browser tabs on the deployed URL: rooms are per-path
(`/ws/<room>`), so two tabs on the same room join the same game.

## Art and audio

The asset pipeline is in this bundle, under the `game-` prefix. Read
`references/game-design-system.md` FIRST — it settles the game profile, the core
loop and the asset manifest — then `references/game-stylization.md` to derive the
STYLE FORMULA every visual prompt reuses byte-for-byte. No visual should exist
before that formula does.

Then the reference matching each manifest row:

| Asset | Reference |
| --- | --- |
| Sprites, backgrounds, UI | `references/game-stylization.md` |
| Spritesheets / 2D animation | `references/game-2d-animation.md` |
| Tiles, walls, ground, PBR maps | `references/game-textures.md` |
| Music, SFX, voice | `references/game-audio.md` |

**Build 2D games here.** The image-to-3D pipeline — mesh generation, rigging,
animation clips, procedural rigs — is not available on this client: there is no
image-to-3D tool on this tool surface, and the GLB scripts that would do the
rest depend on Blender, which the sandbox image does not carry. Do not offer the
user a 3D game, and do not start one intending to find a way. A 2D game with a
strong art direction is the deliverable; the three references above cover it
end to end.

The texture tooling those references drive ships in this bundle's `scripts/`,
already installed in every sandbox at
`$HF_WORKFLOWS/website-builder-flow/scripts/`. Run them from there with
`sandbox_exec`; never recreate a bundled script from memory.

Assets land in `app/public/`; keep `design/assets.csv` beside them so the
manifest travels with the game.

## Single-player is fine

Nothing here forces multiplayer. `meta: { minPlayers: 1, maxPlayers: 1 }` gives a
single-player game that still gets rooms, persistence and the same deploy — many
of the games on the platform are exactly that.
