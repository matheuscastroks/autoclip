# Third-party notices

Selected OpenShorts source under `vendor/openshorts/` is copyright OpenShorts, MIT licensed, from Marsic1/openshorts commit `b1f5350fcf24b17cb48b581400c35ad9f3974ba5`. Its original license is preserved in `vendor/openshorts/LICENSE`; original and modified hashes plus changes are in `UPSTREAM.json`. No `cloud/` source is packaged.

AutoClip Editor code is MIT licensed. Python dependencies retain their own licenses. Apart from the explicitly tracked assets below, local environments and downloaded models are not committed or shipped in this source repository. `requirements-poc.lock.txt` records the tested package versions.

FFmpeg/ffprobe are external executables supplied or provisioned locally. The tested full build enables GPL/version3/libx264; this repository does not redistribute those binaries. Public binary packaging and a full SBOM/license audit remain a separate release gate. The tracked Montserrat ExtraBold font retains its SIL Open Font License 1.1 in `engine/assets/fonts/OFL.txt`; the tracked BlazeFace model retains its Apache-2.0 license in `engine/assets/models/LICENSE`. Their provenance manifests are adjacent to those files.

## Desktop icons

Fluent UI System Icons are copyright (c) 2020 Microsoft Corporation, MIT licensed.
The desktop uses an explicit, statically compiled subset from
`@iconify-json/fluent` 1.2.60 (collection metadata version 1.1.344), with no runtime
icon service. The MIT permission and warranty terms are reproduced in the root
`LICENSE`; this Microsoft copyright notice applies to the icon artwork.
Upstream: <https://github.com/microsoft/fluentui-system-icons> and
<https://github.com/microsoft/fluentui-system-icons/blob/main/LICENSE>.
`unplugin-icons` 24.0.0 is a build-time MIT-licensed tool by Anthony Fu and
contributors. Dependency packages retain their own license notices. Lucide was
removed after the final consumer migration. Binary releases must carry applicable
third-party notices as part of the release gate above.

The YouTube test video and its transcript/media outputs are excluded from Git; downloading for evaluation does not grant public redistribution rights.
