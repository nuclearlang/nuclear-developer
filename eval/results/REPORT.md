# Nuclear Developer — evaluation

Local model: qwen2.5-coder:3b (coder) + the Nuclear Smart Graph. Reference: Claude sonnet. References cost USD 0.89; the local run took 337.5 s on CPU.

| split | tasks | Sonnet passes | local passes | equivalent (both pass) |
|---|---|---|---|---|
| train | 27 | 22 | 23 | 20 |
| test | 18 | 17 | 14 | 14 |
| all | 45 | 39 | 37 | 34 |

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

## Tasks

| task | split | Sonnet | local | local attempts | what the local answer missed |
|---|---|---|---|---|---|
| model-new-book | train | ✓ | ✓ | 1 |  |
| model-reader | train | ✓ | ✓ | 1 |  |
| model-book-changes | test | ✓ | ✓ | 1 |  |
| entity-book | train | ✓ | ✓ | 1 |  |
| entity-loan | train | ✓ | ✓ | 1 |  |
| entity-reader | test | ✓ | ✗ | 3 | 9:3 N0013 '@column' has no member below it: a decorator goes on the line right above the field or method it modifies |
| repo-by-author | train | ✓ | ✓ | 1 |  |
| repo-available-since | train | ✗ | ✓ | 1 |  |
| repo-by-title | test | ✓ | ✓ | 1 |  |
| repo-count-open-loans | train | ✓ | ✓ | 1 |  |
| usecase-create-book | train | ✗ | ✓ | 1 |  |
| usecase-get-book | train | ✓ | ✓ | 1 |  |
| usecase-lend-book | test | ✓ | ✓ | 2 |  |
| usecase-books-of-author | train | ✓ | ✓ | 1 |  |
| appcomponent-books | train | ✓ | ✓ | 1 |  |
| appcomponent-loans | test | ✓ | ✓ | 1 |  |
| controller-books | train | ✓ | ✓ | 1 |  |
| controller-author | train | ✗ | ✗ | 1 | ~books.byAuthor(name) |
| controller-loans | test | ✓ | ✓ | 1 |  |
| tools-books | train | ✓ | ✓ | 1 |  |
| tools-loans | test | ✓ | ✓ | 1 |  |
| agent-librarian | train | ✓ | ✓ | 1 |  |
| agent-loans | test | ✓ | ✓ | 1 |  |
| graph-summary | train | ✗ | ✗ | 1 | question: string |
| graph-two-steps | test | ✗ | ✗ | 3 | 7:5 N0019 'draft' is a method of 'Review': it cannot be assigned; give the variable another name |
| tests-create-book | train | ✓ | ✓ | 1 |  |
| tests-missing-book | test | ✓ | ✓ | 1 |  |
| listener-loans | train | ✓ | ✓ | 1 |  |
| flutter-model | train | ✓ | ✓ | 1 |  |
| flutter-repository | test | ✓ | ✗ | 1 | book(id: int) Result< |
| service-isbn | train | ✗ | ✓ | 1 |  |
| function-label | test | ✓ | ✓ | 1 |  |
| flutter-usecase | train | ✓ | ✓ | 1 |  |
| flutter-state-model | train | ✓ | ✗ | 3 | loaded: Book[]; error: BookError; loading: boolean |
| flutter-manager | test | ✓ | ✓ | 1 |  |
| flutter-screen | test | ✓ | ✓ | 1 |  |
| flutter-repository-post | train | ✓ | ✓ | 1 |  |
| web-repository | train | ✓ | ✓ | 1 |  |
| web-tile | test | ✓ | ✓ | 1 |  |
| web-service | train | ✓ | ✓ | 1 |  |
| web-manager | test | ✓ | ✓ | 1 |  |
| web-appcomponent | train | ✓ | ✓ | 1 |  |
| feature-books-by-author | train | ✓ | ✗ | 4 | appcomponent BooksAppComponent; booksOf() = BooksOfAuthor.exec |
| feature-new-reader | test | ✓ | ✗ | 10 | appcomponent ReadersAppComponent; 201 |
| feature-books-list-app | test | ✓ | ✓ | 5 |  |
