#!/usr/bin/env bash
# Merge upstream freqtrade `develop` into `lite`, without committing, and list what needs a
# human look before the merge is committed (see LITE.md, "Keeping up with upstream"):
#
#   1. upstream changes to code lite removed (FreqAI, plotting, webhook/Discord,
#      producer/consumer, strategy-updater, Edge): must NOT come back;
#   2. upstream changes to files lite fixed for backtest accuracy (A1-A14): check that the
#      merge keeps lite's fix and that upstream didn't change the same logic another way;
#   3. merge conflicts.
#
# Usage: scripts/lite-sync.sh        (on a clean `lite` checkout)
# Then review, run the tests, `git commit`, push. `git merge --abort` throws it away.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

UPSTREAM=https://github.com/freqtrade/freqtrade
[ "$(git branch --show-current)" = lite ] || { echo "not on lite"; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "working tree not clean"; exit 1; }

git fetch -q "$UPSTREAM" develop:refs/remotes/upstream/develop
n=$(git rev-list --count lite..upstream/develop)
echo "upstream develop: $n new commits"
[ "$n" = 0 ] && exit 0
git log --oneline --no-merges lite..upstream/develop | sed 's/^/  /'

REMOVED='freqtrade/freqai/|freqtrade/plot/|freqtrade/rpc/webhook\.py|freqtrade/rpc/discord\.py|external_message_consumer|producer_pairlist|ProducerPairList|strategyupdater|strategy_utils_commands|requirements-freqai|requirements-plot|Dockerfile\.(freqai|plot)|docs/(freqai|plotting|webhook-config|producer-consumer)|tests/freqai/'
FIXED='freqtrade/optimize/backtesting\.py|freqtrade/strategy/interface\.py|freqtrade/persistence/trade_model\.py|freqtrade/freqtradebot\.py|freqtrade/exchange/exchange\.py|freqtrade/optimize/backtest_caching\.py'

changed=$(git diff --name-only lite...upstream/develop)
echo
echo "== touches code lite removed (keep it removed):"
echo "$changed" | grep -E "$REMOVED" | sed 's/^/  /' || echo "  none"
echo "== touches files with lite's accuracy fixes (review the merged result):"
echo "$changed" | grep -E "$FIXED" | sed 's/^/  /' || echo "  none"
echo "== new dependencies / version changes:"
git diff lite...upstream/develop -- requirements.txt requirements-hyperopt.txt | grep -E '^[+-][A-Za-z]' | sed 's/^/  /' || echo "  none"

echo
if git merge --no-ff --no-commit upstream/develop >/dev/null 2>&1; then
    echo "merged without conflicts (not committed)"
else
    echo "conflicts:"
    git diff --name-only --diff-filter=U | sed 's/^/  /'
fi
# files upstream added in removed areas come back silently in a clean merge: list them
back=$(git diff --cached --name-only --diff-filter=A | grep -E "$REMOVED" || true)
if [ -n "$back" ]; then
    echo "removed code that this merge would bring back (git rm them):"
    echo "$back" | sed 's/^/  /'
fi
echo
echo "next: review the lists above, run the tests (tests/optimize, tests/strategy at least),"
echo "      then: git commit -m 'Merge upstream develop into lite (...)' && git push origin lite"
