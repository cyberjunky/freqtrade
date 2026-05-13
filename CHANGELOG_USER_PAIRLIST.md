# Changelog — User Pairlist Support

## [Unreleased] — 2026-05-13

### Added

#### User-defined pairlist handlers from `user_data/pairlist/`

Custom `IPairList` subclasses placed in `user_data/pairlist/` are now
discovered and loaded by `PairListResolver`, mirroring how strategies are
loaded from `user_data/strategies/`.

**Usage:**

1. Create `user_data/pairlist/MyPairList.py` containing a class that extends
   `IPairList`.
2. Reference it by class name in `config.json`:
   ```json
   "pairlists": [{"method": "MyPairList"}]
   ```

**Files changed:**

| File | Change |
|------|--------|
| `freqtrade/constants.py` | Added `USERPATH_PAIRLISTS = "pairlist"` |
| `freqtrade/resolvers/pairlist_resolver.py` | Set `user_subdir = USERPATH_PAIRLISTS` so the resolver searches `user_data/pairlist/` |
| `freqtrade/configuration/directory_operations.py` | Added `USERPATH_PAIRLISTS` to `sub_dirs` so `freqtrade create-userdir` creates `user_data/pairlist/` |
| `freqtrade/config_schema/config_schema.py` | Removed `"enum": AVAILABLE_PAIRLISTS` from the `method` field, allowing custom class names to pass config validation |
| `build_helpers/schema.json` | Regenerated to match — removed the `"enum"` array from `pairlists → items → properties → method` |
| `tests/plugins/test_pairlist.py` | Added `test_load_pairlist_from_user_data` |
