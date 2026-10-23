# Golden tests

Golden tests for the deck grid, the terminal chrome, and the alert banner live
here.

They are not enabled yet. Golden files are platform-sensitive (font rendering
differs between Linux CI, macOS, and Windows), so Phase 1 decides the policy
before the first image is committed. The likely shape:

- Goldens are generated and compared on `ubuntu-latest` only, in a container
  with the same Flutter version as CI.
- Tests use `matchesGoldenFile`, and a failing diff uploads the actual,
  expected, and difference images as CI artefacts.
- Regenerate with `flutter test --update-goldens test/golden`.

Until then, `flutter test` runs the unit and widget tests in the sibling
directories.
