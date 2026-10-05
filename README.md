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

MLOps Bench is a self-contained benchmark suite for evaluating coding agents
on MLOps-stage engineering contracts. Each task provides a natural-language
specification, a starting task workspace, a buggy baseline, an oracle
implementation, and executable evaluation tests. The repository does not
provide a top-level benchmark runner; the released task workspaces are designed
to be exercised individually or by a compatible external harness.

The suite covers data pipelines, feature engineering, model training, model
serving, monitoring and observability, CI/CD and governance, and end-to-end
MLOps flow. The accompanying source-project inventory records public project
URLs, pinned commits, and license material used during benchmark construction.
The released task workspaces are self-contained benchmark artifacts; they are
not redistributions of the upstream project source trees.

## Research paper

This repository is the companion artifact for the manuscript:

> Quoc Co Tran, Hitesh Laxmichand Patel, Diwakar Mahajan, Kshitij Bakliwal,
> Avi Sil, and Katrin Kirchhoff. 2026. *MLOps-Bench: Benchmarking AI Agents on
> Production ML Engineering in Real Repositories.*

The paper describes the benchmark motivation, task-construction protocol, human
audits, and agent evaluation methodology. Until archival venue metadata is
available, please cite the work as a manuscript:

```bibtex
@misc{tran2026mlopsbench,
  title = {MLOps-Bench: Benchmarking AI Agents on Production ML Engineering in Real Repositories},
  author = {Quoc Co Tran and Hitesh Laxmichand Patel and Diwakar Mahajan and Kshitij Bakliwal and Avi Sil and Katrin Kirchhoff},
  year = {2026},
  note = {Manuscript}
}
```

## Reproducibility and test counts

F2P and P2P counts refer to public `test_*` functions in each task's
`tests/test_f2p.py` and `tests/test_p2p.py` files, respectively. The task-level
`f2p_test_count` and `p2p_test_count` metadata fields use the same convention.
The auxiliary oracle contract tests under `oracle/tests/` are intentionally not
included in the published F2P/P2P totals.

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
git clone https://github.com/oracle-samples/mlops-bench.git
cd mlops-bench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip pytest
```

## Usage

The dataset is ready to inspect without a compilation step. It does not ship a
top-level evaluation command; locate tasks by repository, MLOps stage, and
instance ID:

```text
dataset/mlops-bench/<repository>/<stage>/<instance>/
```

A task includes the following material:

```text
problem.json              # task statement and requirements
repo/                     # starting task workspace
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

Released under the [Apache License version 2.0](LICENSE)