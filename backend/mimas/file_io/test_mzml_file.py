from mimas.file_io import spec_file


def test_read(mzml_file):
    for spec in spec_file.read_one_spectrum(mzml_file):
        print(spec)
        break


if __name__ == '__main__':
    test_read(r"D:\test\spectra_example\Neg_HILIC_45_Mix_9_4.mzML")
    test_read(r"D:\test\spectra_example\MB_Qtof_C18_pos_2.mzML")
    test_read(r"D:\test\spectra_example\Neg_HILIC_45_Mix_9_4.mzML.gz")
    test_read(r"D:\test\spectra_example\MB_Qtof_C18_pos_2.mzML.gz")
