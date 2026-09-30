<!--
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

# MLOps Bench

MLOps Bench is a dataset of repository-grounded MLOps engineering tasks for
evaluating coding agents. Each task includes a problem statement, a repository
snapshot, a buggy baseline, an oracle implementation, and evaluation tests.

## Contents

- `dataset/mlops-bench/` contains 212 benchmark tasks across seven MLOps stages.
- `dataset/metadata/` contains the source-repository inventory, pinned commits,
  Apache-2.0 license texts, and applicable upstream notices.
- Each benchmark contains F2P, P2P, and oracle contract tests.

The dataset manifest records 636 F2P tests and 856 P2P tests, for 1,492 test
cases in total.

## Getting started

### Prerequisites

- Git
- Python 3.9 or later
- `pytest` to run the Python evaluation tests

No Oracle Cloud service, API key, build system, or deployment environment is
required to use the dataset.

### Installation

Clone the repository and install the test runner in an isolated environment:

```bash
git clone https://github.com/oracle/mlops-bench.git
cd mlops-bench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip pytest
```

## Usage

The dataset is ready to inspect without a compilation step. Locate tasks by
repository, MLOps stage, and instance ID:

```text
dataset/mlops-bench/<repository>/<stage>/<instance>/
```

A task includes the following material:

```text
problem.json              # task statement and requirements
repo/                     # starting repository snapshot
buggy/                    # intentionally incomplete baseline
oracle/                   # reference implementation
tests/test_f2p.py         # fail-to-pass evaluation tests
tests/test_p2p.py         # pass-to-pass evaluation tests
```

To run an oracle contract test for a selected task, run `pytest` from its
`oracle/` directory. For example:

```bash
TASK=dataset/mlops-bench/01_GOOGLECLOUDPLATFORM__MLOPS_WITH_VERTEX_AI/01_data_pipeline/MLO-01_GOOGLECLOUDPLATFORM__MLOPS_WITH_VERTEX_AI-01_DATA_PIPELINE-20260728_194731
(cd "$TASK/oracle" && python -m pytest -q tests/test_stage_contract.py)
```

## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please [review our contribution guide](./CONTRIBUTING.md)

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security vulnerability disclosure process

## License

Copyright (c) 2026 Oracle and/or its affiliates.

*Replace this statement if your project is not licensed under the UPL*

Released under [Apache License version 2.0](LICENSE)