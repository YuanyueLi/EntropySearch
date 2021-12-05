# EntropySearch

Search spectral library with entropy similarity

# Usage

## 1. Prepare your spectral library

* The spectral library should be in the format of `.msp`.
* You can get your spectral library from public spectral library like
  MoNA: [https://massbank.us/downloads](https://massbank.us/downloads), or you can generate your own spectral library by
  yourself, but the format should be `.msp` file, and contains the following information:

```text
Name: XXX           <-- Required
ID: XXX             <-- Not required, but recommended. Can also be "spectrum_id" or "spectrumid" or "db#".
PrecursorMZ: XXX    <-- Required, can also be "precursor_mz"
Precursor_type: XXX <-- Required, can also be "precursortype" or "adduct". The last character of the value should be "+" or "-".
InChIKey: XXX       <-- Not required, but recommended.
Num Peaks: XXX      <-- Required, should be the same as the number of peaks in the spectrum.
```

The `Name`, `ID`, `InChIKey` will be used for result output. The `PrecursorMZ` and `Precursor_type` will be used for
similarity search.

* Here is an example from MoNA:

```text
Name: Mebendazole
DB#: AU106401
InChIKey: OPXLLQIJSORQAM-UHFFFAOYSA-N
Precursor_type: [M+H]+
PrecursorMZ: 296.103
Num Peaks: 3
264.0768 3.623080
296.103 100.000000
297.1063 12.911883
```

## 2. Convert your raw spectral file

* The raw spectral file need to be converted to one of the following format: `.mzML, .mzML.gz, .msp`.
* Use `msconvert` from `proteowizard` is highly recommended, you can download it
  from [https://proteowizard.sourceforge.io/download.html](https://proteowizard.sourceforge.io/download.html).
* When using `msconvert`, you need to add the `peakPicking` filter to get the centroided spectra.

## 3. Run the EntropySearch software

* Download the EntropySearch software
  from [https://github.com/YuanyueLi/SpectralEntropy/releases/](https://github.com/YuanyueLi/SpectralEntropy/releases/)
* Select the input file and output file, and the parameters you want to use.
* Run the software.