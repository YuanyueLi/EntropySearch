import {atom} from 'jotai'


export const atomGlobalRunData = atom({});

export const atomSelectedScan = atom(null);

export const atomGlobalSpectrumData = atom({});

export const atomSelectedLibrary = atom({charge: null, idx: null});

export const atomGlobalLibraryData = atom({});

export const atomUpperSpectrumData = atom({});

export const atomLowerSpectrumData = atom({});