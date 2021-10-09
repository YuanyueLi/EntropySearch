import pymzml


def test_read(mzml_file):
    run = pymzml.run.Reader(mzml_file)
    for n, spec in enumerate(run):
        print(
            "Spectrum {0}, MS level {ms_level} @ RT {scan_time:1.2f}".format(
                spec.ID, ms_level=spec.ms_level, scan_time=spec.scan_time_in_minutes()
            )
        )
    print("Parsed {0} spectra from file {1}".format(n, mzml_file))
    print()


if __name__ == '__main__':
    test_read(r"D:\test\step_2\I5I5A9ER\I5I5A9ER.mzML.gz")
