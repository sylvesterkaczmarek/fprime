set -euo pipefail
SRC=Svc/Ccsds/AosFramer/AosFramer.cpp
BUILD=build-fprime-automatic-native-ut
TESTDIR="$BUILD/F-Prime/Svc/Ccsds/AosFramer"
LOG="$VALIDATION_LOG_DIR"
cmake --build "$BUILD" --target Svc_Ccsds_AosFramer_ut_exe -j4 >"$LOG/fixed-build.log" 2>&1
ASAN_OPTIONS=halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 ctest --test-dir "$TESTDIR" --no-tests=error -V >"$LOG/fixed-test.log" 2>&1
cp "$SRC" "$LOG/fixed-source.cpp"
trap 'cp "$LOG/fixed-source.cpp" "$SRC"' EXIT
git show "$BASE_SHA:$SRC" > "$SRC"
cmake --build "$BUILD" --target Svc_Ccsds_AosFramer_ut_exe -j4 >"$LOG/baseline-build.log" 2>&1
set +e
GTEST_FILTER=AosFramerIdlePadding.MixedMaskFillsEveryRemainder ctest --test-dir "$TESTDIR" --no-tests=error -V >"$LOG/baseline-regression.log" 2>&1
result=$?
set -e
if [ "$result" -eq 0 ]; then echo 'Baseline unexpectedly passed'; exit 1; fi
grep -q 'Actual:   0' "$LOG/baseline-regression.log"
grep -q 'Expected: 1' "$LOG/baseline-regression.log"
cp "$LOG/fixed-source.cpp" "$SRC"
cmake --build "$BUILD" --target Svc_Ccsds_AosFramer_ut_exe -j4 >"$LOG/restored-build.log" 2>&1
ASAN_OPTIONS=halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 ctest --test-dir "$TESTDIR" --no-tests=error -V >"$LOG/restored-test.log" 2>&1
grep -E 'PASSED|100% tests' "$LOG/fixed-test.log" "$LOG/restored-test.log"
echo 'Baseline emitted zero frames instead of one, as expected.'
