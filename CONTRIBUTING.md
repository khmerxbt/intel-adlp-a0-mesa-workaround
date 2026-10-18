# Contributing

Keep affected-silicon matching narrow and preserve unaffected stepping/device
controls. A successful build is not proof of rendering health. Add your exact
PCI ID/revision, distribution, Mesa/kernel versions, renderer, API, actual pixel
or game result and fresh kernel-error summary. State duration and whether a
compression-enabled control was run on the same recovered boot.

Please redact hostnames, private URLs, IP addresses, serial numbers, account
identifiers, tokens and unrelated log/process details. Do not upload game ISO,
BIOS, firmware, saved games, proprietary drivers or complete private Compose files.
Chinese and English reports are welcome. QXSG and other samples need independent
tests; do not infer support from a similar seller model name.

Run `python3 -m unittest discover -s tests -v`,
`python3 scripts/validate_package.py`, and `sh scripts/check-patches.sh`.
The CI checks source integrity and patch application, not GPU stability. Keep
host deployment/recovery instructions reversible and distribution-specific.
