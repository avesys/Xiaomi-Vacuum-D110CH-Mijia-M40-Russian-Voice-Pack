#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
import time

from miio import Device


def md5_and_size(path: str):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest(), os.path.getsize(path)


def miot_get_properties(dev: Device, props):
    # props: list of dicts with siid/piid (optionally did)
    return dev.send("get_properties", props)


def miot_set_properties(dev: Device, props):
    # props: list of dicts with siid/piid/value (optionally did)
    return dev.send("set_properties", props)


def main():
    ap = argparse.ArgumentParser(description="Set voice pack for xiaomi.vacuum.d110ch via MIoT local (IP+token)")
    ap.add_argument("--ip", required=True)
    ap.add_argument("--token", required=True, help="32-hex token")
    sub = ap.add_subparsers(dest="cmd", required=True)

    st = sub.add_parser("status", help="Show audio-related properties")
    st.add_argument("--poll", type=int, default=0, help="Poll every N seconds (0 = once)")

    ins = sub.add_parser("install", help="Install voice pack by URL+md5+size")
    ins.add_argument("--lang-id", required=True, help="Language/pack id (e.g. RU, EN, R2307_RU)")
    ins.add_argument("--url", required=True, help="Direct URL to voice pack archive (tar.gz usually)")
    ins.add_argument("--md5", default=None, help="MD5 checksum (hex). If omitted and --file given, computed.")
    ins.add_argument("--size", type=int, default=None, help="Size in bytes. If omitted and --file given, computed.")
    ins.add_argument("--file", default=None, help="Local file to compute md5/size from (does NOT upload it)")
    ins.add_argument("--wait", type=int, default=60, help="Seconds to poll progress after setting (0 = no wait)")

    args = ap.parse_args()

    dev = Device(args.ip, args.token)
    dev.timeout = 5

    # d110ch audio service (from MIoT spec): siid=7
    # piid=1 volume, piid=2 voice-packet-id, piid=3 voice-change-state, piid=4 set-voice
    audio_props = [
        {"siid": 7, "piid": 1},
        {"siid": 7, "piid": 2},
        {"siid": 7, "piid": 3},
    ]

    if args.cmd == "status":
        def once():
            r = miot_get_properties(dev, audio_props)
            print(json.dumps(r, ensure_ascii=False, indent=2))

        if args.poll and args.poll > 0:
            while True:
                once()
                time.sleep(args.poll)
        else:
            once()
        return

    if args.cmd == "install":
        md5 = args.md5
        size = args.size

        if args.file:
            calc_md5, calc_size = md5_and_size(args.file)
            md5 = md5 or calc_md5
            size = size or calc_size

        if not md5 or not size:
            print("ERROR: need --md5 and --size (or provide --file to compute them).", file=sys.stderr)
            sys.exit(2)

        payload = {"id": args.lang_id, "url": args.url, "md5": md5, "size": int(size)}
        value = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

        # Primary attempt (most common for MIoT local)
        set_req = [{"siid": 7, "piid": 4, "value": value}]

        # Fallback variant (некоторые устройства любят did)
        set_req_alt = [{"did": "audio", "siid": 7, "piid": 4, "value": value}]

        last_err = None
        for req in (set_req, set_req_alt):
            try:
                res = miot_set_properties(dev, req)
                print("set_properties response:")
                print(json.dumps(res, ensure_ascii=False, indent=2))
                last_err = None
                break
            except Exception as e:
                last_err = e

        if last_err:
            print(f"ERROR sending set_properties: {last_err}", file=sys.stderr)
            sys.exit(1)

        if args.wait and args.wait > 0:
            print(f"\nPolling voice-change-state for {args.wait}s ...")
            t_end = time.time() + args.wait
            while time.time() < t_end:
                try:
                    r = miot_get_properties(dev, [{"siid": 7, "piid": 2}, {"siid": 7, "piid": 3}])
                    print(json.dumps(r, ensure_ascii=False))
                except Exception as e:
                    print(f"poll error: {e}", file=sys.stderr)
                time.sleep(5)

        return


if __name__ == "__main__":
    main()
