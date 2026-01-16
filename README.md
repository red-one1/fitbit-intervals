# Fitbit → Intervals.icu Daily Sync

A small Python app that pulls daily health data from the Fitbit Web API and publishes it to Intervals.icu.

## Setup

1. Create a Fitbit app and obtain OAuth credentials and a refresh token.
2. Create an Intervals.icu API token and note your athlete ID.
3. Copy .env.example to .env and fill in values.

## Install

- Create a virtual environment and install dependencies from requirements.txt.

## Run

- Run the app:
  - python -m fitbit_intervals
- Specify a date:
  - python -m fitbit_intervals --date 2026-01-15

## Payload mapping

The app builds a payload using INTERVALS_FIELD_MAP_JSON. Defaults:

- weight -> weight
- restingHR -> rhr
- sleepSecs -> sleep.minutes
- sleepScore -> sleep.score
- avgSleepingHR -> sleep.avg_hr
- spO2 -> spo2
- hrv -> hrv.rmssd
- respiration -> respiration
- steps -> summary.steps
- kcalConsumed -> summary.caloriesOut

- does NOT include 'readiness', because Fitbit suck.

Override with JSON in .env, for example:

{"weight":"weight","restingHR":"rhr","sleepSecs":"sleep.minutes","sleepScore":"sleep.score","avgSleepingHR":"sleep.avg_hr","spO2":"spo2","hrv":"hrv.rmssd","readiness":"readiness","respiration":"respiration","steps":"summary.steps","kcalConsumed":"summary.caloriesOut"}

## Notes

- Intervals.icu endpoint defaults to /api/v1/athlete/{athlete_id}/wellness. Adjust INTERVALS_WELLNESS_PATH if your account uses a different endpoint.
- The date is sent in the URL, so it should not be included as a field in the payload.
- Fitbit data comes from:
  - /1/user/-/activities/date/{date}.json
  - /1.2/user/-/sleep/date/{date}.json
  - /1/user/-/activities/heart/date/{date}/1d.json
- Fitbit refresh tokens rotate; the app will update FITBIT_REFRESH_TOKEN in .env automatically when Fitbit returns a new one.
