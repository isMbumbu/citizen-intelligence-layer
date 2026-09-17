# Intelligence specification

The vertical slice has one deterministic, non-AI review flag. When reported
progress exceeds the share of allocated budget recorded as spent by at least 25
percentage points, the API returns a `PROGRESS_SPEND_GAP` flag with
`REVIEW_REQUIRED` status. It cites the progress, allocation, and spend claims.

The flag says that the figures may warrant verification. It does not allege
fraud, corruption, or wrongdoing; it is neither evidence nor a verification
result. General AI answers and anomaly platforms remain out of scope.
