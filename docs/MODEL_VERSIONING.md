# Detector versioning rules

Record the model name and version with every stored analysis so historical results remain interpretable.

## When the model changes
Update the model version identifier, review the fixed regression image set, and compare inference behavior before release.

## Accuracy claims
Do not compare results across model versions without noting preprocessing, threshold, and dataset differences.

## Rollback
Keep the previous checkpoint available until the new version has passed regression checks.
