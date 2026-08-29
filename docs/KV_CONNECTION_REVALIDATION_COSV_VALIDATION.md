# KV Connection Revalidation COSV Validation

This lane validates projection only. It does not claim live resident execution, authentic provider conformance, private-KV readback, provider operation authority, or connection activation.

Run:

```bash
python scripts/check_kv_connection_revalidation_cosv.py
python -m unittest -v tests.test_kv_connection_revalidation_cosv
python -m unittest -v tests.test_cosv_live_denominator_reconciliation
python -m unittest -v tests.test_cosv_task_vector_index
```

Expected partition after projection: 57 worker task IDs = 35 canonically indexed + 15 active unvectorized + 6 completed historical + 1 superseded historical. Organization active-unvectorized remains 14, so the combined active-unvectorized count is 29.
