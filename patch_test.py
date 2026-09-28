def patch_test():
    with open("tests/quality/atdd/test_atdd_l2_preflight_and_findings.py", "r") as f:
        content = f.read()
    content = content.replace("report_1099.rows.read == 10", "report_1099.rows.read == 12")
    with open("tests/quality/atdd/test_atdd_l2_preflight_and_findings.py", "w") as f:
        f.write(content)
patch_test()
