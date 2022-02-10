import gzip
import zipfile
import shlex
import io


def guess_encoding(filename):
    encodings = ['utf-8', 'windows-1250', 'windows-1252']  # add more
    for e in encodings:
        try:
            fh = io.open(filename, 'r', encoding=e)
            fh.readline()
            return e
        except UnicodeDecodeError:
            # print('got unicode error with %s , trying different encoding' % e)
            pass
    raise IOError("Can't determine encoding!")


def _add_information_to_dict(dict_to_add: dict, item: str, content: str):
    if item in dict_to_add:
        if isinstance(dict_to_add[item], list):
            dict_to_add[item].append(content)
        else:
            dict_to_add[item] = [dict_to_add[item], content]
    else:
        dict_to_add[item] = content


def _parse_comments(spectrum_info):
    comments = spectrum_info["comments"].strip()
    comments_list = shlex.split(comments)

    comments_list_final = {}

    for comment in comments_list:
        info = comment.split("=")
        _add_information_to_dict(comments_list_final, info[0].lower(), "=".join(info[1:]))
        # comments_list_final.append([info[0].lower(), "=".join(info[1:])])

    return comments_list_final


def _parse_information(line: bytes, spec: dict) -> [str, str]:
    """
    Parse the line in .msp file, update information in the spec
    :param line: The input line.
    :param spec: The output information collection.
    :return: The entry of the added information.
    """
    if line:
        lines = line.split(":")
        if len(lines) > 2:
            item = lines[0]
            cont = ":".join(lines[1:])
        elif len(lines) == 2:
            item, cont = lines
        else:
            return "", ""

        item = item.strip().lower()
        cont = cont.strip()
        _add_information_to_dict(spec, item, cont)
        return item, cont
    else:
        return "", ""


def _parse_spectrum(line: str, spec: list) -> int:
    """
    Add peak data to spec
    :param line: The raw line information from .msp file
    :param spec: The spectrum will be added.
    :return: 0: success. 1: no information in this line.
    """
    lines = line.split()
    if len(lines) >= 2:
        mz, intensity = lines[0], lines[1]
        spec.append([float(mz), float(intensity)])
        return 0
    else:
        return 1


def read(stream_input) -> dict:
    """
    Read information from .msp file.
    :param stream_input: a stream for input.
    :return: a dict contains a list with key 'spectra'.
        The list contains multiple dict, one dict represent a single spectrum's informaiton.
    """

    exp = {
        'spectra': []
    }

    for spectrum_info in read_one_spectrum(stream_input):
        exp['spectra'].append(spectrum_info)
    return exp


def read_one_spectrum(filename_input: str,
                      include_raw=0,
                      parse_mol=False,
                      parse_comments=False,
                      **kwargs) -> dict:
    """
    Read one spectrum from .msp file.
    :param filename_input: a stream for input.
    :param include_raw: whether output raw spectrum or not.
    :param parse_mol: whether parser molecule or not
    :param parse_comments: whether parser comments or not
    :return: a dict contains one spectrum information.
    """
    # Deal with compressed file
    if filename_input.lower()[-3:] == ".gz":
        fi = gzip.open(filename_input)
    elif filename_input.lower()[-4:] == ".zip":
        fzip_all = zipfile.ZipFile(filename_input)
        fzip_list = zipfile.ZipFile.namelist(fzip_all)
        fi = fzip_all.open(fzip_list[0], "r")
    else:
        fi = open(filename_input, "rt", encoding=guess_encoding(filename_input))

    if parse_mol:
        mol_cache = {}

    _scan_number = 1
    spectrum_info = {
        "_ms_level": 2,
        "_scan_number": _scan_number,
        'peaks': []
    }
    is_adding_information = True
    is_spec_end = False
    raw = []
    for line in fi:
        if not isinstance(line, str):
            line = line.decode()

        line = line.strip()
        if include_raw:
            raw.append(line)

        if is_adding_information:
            item, _ = _parse_information(line, spectrum_info)
            if item.startswith("num") and item.lower() == "num peaks":
                spectrum_info[item] = int(spectrum_info[item])
                is_adding_information = False
                peak_num = spectrum_info[item]
                if peak_num == 0:
                    is_spec_end = True
        else:
            peaks = spectrum_info['peaks']
            _parse_spectrum(line, peaks)
            if len(peaks) == peak_num:
                is_spec_end = True

        if is_spec_end:
            if include_raw:
                raw.append("\n")
                spectrum_info["raw"] = "\n".join(raw)
                raw = []

            if parse_comments and "comments" in spectrum_info:
                spectrum_info["comments"] = _parse_comments(spectrum_info)

            if parse_mol:
                spectrum_info["_mol"] = _parse_mol(spectrum_info, mol_cache)

            yield spectrum_info

            # Preparing adding the next one.
            is_adding_information = True
            is_spec_end = False
            _scan_number += 1
            spectrum_info = {
                "_scan_number": _scan_number,
                "_ms_level": 2,
                'peaks': []
            }

    fi.close()


def _parse_mol(spectrum_info, mol_cache):
    from rdkit import Chem
    try:
        if "smiles" in spectrum_info:
            smiles = spectrum_info["smiles"]
            if smiles in mol_cache:
                return mol_cache[smiles]
            mol = Chem.MolFromSmiles(smiles)
            mol_cache[smiles] = mol
            return mol
    except:
        pass
    try:
        if "inchi" in spectrum_info:
            inchi = spectrum_info["inchi"]
            if inchi in mol_cache:
                return mol_cache[inchi]
            mol = Chem.MolFromInchi(inchi)
            mol_cache[inchi] = mol
            return mol
    except:
        pass
    if "comments" in spectrum_info and \
            isinstance(spectrum_info["comments"], list):
        for name, value in spectrum_info["comments"]:
            try:
                if name.lower() == "smiles" or \
                        name.lower() == "computed smiles":
                    if value in mol_cache:
                        return mol_cache[value]
                    mol = Chem.MolFromSmiles(value)
                    mol_cache[value] = mol
                    return mol
            except:
                pass
            try:
                if name.lower() == "inchikey" \
                        or name.lower == "computed inchikey":
                    if value in mol_cache:
                        return mol_cache[value]
                    mol = Chem.MolFromInchi(value)
                    mol_cache[value] = mol
                    return mol
            except:
                pass
    return None


def write_one_spectrum(fo, spectrum: dict):
    """
    Write one spectrum to .msp file. The name starts with _ will not be written.
    """
    for name in spectrum:
        if name == "peaks":
            continue
        if name.startswith("_"):
            continue
        if name.strip().lower() == "num peaks":
            continue

        item = spectrum[name]

        if isinstance(item, list):
            str_out = "".join([str(name).capitalize() + ": " + str(x) + "\n" for x in item])
        else:
            str_out = str(name).capitalize() + ": " + str(item) + "\n"

        fo.write(str_out)

    fo.write("Num peaks: {}\n".format(len(spectrum["peaks"])))
    for p in spectrum["peaks"]:
        fo.write(" ".join([str(x) for x in p]))
        fo.write("\n")
    fo.write("\n")
