<!--
Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Contributing to MLOps Bench

We welcome contributions that improve benchmark quality, documentation, metadata,
and evaluation tests.

## Opening issues

For dataset defects, documentation corrections, or enhancement requests, please
open a GitHub issue with the affected benchmark instance ID, a concise
description, and reproduction steps where applicable. Do not use GitHub issues
to report security vulnerabilities; follow the instructions in
[SECURITY.md](./SECURITY.md).

## Contributing benchmarks and tests

Before opening a pull request:

1. Discuss material benchmark additions or removals in an issue.
1. Keep every task self-contained under `dataset/mlops-bench/`.
1. Preserve task metadata and upstream provenance in `dataset/metadata/`.
1. Include or update the task's F2P and P2P tests when changing task behavior.
1. Run the relevant oracle test from the task's `oracle/` directory.
1. Do not add credentials, personal data, or generated caches.

## Oracle Contributor Agreement

Before submitting a pull request, you must have signed the
[Oracle Contributor Agreement][OCA] (OCA). Your commits must include the
following line using the name and email address used to sign the OCA:

```text
Signed-off-by: Your Name <you@example.org>
```

Add this automatically by committing with `--signoff` or `-s`:

```text
git commit --signoff
```

Only pull requests from contributors whose OCA can be verified can be accepted.

## Pull request process

1. Ensure an issue exists for the proposed change.
1. Fork the repository and create a descriptive branch.
1. Update documentation and metadata required by the change.
1. Include clear validation steps in the pull request description.
1. Reference the tracking issue in the pull request.

## Code of conduct

Follow the [Golden Rule](https://en.wikipedia.org/wiki/Golden_Rule). For more
specific community guidance, see the [Contributor Covenant Code of Conduct][COC].

[OCA]: https://oca.opensource.oracle.com
[COC]: https://www.contributor-covenant.org/version/1/4/code-of-conduct/
