# Nuclear Developer — evaluation

Local model: qwen2.5-coder:3b (coder) + the Nuclear Smart Graph. Reference: Claude sonnet. References cost USD 0.89; the local run took 348.8 s on CPU.

| split | tasks | Sonnet passes | local passes | equivalent (both pass) |
|---|---|---|---|---|
| train | 27 | 22 | 27 | 22 |
| test | 18 | 17 | 16 | 15 |
| all | 45 | 39 | 43 | 37 |

## Rounds (test split: local passes / Sonnet passes)

- round 1: 9 / 5 (all: 23 / 15)
- round 2: 8 / 10 (all: 26 / 25)
- round 3: 10 / 10 (all: 28 / 25)
- round 4: 14 / 17 (all: 38 / 39)
- round 5: 14 / 17 (all: 38 / 39)
- round 6: 14 / 17 (all: 38 / 39)
- round 7: 14 / 17 (all: 38 / 39)
- round 8: 14 / 17 (all: 37 / 39)
- round 9: 14 / 17 (all: 37 / 39)
- round 10: 13 / 17 (all: 37 / 39)
- round 11: 13 / 17 (all: 37 / 39)
- round 12: 8 / 17 (all: 29 / 39)
- round 13: 15 / 17 (all: 38 / 39)
- round 15: 15 / 17 (all: 38 / 39)
- round 17: 14 / 17 (all: 37 / 39)
- round 18: 15 / 17 (all: 38 / 39)
- round 19: 16 / 17 (all: 40 / 39)
- round 20: 14 / 17 (all: 39 / 39)
- round 21: 14 / 17 (all: 39 / 39)
- round 22: 16 / 17 (all: 43 / 39)
- round 23: 16 / 17 (all: 43 / 39)

## Tasks

| task | split | Sonnet | local | local attempts | what the local answer missed |
|---|---|---|---|---|---|
| model-new-book | train | ✓ | ✓ | 1 |  |
| model-reader | train | ✓ | ✓ | 1 |  |
| model-book-changes | test | ✓ | ✓ | 1 |  |
| entity-book | train | ✓ | ✓ | 1 |  |
| entity-loan | train | ✓ | ✓ | 1 |  |
| entity-reader | test | ✓ | ✓ | 1 |  |
| repo-by-author | train | ✓ | ✓ | 1 |  |
| repo-available-since | train | ✗ | ✓ | 1 |  |
| repo-by-title | test | ✓ | ✓ | 1 |  |
| repo-count-open-loans | train | ✓ | ✓ | 1 |  |
| usecase-create-book | train | ✗ | ✓ | 1 |  |
| usecase-get-book | train | ✓ | ✓ | 1 |  |
| usecase-lend-book | test | ✓ | ✓ | 1 |  |
| usecase-books-of-author | train | ✓ | ✓ | 1 |  |
| appcomponent-books | train | ✓ | ✓ | 1 |  |
| appcomponent-loans | test | ✓ | ✓ | 1 |  |
| controller-books | train | ✓ | ✓ | 1 |  |
| controller-author | train | ✗ | ✓ | 2 |  |
| controller-loans | test | ✓ | ✓ | 1 |  |
| tools-books | train | ✓ | ✓ | 1 |  |
| tools-loans | test | ✓ | ✓ | 1 |  |
| agent-librarian | train | ✓ | ✓ | 1 |  |
| agent-loans | test | ✓ | ✓ | 1 |  |
| graph-summary | train | ✗ | ✓ | 1 |  |
| graph-two-steps | test | ✗ | ✓ | 1 |  |
| tests-create-book | train | ✓ | ✓ | 1 |  |
| tests-missing-book | test | ✓ | ✓ | 1 |  |
| listener-loans | train | ✓ | ✓ | 1 |  |
| flutter-model | train | ✓ | ✓ | 1 |  |
| flutter-repository | test | ✓ | ✓ | 1 |  |
| service-isbn | train | ✗ | ✓ | 1 |  |
| function-label | test | ✓ | ✗ | 3 | age(year: int, now: int) string |
| flutter-usecase | train | ✓ | ✓ | 1 |  |
| flutter-state-model | train | ✓ | ✓ | 1 |  |
| flutter-manager | test | ✓ | ✓ | 1 |  |
| flutter-screen | test | ✓ | ✓ | 1 |  |
| flutter-repository-post | train | ✓ | ✓ | 1 |  |
| web-repository | train | ✓ | ✓ | 1 |  |
| web-tile | test | ✓ | ✓ | 1 |  |
| web-service | train | ✓ | ✓ | 1 |  |
| web-manager | test | ✓ | ✓ | 1 |  |
| web-appcomponent | train | ✓ | ✓ | 1 |  |
| feature-books-by-author | train | ✓ | ✓ | 5 |  |
| feature-new-reader | test | ✓ | ✗ | 13 | components/readers/data/entities/reader.nuc:9:3 N0102 'email' is declared twice in 'Reader'; each member is declared onc |
| feature-books-list-app | test | ✓ | ✓ | 6 |  |
