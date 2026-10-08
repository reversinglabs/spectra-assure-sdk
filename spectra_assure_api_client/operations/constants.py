# `list` is paged. When looking up one file by id, stop after this many pages
# rather than walking an unbounded group.
_LOOKUP_PAGE_SIZE = 100
_LOOKUP_MAX_PAGES = 50

# The rl-safe archive answers 202 while the analysis is still running, which is a
# normal step rather than a failure. These bound the wait for it to become ready.
_ARCHIVE_POLL_INTERVAL = 5
_ARCHIVE_MAX_WAIT = 300

# The approval states that count as approved, lowercased for comparison.
# The specification declares approval_status as one of Undetermined, Approved,
# ApprovedAutomatically, ApprovalRejected or ApprovalRevoked. A file approved by
# an automatic policy is approved: matching only "approved" would silently skip
# it, which is the opposite of what the caller asked for.
_APPROVED_STATUSES = frozenset({"approved", "approvedautomatically"})

# The analysis states after which nothing changes any more, lowercased. The
# specification declares analysis/status as PROCESSING, DONE or ERROR, and for
# File Stream files also SECURING and IMPORTING. Waiting stops on either of
# these; every other value, including one the Portal adds later, is waited on.
_ANALYSIS_FINISHED = frozenset({"done", "error"})
