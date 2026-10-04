## Retail inference regression checklist

The inference path separates validation, preprocessing, YOLOX execution, normalized detections, and analysis history.

Verify changes against:

- an accepted image below the configured limit;
- an oversized image rejected before buffering;
- deterministic history ordering;
- detector/model version metadata retained with an analysis;
- malformed inference output handled without corrupting history.

Engineering baselines should remain separate from claims about real-world retail accuracy.