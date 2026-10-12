# Third-party notices

Selected OpenShorts source under `vendor/openshorts/` is copyright OpenShorts, MIT licensed, from Marsic1/openshorts commit `b1f5350fcf24b17cb48b581400c35ad9f3974ba5`. Its original license is preserved in `vendor/openshorts/LICENSE`; original and modified hashes plus changes are in `UPSTREAM.json`. No `cloud/` source is packaged.

AutoClip Editor code is MIT licensed. Python dependencies retain their own licenses; the local environment and models are not committed or shipped in this source repository. `requirements-poc.lock.txt` records the tested package versions.

FFmpeg/ffprobe are external executables supplied by the user. The tested full build enables GPL/version3/libx264; this repository does not redistribute those binaries. Public binary packaging, model/font redistribution and a full SBOM/license audit remain a separate release gate. Installed Arial is used locally and is not redistributed.

The YouTube test video and its transcript/media outputs are excluded from Git; downloading for evaluation does not grant public redistribution rights.
