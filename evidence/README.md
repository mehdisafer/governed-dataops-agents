# Evidence retained with the source

New qualification runs write original results, workflow histories, traces, source manifests and service logs under the ignored `evidence/runs/` directory. Credentials and live databases are created in a separate temporary directory and removed when the supervisor stops. Reviewed reports are promoted here or attached to CI; an untracked local file is not a durable published result.

The previous session's temporary source and proof files were unavailable on 2026-11-14. Its historical conversation results are not used to validate this reconstructed implementation. Current acceptance claims require current retained originals.

A hash establishes which bytes were used. It is not an independent audit, certification, or proof of model correctness. Unit tests explicitly label fake Temporal/provider boundaries; native and container runs use real services and are reported separately.
