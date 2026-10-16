# Application reviews

All knobs live together in `app/hackathon_variables.py`:

| Setting | Default | Meaning |
| --- | ---: | --- |
| `N_MAX_LIVE_HACKERS` | 700 | Attendance goal |
| `HACKER_INVITE_EXTRA_PERCENT` | 25 | Working invitation target: 700 × 1.25 = 875 |
| `REVIEW_EARLY_CUTOFF_PERCENT` | 50 | Early cutoff percentile, capped at the invitation target |
| `REVIEW_RANDOM_POOL_SIZE` | 10 | Mix this many leading applications at the highest priority |
| `MIN_VOTES_TO_APP` | 5 | Baseline scored reviews |
| `MAX_VOTES_TO_APP` | 12 | Hard cap |
| `REVIEW_FULL_URGENCY_PERCENT` | 5 | Full urgency within this % of the ranked pool on **each** side |
| `REVIEW_ZERO_URGENCY_PERCENT` | 12 | Urgency reaches zero at this % on each side |
| `REVIEW_DISPUTE_GAP` | 1.0 | Highest minus lowest normalized vote |

Keep `0 <= FULL < ZERO <= 100`, `0 < EARLY <= 100`, `RANDOM_POOL_SIZE >= 1`
and `1 <= MIN <= MAX`. Increasing FULL or ZERO
means more reviews. These defaults are starting points, not calibrated guarantees.

## Pipeline

1. A submitted application becomes reviewable after two hours, while pending.
2. Organizers pull from a shared queue. Own applications and ones they already
   reviewed/skipped are excluded. Nobody is assigned the whole applicant pool.
3. Applications below five scored reviews come first. Order by fewest reviews,
   then oldest submission, and randomly select within the leading group. A skip
   hides it for that organizer but adds no score.
4. Each organizer gives technical and personal marks (1–5). Each is normalized
   against that organizer's mean and standard deviation. The weighted result is
   `0.5 × (0.2 × technical_z + 0.8 × personal_z)`. Application score = average of
   these votes. A new vote also recalculates that organizer's previous scores.
5. Rank pending, waitlisted, invited, confirmed and attended in-person applications
   with at least five scored reviews. The cutoff rank is
   `min(invitation_target, ceil(ranked_count × EARLY / 100))`.
6. Calculate urgency and the review target below. Higher urgency comes first.
   Mix the first 25 candidates, keeping only those at the highest available priority.
   Disagreements can get full urgency. Set the random pool to 1 for strict ordering.
7. Pause when the target is met. Scores/ranks are recalculated each request, so
   an application can return later. Twelve scored reviews is always the cap.
8. Directors still invite/waitlist manually. Stopping reviews is not rejection
   or acceptance. Team invitation rules are unchanged.

## A growing applicant pool

With `EARLY = 50`, the cutoff stays in the middle until 1,750 applicants have
baseline reviews. After that it stays at rank 875:

| Ranked applicants | Cutoff rank |
| ---: | ---: |
| 100 | 50 |
| 400 | 200 |
| 875 | 438 |
| 1,000 | 500 |
| 1,500 | 750 |
| 1,750 or more | 875 |

This is a review-priority heuristic, not an admission prediction. We cannot rank
applications reliably before baseline reviews, so raw submission count is not used.
For example, 1,000 submissions but 400 fully reviewed applicants means cutoff 200.
Baseline reviews still have priority over all extra reviews.

Invited/confirmed hackers remain in the ranking, though only pending applications
can be reviewed. Inviting the top 100 leaves the cutoff and urgency bands unchanged
if scores stay the same. Cancelled/expired/invalid applications leave the pool; new
ranked applicants and recalculated scores can move the boundary. Do not subtract
invitations from 875 again: they are already included in the full ranking.

The physical goal remains 700. The 875 review-planning target does not send emails
or limit invitation batches. Directors continue managing invitations manually.

## Example: 2,000 ranked applicants, nobody invited yet

The cutoff is rank 875. Five percent of 2,000 = 100 ranks on each side;
12% = 240 ranks on each side. Urgency is flat near the cutoff, then falls linearly.

| Rank | Distance from 875 | Urgency | Review target |
| --- | ---: | ---: | ---: |
| 635 or 1115 | 240 | 0% | 5 |
| 670 or 1080 | 205 | 25% | 7 |
| 705 or 1045 | 170 | 50% | 9 |
| 740 or 1010 | 135 | 75% | 11 |
| 775 through 975 | 0–100 | 100% | 12 |

`target = ceil(MIN + (MAX - MIN) × urgency)`; urgency is between 0 and 1.
At 50%, this is `ceil(5 + 7 × 0.5) = 9`. This controls both how soon an applicant
is shown and how many reviews they need. Simply lowering queue priority would
still eventually give everybody twelve reviews.

Alice at rank 875 gets up to twelve reviews. Bob at rank 1045 gets up to nine.
Carla at rank 1400 normally stops at five. An organizer who already reviewed Alice
gets another eligible application; a different organizer can still receive her.
An organizer doing 300 reviews and one doing 1,000 contribute to the same pool;
there are no individual quotas or extra weight for the more active organizer.

Review totals depend on ties, disputes and moving ranks. Early reviews are never
removed when a later target shrinks; twelve scored reviews remains the hard cap.

## What does a score of 1.0 mean?

It is not one star. For example, if an organizer's mean is 3 and standard
deviation is 1 in both categories, two raw marks of 4 give a normalized vote of
`0.5 × (0.2 × 1 + 0.8 × 1) = 0.5`. Two marks of 2 give `-0.5`.
That is a vote gap of 1.0. Negative means below that reviewer's usual marks.

Suppose votes are `[-0.6, -0.4, 0, 0.5, 0.8]`: the gap is 1.4. If the cutoff
score is 0.1, opinions cross it, so this application gets full urgency even outside
the rank band. Votes `[-2, -2, -2, -1, -1]` also have a large gap, but are all below
0.1; that alone does not trigger extra reviews.

## Edge cases

- Band widths use the **full ranked pool**, including invited/confirmed hackers.
  With 1,800 ranked applicants, full urgency extends 90 ranks each way and fades
  to zero at 216 ranks. Unreviewed applicants must first get baseline reviews.
- Equal scores get equal urgency. A tied group crossing the cutoff gets full
  urgency, which can make the full-urgency group wider than the configured band.
- Online applicants get baseline/dispute reviews without using in-person places.
- Skips do not count toward targets, displayed votes or automatic CV approval.
- Shared rules cover the queue, counters, direct links and POSTs. Submission
  rechecks under a write lock, so stale tabs cannot exceed the cap.
- No new database fields. Keep the earlier score-correction migration applied.

Implementation: `organizers/review_policy.py`. Rank bands use a small Python pass
over the ranked list; filtering and ordering remain Django querysets.

## Simultaneous organizers

Organizers share priority rules, not a fixed identical sequence. Each request
builds a fresh eligible queue, then picks randomly from its leading group. The
next application is chosen after submitting/skipping; there is no prefetched next
application. Direct review links still show the requested eligible application.

The current page does not auto-refresh: replacing it while someone is reading
could lose their work. Randomness reduces collisions but does not reserve a slot.
Two organizers can still open the same application, especially with a small queue.
The submission lock prevents exceeding the cap, but cannot prevent wasted reading.

If that becomes common, use short-lived database reservations with renewal and
expiry for abandoned tabs. Reservations would reserve remaining review slots
across all server workers. Live polling alone would only notice collisions after
both people started; it would not reserve anything. Those additions are deliberately
outside this small change.
