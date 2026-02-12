# test_lib

KiCad library repository prepared for the KiCad Plugin and Content Manager (PCM).

## What this repo contains

- `lib-content/` - library content that will go into the package archive
- `pcm/metadata.base.json` - base package metadata
- `scripts/build_pcm_repo.py` - builds:
  - `dist/releases/<identifier>_v<version>_pcm.zip`
  - `dist/packages.json`
  - `dist/repository.json`

## Update library metadata

Edit `pcm/metadata.base.json` before publishing:

- `name`, `description`, `description_full`
- `identifier` (reverse-domain style; example: `com.github.degesz.test-lib`)
- `author`, `maintainer`, `license`
- `resources.homepage`

## Build package + PCM index

```bash
python3 scripts/build_pcm_repo.py --version 1.0.0 --github-owner degesz --repo test_lib
```

This command generates the package zip and repository files in `dist/`.

## Publish on GitHub

1. Create and push repository:

```bash
git init
git add .
git commit -m "Initial KiCad PCM library setup"
gh repo create degesz/test_lib --public --source . --remote origin --push
```

2. Create release and upload the generated zip:

```bash
gh release create v1.0.0 "dist/releases/com.github.degesz.test-lib_v1.0.0_pcm.zip" \
  --title "v1.0.0" \
  --notes "Initial PCM release"
```

3. Commit and push `dist/` files (so `repository.json` and `packages.json` are available):

```bash
git add dist
git commit -m "Add PCM repository index for v1.0.0"
git push
```

## Add to KiCad Package Manager

In KiCad:

1. Open **Plugin and Content Manager**
2. **Manage repositories** / **Add**
3. Paste this URL:

```text
https://raw.githubusercontent.com/degesz/test_lib/main/dist/repository.json
```

Then refresh and install your library package.
