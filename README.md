# gta6-twitch-ccu-forecast-01 entry

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/tenamusic/gta6-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/tenamusic/gta6-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Entry for make.fun's [gta6-twitch-ccu-forecast-01 bounty](https://make.fun/bounty/gta6-twitch-ccu-forecast-01) — "Forecast GTA VI's launch-day Twitch viewers hour by hour".

`main.py` (Python 3.13, standard library only) reads each case in the input
directory and writes, for hours 2–24 of the release day, the 5%, 25%, 50%,
75% and 95% quantiles of that hour's mean Twitch viewer count for the
category.

Model: a launch day's shape — each hour's viewers as a ratio to hour 1's —
depends strongly on the launch's scale. This entry pools the release-day
curves of the case's own comparables, weighting each by a Gaussian kernel on
the distance between its log hour-1 viewers and the target's, and reads each
hour's quantiles off the weighted empirical distribution of log-ratios, with
the spread narrowed slightly (×0.9 in log space) as cross-validation
favoured. Leave-one-out CV over the kit's 37 comparable launches (the
contest's pinball loss on the log scale): 0.425 vs the house persistence
baseline's 0.930; on launches with hour-1 ≥ 50k, 0.206 vs 0.251.

Fully deterministic: no randomness, no clock, no network.
