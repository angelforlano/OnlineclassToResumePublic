# Rights-gated real clips

This renderer is intentionally **fail-closed**. It will not download or render a
source until every manifest item has a human-reviewed `rights_status: "approved"`
plus a source page, HTTPS media URL, license, and credit.

The sample manifests currently preserve production notes but are not approvals.
They must remain blocked until a reviewer verifies that the exact reuse, excerpt,
translation, voice-over, and distribution plan comply with the source terms.

Rendering is manual-only in GitHub Actions. Generated media and working downloads
are transient artifacts: do not commit them, upload them to a channel, or run paid
distribution without completing the rights review.
